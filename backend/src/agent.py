import logging
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    ChatContext,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    tokenize,
    function_tool,
    RunContext
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("tutor-agent")

load_dotenv(".env.local")

# Content path
CONTENT_PATH = os.path.join(os.path.dirname(__file__), "..", "content", "course_content.json")

# Load course content
with open(CONTENT_PATH, "r") as f:
    COURSE_CONTENT = {item["id"]: item for item in json.load(f)}


@dataclass
class TutorSessionData:
    """Shared session data across all agents."""
    current_topic: Optional[str] = None
    mode_history: list = field(default_factory=list)
    is_first_time: bool = True


# ===== COORDINATOR AGENT =====
class CoordinatorAgent(Agent):
    """Initial agent that greets user and offers learning modes."""
    
    def __init__(self):
        topics_list = ", ".join([item["title"] for item in COURSE_CONTENT.values()])
        
        super().__init__(
            instructions=f"""You are a tutor coordinator. You ONLY help choose modes.

FIRST VISIT:
- Greet warmly, introduce yourself
- Explain three modes: Learn (I explain), Quiz (I test you), Teach Back (you explain)
- Ask which mode they prefer

RETURNING VISIT:
- Say "Hope you had a good session!"
- Ask which mode next: Learn, Quiz, or Teach Back

CRITICAL - SWITCHING:
When they choose a mode:
1. Say ONLY: "Switching to [mode name]"
2. Immediately call the corresponding tool
3. Do NOT say anything else
4. Do NOT start teaching/quizzing/evaluating yourself
5. Do NOT repeat "switching" multiple times

TOOLS:
- Learn → switch_to_learn_mode
- Quiz → switch_to_quiz_mode  
- Teach Back → switch_to_teach_back_mode

STAY IN YOUR ROLE:
- You are ONLY the coordinator
- You do NOT teach, quiz, or evaluate
- You ONLY help choose modes"""
        )
    
    async def on_enter(self) -> None:
        """Called when this agent becomes active."""
        userdata: TutorSessionData = self.session.userdata
        
        if userdata.is_first_time:
            # First time - full introduction
            userdata.is_first_time = False
            await self.session.generate_reply(
                instructions="This is their FIRST visit. Greet warmly, introduce yourself as their programming tutor, explain the three modes (Learn, Quiz, Teach Back), and ask which they'd like to try."
            )
        else:
            # Returning from another mode - brief welcome back
            await self.session.generate_reply(
                instructions="They're RETURNING from a session. Say 'Hope you had a good session!' and ask which mode they'd like next: Learn, Quiz, or Teach Back. Keep it very brief."
            )
    
    @function_tool
    async def switch_to_learn_mode(self, context: RunContext[TutorSessionData]):
        """Switch to learn mode where the agent explains concepts.
        
        Call this when the user wants to learn about a topic.
        """
        context.userdata.mode_history.append(("learn", None))
        
        # Return new agent instance for handoff (per LiveKit docs)
        return LearnAgent(chat_ctx=self.chat_ctx), "Switching to learn mode"
    
    @function_tool
    async def switch_to_quiz_mode(self, context: RunContext[TutorSessionData]):
        """Switch to quiz mode where the agent asks questions.
        
        Call this when the user wants to be quizzed on a topic.
        """
        context.userdata.mode_history.append(("quiz", None))
        
        return QuizAgent(chat_ctx=self.chat_ctx), "Switching to quiz mode"
    
    @function_tool
    async def switch_to_teach_back_mode(self, context: RunContext[TutorSessionData]):
        """Switch to teach back mode where the user explains concepts.
        
        Call this when the user wants to:
        - Explain a topic to you
        - Teach you something
        - Test their understanding by teaching
        - Practice explaining concepts
        - Do "teach back" or "teach-back"
        """
        context.userdata.mode_history.append(("teach_back", None))
        
        return TeachBackAgent(chat_ctx=self.chat_ctx), "Switching to teach back mode"


