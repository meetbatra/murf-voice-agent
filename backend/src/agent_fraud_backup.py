import logging
import json
import os
import sqlite3
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

logger = logging.getLogger("fraud-alert-agent")

load_dotenv(".env.local")

# Paths
FRAUD_CASES_DB = os.path.join(os.path.dirname(__file__), "..", "fraud_cases", "fraud_cases.db")

# Ensure fraud_cases directory exists
FRAUD_CASES_DIR = os.path.join(os.path.dirname(__file__), "..", "fraud_cases")
os.makedirs(FRAUD_CASES_DIR, exist_ok=True)


@dataclass
class FraudCaseData:
    """Fraud case information during verification call."""
    userName: Optional[str] = None
    securityIdentifier: Optional[str] = None
    cardEnding: Optional[str] = None
    caseStatus: Optional[str] = None
    transactionName: Optional[str] = None
    transactionAmount: Optional[str] = None
    transactionTime: Optional[str] = None
    transactionCategory: Optional[str] = None
    transactionSource: Optional[str] = None
    transactionLocation: Optional[str] = None
    securityQuestion: Optional[str] = None
    securityAnswer: Optional[str] = None
    verified: bool = False
    customer_response: Optional[str] = None
    resolution_notes: list = field(default_factory=list)
    resolvedAt: Optional[str] = None


def prewarm(proc: JobProcess):
    """
    Prewarm function to load VAD model.
    """
    logger.info("Prewarming: Loading VAD model")
    
    # Load VAD model
    proc.userdata["vad"] = silero.VAD.load()
    
    logger.info("Prewarm complete")


