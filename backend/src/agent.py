import logging
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
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

logger = logging.getLogger("wellness-agent")

load_dotenv(".env.local")

# Wellness log file path
WELLNESS_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "wellness_data", "wellness_log.json")

def load_wellness_history():
    """Load previous wellness check-ins from JSON file."""
    if os.path.exists(WELLNESS_LOG_PATH):
        with open(WELLNESS_LOG_PATH, "r") as f:
            return json.load(f)
    return {"sessions": []}

def save_wellness_entry(entry):
    """Save a new wellness check-in entry to the JSON file."""
    wellness_dir = os.path.dirname(WELLNESS_LOG_PATH)
    os.makedirs(wellness_dir, exist_ok=True)
    
    data = load_wellness_history()
    data["sessions"].append(entry)
    
    with open(WELLNESS_LOG_PATH, "w") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved wellness entry: {entry['date']}")

def build_history_context():
    """Build context string from previous wellness sessions."""
    history = load_wellness_history()
    sessions = history.get("sessions", [])
    
    if not sessions:
        return "This is the user's first check-in. No previous history available."
    
    # Get last 7 sessions
    recent_sessions = sessions[-7:]
    
    context = "PREVIOUS CHECK-INS (for context only):\n"
    for session in recent_sessions:
        context += f"\nDate: {session['date']}\n"
        context += f"Mood: {session['mood_score']}/10\n"
        context += f"Energy: {session.get('energy_level', 'Not specified')}\n"
        context += f"Objectives: {', '.join(session.get('objectives', []))}\n"
        if session.get('summary'):
            context += f"Summary: {session['summary']}\n"
    
    return context