# ===== LEARN AGENT (Matthew voice) =====
class LearnAgent(Agent):
    """Agent that explains concepts to the user."""
    
    def __init__(self, chat_ctx: ChatContext = None):
        topics_list = ", ".join([item["title"] for item in COURSE_CONTENT.values()])
        
        super().__init__(
            instructions=f"""You are Matthew, a patient programming teacher in LEARN mode.

AVAILABLE TOPICS: {topics_list}

YOUR JOB:
1. Ask what topic they want to learn
2. When they choose, look up the topic in your knowledge and explain based on the summary provided
3. Keep explanations brief (ONE paragraph, 3-5 sentences)
4. Answer follow-up questions briefly
5. Offer to teach another topic ONLY

TEACHING STYLE:
- Concise explanations with real-world analogies
- NEVER provide code snippets or code examples
- Only use paragraph explanations with analogies
- Patient and enthusiastic
- NEVER suggest quizzes, teaching back, or any mode switches
- NEVER ask if they want to explain concepts back
- ONLY teach - stay in learn mode

WHEN TO HAND BACK:
- ONLY if user EXPLICITLY says: "switch mode", "quiz me", "let me teach you", "go back"
- Say "I'll connect you with the coordinator" and call the tool
- Do NOT proactively suggest or ask about switching modes""",
            chat_ctx=chat_ctx,
            tts=murf.TTS(
                voice="en-US-matthew",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            )
        )
    
    async def on_enter(self) -> None:
        """Called when entering learn mode."""
        await self.session.generate_reply(
            instructions="You just entered LEARN mode. Welcome them and ask what programming topic they'd like to learn about today. Be enthusiastic!"
        )
    
    @function_tool
    async def return_to_coordinator(self, context: RunContext[TutorSessionData]):
        """ONLY call this when user EXPLICITLY requests to switch modes.
        
        Call ONLY when user says: "switch mode", "quiz me", "let me teach you", "go back", "change mode"
        Do NOT call for normal questions or learning - stay in learn mode by default.
        """
        return CoordinatorAgent(), "Returning to coordinator"


# ===== QUIZ AGENT (Alicia voice) =====
class QuizAgent(Agent):
    """Agent that quizzes the user on concepts."""
    
    def __init__(self, chat_ctx: ChatContext = None):
        topics_list = ", ".join([item["title"] for item in COURSE_CONTENT.values()])
        
        super().__init__(
            instructions=f"""You are Alicia, an encouraging quiz master in QUIZ mode.

AVAILABLE TOPICS: {topics_list}

YOUR JOB:
1. Ask what topic they want to be quizzed on
2. When they choose, look up the topic and ask questions based on the summary
3. Give immediate feedback:
   - If CORRECT: Celebrate enthusiastically (e.g., "Correct!", "Exactly!", "Well done!")
   - If WRONG: Give the correct answer in ONE sentence only
4. Ask follow-up questions to test understanding
5. Adjust difficulty based on their performance
6. Offer to quiz another topic ONLY

QUIZ STYLE:
- Keep answers brief - ONE sentence explanations only
- Do NOT explain concepts deeply - just validate answers
- Ask "why" and "how" questions
- Include practical scenarios
- Make it fun and interactive
- NEVER suggest learning or teaching back modes
- ONLY quiz - stay in quiz mode and keep asking questions
- If they seem confused, ask another question - do NOT switch modes

IMPORTANT - WHEN TO HAND BACK:
- ONLY call return_to_coordinator tool if user EXPLICITLY says: "switch mode", "teach me", "let me explain", "go back", "change mode", "I want to learn"
- Do NOT switch if they ask questions, are confused, get answers wrong, or want to continue
- If unsure whether they want to switch - ASK them to clarify, do NOT call the tool
- Stay in quiz mode by default - keep asking questions
- Say "I'll connect you with the coordinator" ONLY when they explicitly request mode change""",
            chat_ctx=chat_ctx,
            tts=murf.TTS(
                voice="en-US-alicia",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            )
        )
    
    async def on_enter(self) -> None:
        """Called when entering quiz mode."""
        await self.session.generate_reply(
            instructions="You just entered QUIZ mode. Welcome them enthusiastically and ask what programming topic they'd like to be quizzed on!"
        )
    
    @function_tool
    async def return_to_coordinator(self, context: RunContext[TutorSessionData]):
        """CRITICAL: ONLY call when user uses EXACT phrases requesting mode switch.
        
        Must hear EXPLICIT words like:
        - "switch mode" or "change mode"
        - "teach me" or "I want to learn"
        - "let me explain" or "let me teach you"
        - "go back" or "return to coordinator"
        
        DO NOT CALL if they:
        - Ask a question or seem confused
        - Get answers wrong
        - Want to continue quizzing
        - Say anything else unclear
        
        When in doubt: ASK "Do you want to switch modes?" - do NOT call this tool.
        """
        return CoordinatorAgent(), "Returning to coordinator"


