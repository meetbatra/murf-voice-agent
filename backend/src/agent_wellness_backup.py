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
        return ""
    
    # Only last session to minimize tokens
    last_session = sessions[-1]
    goals_str = ', '.join(last_session.get('objectives', [])[:2])
    
    return f"Last check-in ({last_session['date']}): Mood {last_session['mood_score']}/10, Energy: {last_session.get('energy_level', 'N/A')}, Goals: {goals_str}"


class Assistant(Agent):
    def __init__(self) -> None:
        # Load historical context
        history_context = build_history_context()
        
        super().__init__(
            instructions=f"""Wellness companion. Brief daily check-in.

{history_context}

FLOW:
1. Greet warmly. Reference past if exists: "Last time you [X]"
2. Ask: "How are you feeling?" Listen deeply. Dig into feelings.
3. Silently infer mood 1-10, energy (low/med/high), stressors. Call update_checkin.
4. Ask: "What's on your plate today?" Save goals with add_objective.
5. Ask: "Anything else on your mind?" Give space to share.
6. Summarize: "So mood [X], stressors [Y], goals [Z]. Sound right?"
7. When confirmed, call complete_checkin with summary. Then natural closing: "Good luck with [goal]!" or "Take care!" Never mention saving.

RULES:
- One question at a time, 2-3 sentences max
- Tools silently before responding
- Empathetic, curious, warm
- Never say "saved", "update", "disconnect"
- Friend, not therapist""",
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
        llm=google.LLM(
            model="gemini-2.5-flash-lite",
            temperature=0.7,
        ),
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