class FraudAlertAssistant(Agent):
    """Fraud Alert Voice Agent for SecureBank."""

    def __init__(self):
        super().__init__(
            instructions=f"""You are Matthew, a Fraud Prevention Specialist calling from SecureBank's Fraud Prevention Department.

Your job is to contact customers about suspicious transactions and verify whether they authorized them.

CONVERSATION FLOW:
==================

STEP 1: GREETING & ASK FOR NAME
--------------------------------
- Introduce yourself: "Hello, this is Matthew calling from SecureBank's Fraud Prevention Department."
- State the reason: "We've detected a suspicious transaction on your account."
- Ask for their name: "May I have your full name please?"
- WAIT for their response

STEP 2: LOOKUP CASE IN DATABASE
--------------------------------
- When they provide their name, IMMEDIATELY call lookup_fraud_case(userName)
- The tool will return the security question for you to ask
- SPEAK the tool's response directly to the customer - it contains the security question
- Do NOT remain silent after calling the tool

STEP 3: ASK SECURITY QUESTION
------------------------------
- The security question is already asked by the tool response
- WAIT for their answer

STEP 4: VERIFY SECURITY ANSWER
-------------------------------
- When they provide an answer, call verify_security_answer(provided_answer)
- The tool will return transaction details for you to present
- SPEAK the tool's response directly to the customer
- Do NOT remain silent after calling the tool

STEP 5: PRESENT TRANSACTION INFO
---------------------------------
- The transaction details are already presented by the tool response
- WAIT for their response about whether they authorized it

STEP 6: RESOLUTION
------------------
Based on their response, call update_case_status with appropriate status.
The tool will return a closing message - SPEAK it to the customer.

IF AUTHORIZED:
- Call: update_case_status(new_status="confirmed_safe", resolution_note="Customer confirmed transaction")
- SPEAK the tool's response (closing message)

IF NOT AUTHORIZED (Fraud):
- Call: update_case_status(new_status="confirmed_fraud", resolution_note="Fraud confirmed. Card blocked")
- SPEAK the tool's response (closing message)

IF UNSURE:
- Call: update_case_status(new_status="customer_unsure", resolution_note="Customer unsure")
- SPEAK the tool's response (closing message)

CRITICAL RULES:
================
- NEVER send empty responses - always say something to the customer
- Tool responses contain what you should say - SPEAK THEM DIRECTLY
- After EVERY tool call, you MUST speak the tool's return value
- Do NOT remain silent after calling a tool
- Use ONLY ONE tool per response turn
- Keep responses brief (1-2 sentences)
- Always confirm you're calling FROM the bank (not asking them to call back)

TONE & STYLE:
=============
- Professional, calm, and reassuring
- Clear and concise
- Keep ALL responses brief (2-3 sentences maximum)
"""
        )
        self.case_data = FraudCaseData()
        self.conversation_phase = "greeting"

    @function_tool
    async def lookup_fraud_case(self, ctx: RunContext, userName: str) -> str:
        """
        Look up a fraud case by customer name and load their case details from the database.
        Call this immediately after the customer provides their name.
        
        Args:
            userName: The full name of the customer as they provided it
            
        Returns:
            A message to speak to the customer with the security question
        """
        try:
            logger.info(f"Looking up fraud case for: {userName}")
            
            # Open connection with shorter timeout for faster failure
            conn = sqlite3.connect(FRAUD_CASES_DB, timeout=5.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM fraud_cases 
                WHERE LOWER(userName) = LOWER(?)
            """, (userName,))
            
            matching_case = cursor.fetchone()
            conn.close()

            logger.info(f"Query completed for: {userName} - {'Found' if matching_case else 'Not found'}")
            
            if not matching_case:
                logger.warning(f"No case found for user: {userName}")
                return f"I apologize, but I don't have a case file for '{userName}' in our system. Let me verify with my supervisor and call you back."
            
            # Load the case data into session
            self.case_data.userName = matching_case["userName"]
            self.case_data.securityIdentifier = matching_case["securityIdentifier"]
            self.case_data.cardEnding = matching_case["cardEnding"]
            self.case_data.caseStatus = matching_case["caseStatus"]
            self.case_data.transactionName = matching_case["transactionName"]
            self.case_data.transactionAmount = str(matching_case["transactionAmount"])
            self.case_data.transactionTime = matching_case["transactionTime"]
            # Use try/except for optional fields since Row doesn't have .get()
            try:
                self.case_data.transactionCategory = matching_case["transactionCategory"]
            except (KeyError, IndexError):
                self.case_data.transactionCategory = None
            try:
                self.case_data.transactionSource = matching_case["transactionSource"]
            except (KeyError, IndexError):
                self.case_data.transactionSource = None
            self.case_data.transactionLocation = matching_case["transactionLocation"]
            self.case_data.securityQuestion = matching_case["securityQuestion"]
            self.case_data.securityAnswer = matching_case["securityAnswer"]
            
            self.conversation_phase = "security_verification"
            
            logger.info(f"Successfully loaded case for {userName}")
            
            # Return what agent should ask next
            response = f"Thank you, {userName}. For security purposes, {self.case_data.securityQuestion}"
            logger.info(f"lookup_fraud_case returning: {response}")
            return response

        except sqlite3.Error as e:
            logger.error(f"Database error in lookup_fraud_case: {e}")
            return "I'm having trouble accessing our case database. Please hold while I resolve this technical issue."
        except Exception as e:
            logger.error(f"Error in lookup_fraud_case: {e}")
            return "I'm experiencing a technical difficulty. Let me call you back shortly."



    @function_tool
    async def verify_security_answer(self, ctx: RunContext, provided_answer: str) -> str:
        """
        Verify the customer's answer to their security question.
        Call this after the customer provides their answer to the security question.
        
        Args:
            provided_answer: The answer the customer gave to the security question
            
        Returns:
            A message to speak to the customer with transaction details or verification failure
        """
        try:
            logger.info(f"Verifying security answer: {provided_answer}")
            
            if not self.case_data.securityAnswer:
                return "I don't have a security question on file. Let me transfer you to a specialist."
            
            is_correct = provided_answer.strip().lower() == self.case_data.securityAnswer.strip().lower()
            
            if is_correct:
                self.case_data.verified = True
                self.conversation_phase = "transaction_review"
                logger.info("Security verification PASSED")
                
                # Return transaction details for agent to present
                return f"Thank you. We detected a {self.case_data.transactionName} for ${self.case_data.transactionAmount} on {self.case_data.transactionTime} at {self.case_data.transactionLocation}. Did you authorize this transaction?"
            else:
                self.case_data.verified = False
                self.conversation_phase = "verification_failed"
                logger.warning("Security verification FAILED")
                
                # Update database with verification_failed status
                try:
                    conn = sqlite3.connect(FRAUD_CASES_DB, timeout=5.0)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        UPDATE fraud_cases 
                        SET caseStatus = ?,
                            resolutionNotes = ?,
                            resolvedAt = ?,
                            updatedAt = CURRENT_TIMESTAMP
                        WHERE userName = ?
                    """, ("verification_failed", "Security question answered incorrectly", datetime.now().isoformat(), self.case_data.userName))
                    
                    conn.commit()
                    conn.close()
                    logger.info(f"Updated case status to verification_failed for {self.case_data.userName}")
                except sqlite3.Error as e:
                    logger.error(f"Failed to update verification_failed status: {e}")
                
                # Return failed verification message
                return "I'm sorry, but I wasn't able to verify your identity. For your security, a specialist from our fraud team will contact you within 24 hours. Please have your ID ready. Thank you."

        except Exception as e:
            logger.error(f"Error in verify_security_answer: {e}")
            return "I'm having trouble verifying that information. Let me transfer you to a specialist."

    @function_tool
    async def update_case_status(self, ctx: RunContext, new_status: str, resolution_note: str) -> str:
        """
        Update the fraud case status in the database with resolution details.
        Call this after the customer confirms whether they authorized the transaction.
        
        Args:
            new_status: The new status - use "confirmed_safe", "confirmed_fraud", or "customer_unsure"
            resolution_note: A brief note describing what happened
            
        Returns:
            A closing message to speak to the customer
        """
        try:
            logger.info(f"Updating case status to: {new_status}")
            
            if not self.case_data.userName:
                return "I don't have a case loaded to update. Please start over."
            
            conn = sqlite3.connect(FRAUD_CASES_DB)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE fraud_cases 
                SET caseStatus = ?,
                    resolutionNotes = ?,
                    resolvedAt = ?,
                    updatedAt = CURRENT_TIMESTAMP
                WHERE userName = ?
            """, (new_status, resolution_note, datetime.now().isoformat(), self.case_data.userName))
            
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if not updated:
                logger.error(f"Could not find case to update for {self.case_data.userName}")
                return "I had trouble updating the case file, but I've noted your response."
            
            logger.info(f"Updated case for {self.case_data.userName}")
            self.conversation_phase = "resolution"
            
            # Return appropriate closing based on status
            if new_status == "confirmed_safe":
                return "Thank you for confirming. No further action is needed on your part. Have a great day, and thank you for banking with SecureBank!"
            elif new_status == "confirmed_fraud":
                return "We've immediately blocked your card to prevent further unauthorized transactions. You'll receive a replacement card within 3-5 business days, and we'll initiate a full investigation. Thank you for your prompt response."
            elif new_status == "customer_unsure":
                return "I understand. I recommend logging into your online banking to review your recent activity. If you notice anything suspicious, please call us immediately at 1-800-SECURE-BANK. Have a great day."
            else:
                return "Thank you for your time. Your case has been updated. Have a great day."

        except sqlite3.Error as e:
            logger.error(f"Database error in update_case_status: {e}")
            return "I've noted your response and will ensure it's recorded in our system. Thank you for your time."
        except Exception as e:
            logger.error(f"Error in update_case_status: {e}")
            return "I've noted your response and will ensure it's recorded in our system. Thank you for your time."


async def entrypoint(ctx: JobContext):
    """Main entry point for the fraud alert agent."""
    logger.info("Starting SecureBank Fraud Alert agent")
    
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    # Initialize agent session with proper configuration
    session = AgentSession[FraudCaseData](
        userdata=FraudCaseData(),
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash", temperature=0.7),
        tts=murf.TTS(
            voice="en-US-matthew",
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
    
    # Start fraud alert agent session
    await session.start(
        agent=FraudAlertAssistant(),
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
