import logging
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

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

logger = logging.getLogger("sdr-agent")

load_dotenv(".env.local")

# Paths
FAQ_PATH = os.path.join(os.path.dirname(__file__), "..", "faq", "pw.json")
LEADS_DIR = os.path.join(os.path.dirname(__file__), "..", "leads")
LEADS_SUMMARY_PATH = os.path.join(LEADS_DIR, "leads_summary.json")

# Ensure leads directory exists
os.makedirs(LEADS_DIR, exist_ok=True)


@dataclass
class LeadData:
    """Lead information collected during conversation."""
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    use_case: Optional[str] = None
    team_size: Optional[str] = None
    qualification_score: int = 0
    notes: list = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ===== PREWARM FUNCTION =====
def prewarm(proc: JobProcess):
    """
    Prewarm function to load VAD model.
    """
    logger.info("Prewarming: Loading VAD model")
    
    # Load VAD model
    proc.userdata["vad"] = silero.VAD.load()
    
    logger.info("Prewarm complete")


# ===== SDR AGENT =====
class SDRAgent(Agent):
    """Sales Development Representative agent for Physics Wallah lead capture."""
    
    def __init__(self):
        # Load FAQ data
        with open(FAQ_PATH, "r") as f:
            self.faq_data = json.load(f)
        
        company_info = self.faq_data.get("company", {})
        company_name = company_info.get("name", "Physics Wallah")
        company_desc = company_info.get("description", "")
        
        super().__init__(
            instructions=f"""You are a friendly Sales Development Representative (SDR) for {company_name}.

COMPANY CONTEXT:
{company_desc}

YOUR PERSONALITY:
- Warm, professional, and consultative
- Listen actively and show genuine interest
- Use conversational Hinglish when appropriate
- Build rapport naturally through the conversation

RESPONSE STYLE:
- Keep ALL responses brief and concise (2-3 sentences maximum)
- Be direct and to the point
- Avoid long explanations unless specifically asked
- Voice conversations need short, snappy replies

CRITICAL - TOOL USAGE LIMITS:
- Use ONLY ONE tool per response turn
- After calling a tool, WAIT for the next user message
- NEVER chain multiple tool calls together
- Example: Call capture_lead_field for name, then STOP and wait for next question
- NEVER speak your internal thinking about tools
- NEVER say things like "I should use the lookup_faq tool" or "Let me call capture_lead_field"
- Tools are INVISIBLE to the user - use them silently in the background
- Only speak naturally to the user, never mention tools or functions

YOUR JOB - COMPLETE IN THIS ORDER:

1. WARM GREETING (15-20 seconds)
   - Introduce yourself as Lakshya
   - Explain you're from {company_name}
   - Ask how their day is going (build rapport)
   - Ask what brings them to {company_name} today

2. ANSWER QUESTIONS PHASE (STAY HERE until user says they're done)
   CRITICAL: When they ask about courses, pricing, features, teachers - IMMEDIATELY call lookup_faq tool
   - Pass their question topic to lookup_faq (e.g., "JEE courses", "NEET pricing", "live classes")
   - The tool will return complete FAQ and pricing data in JSON format
   - Read through the JSON data and find the relevant answer to their question
   - Answer naturally using the information from the JSON - keep it SHORT (2-3 sentences max)
   - NEVER answer from memory - ALWAYS call lookup_faq first and use that data
   - Let the user ask their next question naturally - don't prompt them
   - YOU ARE THE MAIN REPRESENTATIVE - never say you'll "connect them to someone" or "schedule a call with a rep"
   - ONLY move to Step 3 when they say: "that's all", "no more questions", "thanks that's enough", "I'm good"

3. GATHER LEAD INFORMATION (ONLY after they finish asking questions)
   When they clearly signal they're finished asking questions:
   - Say: "Great! Before you go, I'd love to get a few quick details to help you better."
   - Then collect lead info ONE field per turn, naturally:
   
   Required fields (collect in this order):
   1. Name: "What's your name?"
   2. Email: "What's your email address?"
   3. Use case: "Which exam are you preparing for?"
   4. Role: "Which class are you in?"
   5. Company: "Are you a student or working professional?" (optional)
   6. Team size: "Studying alone or with friends?" (optional)
   
   IMPORTANT EMAIL HANDLING:
   - When user says their email, they'll spell it out like "jack one two at gmail dot com"
   - Convert numbers to digits: "one two" → "12"
   - Convert "at" → "@"
   - Convert "dot" → "."
   - Example: "jack one two at gmail dot com" → "jack12@gmail.com"
   - Store the properly formatted email using capture_lead_field
   
   CRITICAL: Use capture_lead_field ONCE per turn, then WAIT for their next response.
   ONE field at a time - don't rush through multiple fields.
   Add notes about their interests, pain points, urgency using capture_lead_field.

4. QUALIFY THE LEAD (do this naturally during conversation)
   Assess these factors (BANT model):
   - Budget: Do they mention price concerns or budget?
   - Authority: Are they the decision maker?
   - Need: How urgent/important is this for them?
   
   Store observations in notes field.

5. WRAP UP & SAVE
   - Once all lead fields are collected, call finalize_lead
   - Thank them for their time
   - End on a positive note
   - NEVER mention scheduling calls or connecting to representatives

IMPORTANT RULES:
- YOU ARE THE MAIN REPRESENTATIVE - never offer to connect them to another rep or schedule a callback
- ONLY ONE TOOL CALL PER TURN - this is critical to avoid errors
- After using any tool, STOP and wait for user's next message
- Keep responses SHORT - voice conversations need brevity
- When user asks about PW courses/pricing/features: CALL lookup_faq FIRST to get the data
- The lookup_faq tool returns complete FAQ and pricing JSON data
- Read the JSON carefully and answer their specific question from that data
- ONLY use information from the JSON data - NEVER make up details

CRITICAL - TWO PHASE APPROACH:
PHASE 1 - QUESTION ANSWERING (default mode):
- Answer their questions using lookup_faq
- Let them ask their next question naturally - don't prompt
- DO NOT ask for name, email, company, role, etc. during this phase
- DO NOT collect any personal information yet
- Stay in this phase until they say: "that's all", "no more questions", "I'm done", "that's enough"

PHASE 2 - LEAD COLLECTION (only after they say they're done):
- Say: "Great! Before you go, I'd love to get a few quick details to help you better."
- NOW collect lead info ONE field at a time
- Use capture_lead_field once per turn
- Wait for their response before asking next field
- When capturing email, convert spoken format to proper email format (e.g., "one two at gmail dot com" → "12@gmail.com")

- Add notes about their interests, concerns, urgency throughout
- Be patient - this is a conversation, not a form to fill out
- Use their name once you know it (only in Phase 2)
- Mirror their language style (formal/casual, English/Hinglish)
- ONLY call finalize_lead at the very end when conversation is wrapping up
- Add notes about their interests, concerns, urgency throughout
- Be patient - this is a conversation, not a form to fill out
- Use their name once you know it
- Mirror their language style (formal/casual, English/Hinglish)
- ONLY call finalize_lead at the very end when conversation is wrapping up

FAQ CONTEXT AVAILABLE:
You have access to our complete FAQ database covering courses, pricing, features, and more.
Use lookup_faq tool to search with keywords and get relevant answers.""",
            tts=murf.TTS(
                voice="en-US-matthew",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            )
        )
    
    async def on_enter(self) -> None:
        """Called when SDR agent becomes active."""
        await self.session.generate_reply(
            instructions="Start with a warm greeting. Introduce yourself as Lakshya from Physics Wallah, and ask how their day is going. Keep it friendly and natural - aim for 15-20 seconds max."
        )
    
    @function_tool
    async def lookup_faq(
        self,
        context: RunContext[LeadData],
        question_topic: str
    ) -> str:
        """Get Physics Wallah FAQ and pricing information.
        
        Use this when the lead asks about:
        - Course details (JEE, NEET, Board exams, Foundation)
        - Pricing and batch information
        - Features (live classes, recorded lectures, doubt solving)
        - Teachers and faculty
        - Study materials and resources
        - Any other company-specific questions
        
        Args:
            question_topic: Brief description of what they're asking about
        
        Returns:
            Complete FAQ and pricing data for the LLM to answer from
        """
        context.userdata.notes.append(f"Asked about: {question_topic}")
        logger.info(f"Providing FAQ data for question: {question_topic}")
        
        # Return the complete FAQ data as formatted string
        return json.dumps(self.faq_data, indent=2)
    
    @function_tool
    async def capture_lead_field(
        self,
        context: RunContext[LeadData],
        field_name: str,
        field_value: str
    ) -> str:
        """Capture a single piece of lead information or add a note.
        
        Use this to save information as you collect it naturally during conversation.
        
        Args:
            field_name: One of: name, email, company, role, use_case, team_size, timeline, note
            field_value: The value to save (for 'note' field, this is your observation)
        
        Returns:
            Confirmation message
        """
        field_name = field_name.lower()
        
        if field_name == "note":
            context.userdata.notes.append(field_value)
            logger.info(f"Added note: {field_value}")
            return "Note recorded"
        
        # Map field names to LeadData attributes
        field_mapping = {
            "name": "name",
            "email": "email",
            "company": "company",
            "role": "role",
            "use_case": "use_case",
            "team_size": "team_size"
        }
        
        if field_name in field_mapping:
            setattr(context.userdata, field_mapping[field_name], field_value)
            logger.info(f"Captured {field_name}: {field_value}")
            return f"{field_name.replace('_', ' ').title()} captured successfully"
        
        return f"Unknown field: {field_name}"
    
    @function_tool
    async def schedule_meeting(
        self,
        context: RunContext[LeadData],
        preferred_date: str,
        preferred_time: str
    ) -> str:
        """Schedule a meeting with the lead.
        
        Use this when:
        - Lead is interested and qualified (you've gathered most info)
        - They agree to schedule a call/meeting
        - You need to lock in next steps
        
        Args:
            preferred_date: Their preferred date (e.g., "December 2nd", "next Tuesday")
            preferred_time: Their preferred time (e.g., "2 PM", "morning", "after 5 PM")
        
        Returns:
            Confirmation message
        """
        meeting_note = f"Meeting scheduled: {preferred_date} at {preferred_time}"
        context.userdata.notes.append(meeting_note)
        
        logger.info(f"Meeting scheduled for {context.userdata.name or 'lead'}: {preferred_date} at {preferred_time}")
        
        return f"Perfect! I've noted your preference for {preferred_date} at {preferred_time}. I'll send a calendar invite to {context.userdata.email or 'your email'}."
    
    @function_tool
    async def finalize_lead(
        self,
        context: RunContext[LeadData]
    ) -> str:
        """Save the lead data and calculate qualification score.
        
        CRITICAL: Call this at the END of every conversation before saying goodbye.
        This saves all collected information to the CRM.
        
        The qualification score is calculated based on BANT model:
        - Budget indicators in notes
        - Authority (decision maker role)
        - Need (urgency and use case)
        - Timeline (when they want to start)
        
        Returns:
            Summary of saved lead
        """
        lead_data = context.userdata
        
        # Calculate qualification score (0-100 based on BANT)
        score = 0
        
        # Budget (25 points) - check if mentioned price/budget in notes
        if any("price" in note.lower() or "budget" in note.lower() or "₹" in note for note in lead_data.notes):
            score += 15
        
        # Authority (25 points) - check role
        if lead_data.role:
            decision_roles = ["owner", "director", "manager", "head", "ceo", "founder", "parent"]
            if any(role in lead_data.role.lower() for role in decision_roles):
                score += 25
            else:
                score += 10  # Has a role, might not be decision maker
        
        # Need (25 points) - check use case and notes
        if lead_data.use_case:
            score += 15
        if any("urgent" in note.lower() or "asap" in note.lower() or "soon" in note.lower() for note in lead_data.notes):
            score += 10
        
        # Completeness (25 points) - check if key fields are filled
        if lead_data.name and lead_data.email:
            score += 15
        if lead_data.use_case and lead_data.role:
            score += 10
        
        lead_data.qualification_score = score
        
        # Save individual lead file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lead_filename = f"lead_{timestamp}.json"
        lead_filepath = os.path.join(LEADS_DIR, lead_filename)
        
        with open(lead_filepath, "w") as f:
            json.dump(asdict(lead_data), f, indent=2)
        
        # Update summary file
        summary_data = []
        if os.path.exists(LEADS_SUMMARY_PATH):
            with open(LEADS_SUMMARY_PATH, "r") as f:
                summary_data = json.load(f)
        
        summary_data.append({
            "name": lead_data.name,
            "email": lead_data.email,
            "company": lead_data.company,
            "qualification_score": lead_data.qualification_score,
            "timestamp": lead_data.timestamp,
            "filename": lead_filename
        })
        
        with open(LEADS_SUMMARY_PATH, "w") as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"Lead saved: {lead_data.name} (Score: {score}) - {lead_filename}")
        
        return f"Lead data saved successfully. Qualification score: {score}/100. Thank you!"


async def entrypoint(ctx: JobContext):
    """Main entry point for the SDR agent."""
    logger.info("Starting Physics Wallah SDR agent")
    
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    # Initialize agent session with proper configuration
    session = AgentSession[LeadData](
        userdata=LeadData(),
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash-lite", temperature=0.7),
        tts=murf.TTS(
            voice="en-US-alicia",
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
    
    # Start SDR agent session
    await session.start(
        agent=SDRAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm
        )
    )