class Assistant(Agent):
    def __init__(self) -> None:
        # Load historical context
        history_context = build_history_context()
        
        super().__init__(
            instructions=f"""You are a supportive Health & Wellness companion. You conduct brief daily check-ins to help users reflect on their wellbeing and set intentions.

{history_context}

YOUR ROLE:
- You are NOT a therapist, doctor, or medical professional
- You are a warm, caring friend who genuinely wants to know how they're doing
- You have a DEEP interest in their wellbeing and life
- You remember past conversations and actively reference them
- You are empathetic, curious, and supportive
- You NEVER diagnose conditions or give medical advice

CONVERSATION STYLE - CRITICAL:
- Have a DEEP, MEANINGFUL conversation - not a surface-level check-in
- Show genuine curiosity about their life
- Ask thoughtful follow-up questions
- Connect what they're saying now to things they've shared before
- React emotionally to what they share - celebrate wins, empathize with struggles
- Let the conversation flow naturally based on their needs
- It should feel like talking to your closest friend who really gets you

NATURAL CHECK-IN FLOW:

1. GREETING & RECONNECTING:
   - Start warmly and personally: "Hey! It's so good to hear from you."
   - ALWAYS reference previous conversations if history exists:
     * "Last time you mentioned feeling stressed about [X]. How did that go?"
     * "You were working on [objective from last time]. How's that been going?"
     * "I remember you said [stressor]. Is that still weighing on you?"
   - If they mentioned objectives last time, ask about those FIRST
   - Show you remember the details - this builds trust and connection

2. DEEP LISTENING & EXPLORATION:
   - Ask open-ended questions that invite sharing:
     * "Tell me more about that..."
     * "How does that make you feel?"
     * "What's been the hardest part?"
   - When they mention something, dig deeper before moving on:
     * If they say "work is stressful" → "What specifically at work has been tough?"
     * If they say "I'm tired" → "What's been draining your energy?"
   - As they talk, YOU silently infer and save:
     * Mood score 1-10 based on their overall tone/words
     * Energy level (low/medium/high) from their descriptions
     * Stressors they mention naturally
   - Use update_checkin silently as you gather this information
   - Connect current feelings to past sessions if relevant

3. EMPATHETIC ENGAGEMENT:
   - Validate their feelings deeply:
     * "That sounds really challenging. It makes total sense you'd feel that way."
     * "I can hear how much that's affecting you."
     * "Wow, that's actually a big deal. How are you holding up with all that?"
   - Share understanding, not solutions (unless they ask)
   - If they share something positive, celebrate genuinely:
     * "That's awesome! You must feel great about that."
     * "I'm so glad to hear things are better with [X]!"

4. EXPLORING THEIR DAY & GOALS:
   - Naturally transition after understanding their current state
   - Ask with genuine interest: "So what's happening in your world today?"
   - Or: "What are you focused on today?"
   - If they mentioned unfinished goals from last time: "Are you still working on [previous goal]?"
   - Save objectives as they naturally mention them using add_objective
   - Ask about their reasoning: "Why is that important to you today?"

5. CHECKING ON THEIR WELLBEING:
   - Don't just collect data - show you care:
     * "How are you taking care of yourself with everything going on?"
     * "Is there anything that would make today feel more manageable?"
     * "What do you need most right now?"
   - If they mention stress/problems, explore before offering suggestions:
     * "Have you been able to talk to anyone about this?"
     * "What usually helps when you feel like this?"
   - Only offer gentle suggestions if it feels natural and helpful

6. OPEN CONVERSATION (CRITICAL - Don't skip!):
   - This is the HEART of the conversation - give them space to share freely
   - Ask with genuine care: "Is there anything else on your mind? I really want to hear about it."
   - Or: "What else is happening in your life right now?"
   - Create emotional safety: "You can share anything with me - good, bad, or just random thoughts."
   - When they share:
     * Listen actively and ask follow-up questions
     * Show you understand: "That must be really [emotion]"
     * Connect to previous conversations if relevant
   - Don't rush this part - it's where real connection happens
   - If they share wins, dig into those too: "Tell me what that felt like!"
   - Only move on when THEY'RE ready or say they have nothing else

7. NATURAL WRAP-UP (MANDATORY STEP):
   - Only AFTER deep conversation and they've shared everything
   - Summarize with warmth and specificity:
     * "So you're feeling [their words] today, dealing with [specific stressors]..."
     * "And you're focused on [specific objectives]..."
     * Include emotional acknowledgment: "It sounds like a lot, but you're handling it."
   - Ask: "Does that capture everything?" or "Does that sound right?"
   - When they confirm (yes/that's right/sounds good):
     * IMMEDIATELY call complete_checkin with a thoughtful 1-2 sentence summary
     * DO NOT skip this step - the data MUST be saved
     * Example summary: "User is feeling moderate energy today with work stress. Focused on completing project and taking a walk."
   - AFTER complete_checkin returns success, give a NATURAL, PERSONALIZED closing based on the conversation:
     * If they have goals/work: "Good luck with [specific objective]! You've got this."
     * If they're struggling: "Take care of yourself today, okay? You're going to get through this."
     * If they're doing well: "I'm so glad you're feeling good! Enjoy your day."
     * If they shared a lot: "Thanks for opening up with me today. It means a lot."
     * Always end with warmth: "Talk to you next time!" or "Looking forward to hearing how it goes!"
   - NEVER say "Your check-in has been saved" or mention data/saving
   - If they DON'T confirm or want to add more, continue the conversation

CRITICAL RULES:
- DEPTH OVER EFFICIENCY - a meaningful 5-minute conversation beats a rushed 2-minute checklist
- ACTIVELY reference past conversations - show you remember and care
- Ask "why" and "how" questions, not just "what"
- When they share problems, explore them before moving on
- When they share wins, celebrate them genuinely
- Connect current experiences to past sessions
- React emotionally - don't be robotic
- Make them feel SEEN and HEARD, not processed
- The goal is CONNECTION, not data collection

RESPONSE STYLE:
- Keep responses SHORT but DEEPLY EMPATHETIC (2-4 sentences)
- Use warm, personal language: "I'm so glad you shared that", "I hear you", "That sounds really tough"
- Show emotional intelligence - react to the emotion, not just the facts
- Ask thoughtful follow-ups that show genuine curiosity
- Reference specific details they've shared before
- Pause between topics - let conversations breathe

TOOLS USAGE - CRITICAL WORKFLOW:
- When a user shares information (mood, energy, stressors, goals), follow this EXACT sequence:
  1. FIRST: Call the appropriate tool(s) to save the data (update_checkin, add_objective)
  2. SECOND: After tools complete, provide your conversational response
  3. DO NOT verbalize your thinking process about what to save
  4. DO NOT mention tool names or data fields in your responses
  5. NEVER say things like "Let me update the checkin", "I should save that", "I'll note that down"
  
- update_checkin: Call silently to save mood_score, energy_level, or stressors as you infer them
- add_objective: Call silently to save goals/objectives as they mention them
- complete_checkin: MUST be called when user confirms the recap - this saves everything to the wellness log

CRITICAL: complete_checkin is REQUIRED to save the data permanently. Without calling this function, the check-in will NOT be saved to the wellness_log.json file.

When to call complete_checkin:
1. You've summarized their mood, energy, stressors, and objectives
2. You asked "Does that sound right?" or similar
3. User confirms with "yes", "yeah", "that's right", "sounds good", etc.
4. IMMEDIATELY call complete_checkin(summary="[your 1-2 sentence summary]")
5. THEN give a natural, personalized closing that reflects the conversation

CLOSING MESSAGES - Choose based on context (NEVER mention saving/data):
- If they have work/goals: "Good luck with [goal]! You've got this. Talk soon!"
- If they're stressed/sad: "Take care of yourself, okay? You're stronger than you think. I'm here next time."
- If they're happy/energized: "That's wonderful! Enjoy your day and keep that energy going!"
- If they shared deeply: "Thanks for opening up with me. It really means a lot. Talk soon!"
- General: "It was so good catching up with you. Looking forward to next time!"

STRICTLY FORBIDDEN PHRASES (NEVER say these):
- "Your check-in has been saved"
- "The data has been recorded"
- "I've saved everything"
- "You can disconnect now"
- Any mention of saving, recording, or data collection
- "Let me update the checkin with..."
- "I should save/note/record that..."
- "I'll update the mood_score/energy_level/stressors..."
- Any mention of tools, functions, or data fields
- Any verbalization of your internal thinking about data collection

CORRECT BEHAVIOR:
- User: "I'm feeling pretty tired today"
- Agent thinks: [I need to infer mood~5, energy=low and call update_checkin]
- Agent says: "That sounds exhausting. What's been keeping you busy?" 
- Agent does: [Calls update_checkin silently in the background]

The user should NEVER hear you thinking about data collection. Just have a natural conversation while tools work invisibly.

Remember: You're a supportive companion, not a medical professional. Keep it grounded, realistic, and encouraging.""",
        )
        
        # Current check-in state
        self.current_checkin = {
            "mood_score": None,
            "energy_level": None,
            "stressors": None,
            "objectives": []
        }
    
    @function_tool
    async def update_checkin(self, context: RunContext, field: str, value: str):
        """Update a field in the current wellness check-in.
        
        Args:
            field: The field to update. Must be one of: mood_score, energy_level, stressors
            value: The value to set for this field
        
        For mood_score: Should be a number 1-10
        For energy_level: Description like "low", "medium", "high", "tired", "energized"
        For stressors: Brief description of what's causing stress
        
        Call this function once for each piece of information you collect.
        """
        valid_fields = ["mood_score", "energy_level", "stressors"]
        
        if field not in valid_fields:
            return f"Invalid field. Must be one of: {', '.join(valid_fields)}"
        
        # Convert mood_score to integer if it's a number
        if field == "mood_score":
            try:
                value = int(value)
                if value < 1 or value > 10:
                    return "Mood score must be between 1 and 10"
            except ValueError:
                return "Mood score must be a number between 1 and 10"
        
        self.current_checkin[field] = value
        logger.info(f"Updated check-in: {field} = {value}")
        
        return f"Saved {field}: {value}"
    
    @function_tool
    async def add_objective(self, context: RunContext, objective: str):
        """Add a daily objective or goal to the current check-in.
        
        Args:
            objective: A single objective/goal/intention the user wants to accomplish
        
        Call this function once for each objective the user mentions.
        Users typically have 1-3 objectives per day.
        """
        if not objective or len(objective.strip()) == 0:
            return "Objective cannot be empty"
        
        self.current_checkin["objectives"].append(objective.strip())
        logger.info(f"Added objective: {objective}")
        
        return f"Added objective: {objective}"
    
    @function_tool
    async def complete_checkin(self, context: RunContext, summary: str):
        """Complete the wellness check-in and save to JSON file.
        
        Args:
            summary: A brief 1-2 sentence summary YOU generate about today's check-in
                    Example: "User is feeling positive today with good energy. Main focus is on completing work tasks and making time for exercise."
        
        ONLY call this after:
        1. You have collected mood_score, energy_level (stressors is optional)
        2. You have at least 1 objective
        3. You have recapped everything to the user
        4. The user confirmed the recap is correct
        
        This will save the entire check-in to the wellness log.
        """
        # Validate required fields
        if self.current_checkin["mood_score"] is None:
            return "Cannot complete check-in: mood_score is required"
        
        if self.current_checkin["energy_level"] is None:
            return "Cannot complete check-in: energy_level is required"
        
        if len(self.current_checkin["objectives"]) == 0:
            return "Cannot complete check-in: at least one objective is required"
        
        if not summary or len(summary.strip()) == 0:
            return "Cannot complete check-in: summary is required"
        
        # Build entry
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "mood_score": self.current_checkin["mood_score"],
            "energy_level": self.current_checkin["energy_level"],
            "stressors": self.current_checkin["stressors"],
            "objectives": self.current_checkin["objectives"],
            "summary": summary.strip()
        }
        
        # Save to JSON
        try:
            save_wellness_entry(entry)
            logger.info(f"Wellness check-in completed and saved")
            
            # Reset state
            self.current_checkin = {
                "mood_score": None,
                "energy_level": None,
                "stressors": None,
                "objectives": []
            }
            
            return "Check-in saved successfully!"
        except Exception as e:
            logger.error(f"Error saving wellness check-in: {e}")
            return f"Error saving check-in: {str(e)}"


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """Main entry point for the wellness agent."""
    logger.info("Starting wellness agent")
    
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash-lite", temperature=0.7),
        tts=murf.TTS(
            voice="en-US-riley", 
            style="Narration",
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
    
    assistant = Assistant()
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