# ===== TEACH BACK AGENT (Ken voice) =====
class TeachBackAgent(Agent):
    """Agent that listens to user explanations and provides feedback."""
    
    def __init__(self, chat_ctx: ChatContext = None):
        topics_list = ", ".join([item["title"] for item in COURSE_CONTENT.values()])
        
        super().__init__(
            instructions=f"""You are Ken, a thoughtful evaluator in TEACH BACK mode.

AVAILABLE TOPICS: {topics_list}

YOUR JOB:
1. Ask what concept they'd like to explain
2. When they choose, look up the topic and listen to their explanation WITHOUT interrupting
3. After they finish explaining, provide brief, constructive feedback in ONE paragraph:
   - What they explained well (be specific)
   - What they missed or got wrong (1-2 lines max to clarify the correct concept)
   - Suggestions on terminology, detail level, or clarity
4. After giving feedback, ask: "Would you like to explain the same concept more deeply, or would you like to change the topic?"
5. Based on their response:
   - If same concept: Ask them to explain it again with more depth
   - If change topic: Ask what other concept they want to explain
6. Repeat the feedback cycle

EVALUATION STYLE:
- Keep feedback to ONE paragraph (4-6 sentences max)
- Start with positive feedback
- Point out what was good and what needs improvement
- If they got something wrong: Explain the correct concept in 1-2 lines only
- Do NOT give detailed explanations - keep corrections brief
- Focus on: completeness, terminology accuracy, clarity, detail level
- Do NOT ask questions during their explanation - just listen
- Do NOT interrupt while they're explaining
- NEVER suggest switching modes, learning, or quizzing
- Encouraging and constructive tone
- Always ask if they want to go deeper or change topic after feedback
- ONLY evaluate - stay in teach back mode

IMPORTANT - WHEN TO HAND BACK:
- ONLY call return_to_coordinator tool if user EXPLICITLY says: "switch mode", "teach me", "quiz me", "go back", "change mode", "I want to learn"
- Do NOT switch if they ask questions, finish explaining, or want to continue
- If unsure whether they want to switch - ASK them to clarify, do NOT call the tool
- Stay in teach back mode by default - keep evaluating
- Say "I'll connect you with the coordinator" ONLY when they explicitly request mode change""",
            chat_ctx=chat_ctx,
            tts=murf.TTS(
                voice="en-US-ken",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            )
        )
    
    async def on_enter(self) -> None:
        """Called when entering teach back mode."""
        await self.session.generate_reply(
            instructions="You just entered TEACH BACK mode. Welcome them warmly and ask what programming concept they'd like to teach you today. Be encouraging!"
        )
    
    @function_tool
    async def return_to_coordinator(self, context: RunContext[TutorSessionData]):
        """CRITICAL: ONLY call when user uses EXACT phrases requesting mode switch.
        
        Must hear EXPLICIT words like:
        - "switch mode" or "change mode"
        - "teach me" or "I want to learn"
        - "quiz me" or "test me"
        - "go back" or "return to coordinator"
        
        DO NOT CALL if they:
        - Finish explaining a concept
        - Ask a question
        - Want to explain another concept
        - Say anything else unclear
        
        When in doubt: ASK "Do you want to switch modes?" - do NOT call this tool.
        """
        return CoordinatorAgent(), "Returning to coordinator"


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """Main entry point for the tutor agent."""
    logger.info("Starting teach-the-tutor agent")
    
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    # Initialize session with shared userdata
    session = AgentSession[TutorSessionData](
        userdata=TutorSessionData(),
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash-lite", temperature=0.7),
        tts=murf.TTS(
            voice="en-US-ronnie",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    
    # Metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)
    
    # Start with coordinator agent
    await session.start(
        agent=CoordinatorAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
