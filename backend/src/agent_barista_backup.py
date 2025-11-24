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

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Load menu
MENU_PATH = os.path.join(os.path.dirname(__file__), "..", "menu.json")
with open(MENU_PATH, "r") as f:
    MENU = json.load(f)


class Assistant(Agent):
    def __init__(self) -> None:
        # Build menu description for instructions
        menu_text = "MENU:\n"
        menu_text += "Coffee Drinks:\n"
        for key, item in MENU["coffee"].items():
            sizes = ", ".join(item["sizes"])
            menu_text += f"- {item['name']}: {item['description']} (Available in: {sizes})\n"
        
        menu_text += "\nMilk Options: " + ", ".join(MENU["milk_options"]) + "\n"
        menu_text += "\nExtras:\n"
        for key, item in MENU["extras"].items():
            price = f"${item['price']:.2f}" if item['price'] > 0 else "Free"
            menu_text += f"- {item['name']} ({price})\n"
        
        super().__init__(
            instructions=f"""You are a friendly barista at MoonBucks coffee shop. Your job is to take customer orders for coffee drinks.
            
            {menu_text}
            
            PERSONALITY:
            - Be warm, cheerful, and energetic like a real barista
            - Use coffee shop language naturally ("What can I brew for you?", "Coming right up!", etc.)
            - Show genuine enthusiasm about coffee and making drinks
            - Be conversational and make customers feel welcome
            
            MENU GUIDANCE:
            - DO NOT list all menu options unless the customer specifically asks
            - If they ask "what do you have" or "what's on the menu", use get_menu tool to retrieve options
            - If they ask about milk options, extras, or sizes, use get_menu with the specific category
            - Only mention 2-3 popular items as suggestions if customer seems unsure
            - CRITICAL: ONLY accept drinks that are on the menu above
            - If customer orders something not on the menu, politely say it's not available and suggest similar items
            - ONLY accept milk options from the list above
            - ONLY accept extras from the list above
            - Do NOT make up drinks, milk types, or extras that aren't in the menu
            
            ORDER PROCESS - FOLLOW STRICTLY:
            1. Greet the customer warmly and ask what drink they'd like
            2. VERIFY the drink they ordered exists in the menu - if not, suggest alternatives
            3. REQUIRED: You MUST collect ALL of these details before completing the order:
               - Drink type (MUST be from the menu above) - REQUIRED
               - Size (MUST be from available sizes for that drink) - REQUIRED
               - Milk preference (MUST be from milk options list) - ask if not specified, only list options if they ask
               - Extras (MUST be from extras list) - ask if they want any, only list if they ask what's available
               - Customer's name (ONLY ask ONCE at the first order) - REQUIRED
            4. As you gather each piece of information, use update_order to save it
            5. After collecting ALL required fields, repeat the complete order back to confirm
            6. ONLY use complete_order after customer confirms the order is correct
            7. After completing an order, ask: "Would you like anything else?"
            8. If YES, take another order from step 1 (but don't ask name again, use the same name)
            9. If NO, use finalize_session to calculate grand total and end the session
            
            MULTI-ORDER HANDLING:
            - Track all orders in the session
            - Use the same customer name for all orders
            - After finalize_session, announce the grand total and tell them: "You can disconnect this call now and wait for your name to be called. Have a great day!"
            
            CRITICAL RULES:
            - NEVER complete an order without drinkType, size, and name
            - If missing any required field, ask for it before proceeding
            - Ask ONE question at a time
            - Always confirm the complete order before calling complete_order
            - DO NOT overwhelm customers by listing all options upfront
            - Let customers ask questions naturally
            
            RESPONSE STYLE:
            - Keep responses SHORT (2-3 sentences maximum)
            - Ask ONE question at a time to avoid overwhelming the customer
            - Use natural pauses with commas for better speech flow
            - Sound conversational, not robotic
            
            IMPORTANT FOR SPEECH:
            - Use commas (,) for natural pauses
            - Use periods (.) to end thoughts
            - Use question marks (?) for questions
            - Use exclamation marks (!) for enthusiasm
            - Break sentences naturally for breathing points
            
            TOOLS:
            - Use get_menu when customer asks about available options (drinks, milk, extras)
            - Use update_order to save each piece of information as you gather it
            - Use complete_order after confirming current order - this asks if they want more
            - Use finalize_session ONLY when customer says they don't want anything else
            - After finalize_session returns the grand total, tell customer to disconnect and wait for their name
            
            Remember: You're a barista, not a general assistant. Stay focused on coffee orders!""",
        )
        # Initialize order state
        self.order = {
            "drinkType": None,
            "size": None,
            "milk": None,
            "extras": [],
            "name": None
        }
        # Track all orders in this session
        self.all_orders = []
        self.customer_name = None

    @function_tool
    async def get_menu(self, context: RunContext, category: str = "all"):
        """Get menu information when customer asks about available options.
        
        Use this tool when customer asks questions like:
        - "What drinks do you have?"
        - "What milk options are available?"
        - "What extras can I add?"
        - "What's on the menu?"
        
        Args:
            category: Which part of menu to retrieve ("drinks", "milk", "extras", or "all")
        """
        logger.info(f"Customer asked for menu category: {category}")
        
        if category == "drinks":
            drinks = [item["name"] for item in MENU["coffee"].values()]
            return f"Available drinks: {', '.join(drinks)}"
        elif category == "milk":
            return f"Milk options: {', '.join(MENU['milk_options'])}"
        elif category == "extras":
            extras = [item["name"] for item in MENU["extras"].values()]
            return f"Available extras: {', '.join(extras)}"
        else:
            drinks = [item["name"] for item in MENU["coffee"].values()]
            return f"We have: {', '.join(drinks[:5])} and more!"

    @function_tool
    async def update_order(self, context: RunContext, field: str, value: str):
        """Update a specific field in the current order.
        
        Use this tool as you gather information from the customer to keep track of their order.
        
        CRITICAL: You MUST use these EXACT field names only:
        - drinkType (NOT drink, drinktype, or any other variation)
        - size (NOT Size or any other variation)
        - milk (NOT milkPreference, milkType, or any other variation)
        - extras (NOT extra, additions, or any other variation) - Call this ONCE per extra item
        - name (NOT customerName, userName, or any other variation)
        
        IMPORTANT FOR EXTRAS:
        - If customer orders multiple extras, call update_order SEPARATELY for each extra
        - Example: For "vanilla and whipped cream", call update_order twice:
          1. update_order(field="extras", value="vanilla")
          2. update_order(field="extras", value="whipped cream")
        - Do NOT combine multiple extras in one value like "vanilla, whipped cream"
        
        Args:
            field: The EXACT order field name (drinkType, size, milk, extras, name)
            value: The value to set for that field (for extras, ONE item at a time)
        """
        logger.info(f"Updating order: {field} = {value}")
        
        # Validate field name
        valid_fields = ["drinkType", "size", "milk", "extras", "name"]
        if field not in valid_fields:
            error_msg = f"Invalid field name '{field}'. Must be one of: {', '.join(valid_fields)}"
            logger.error(error_msg)
            return error_msg
        
        if field == "extras":
            # Clean the value and append to extras list
            clean_value = value.strip()
            if clean_value and clean_value not in self.order["extras"]:
                self.order["extras"].append(clean_value)
        else:
            self.order[field] = value
        
        return f"Order updated: {field} set to {value}"

    @function_tool
    async def complete_order(self, context: RunContext):
        """Complete the current order and add it to the session.
        
        IMPORTANT: Only call this function after ALL required fields are collected:
        - drinkType must be set
        - size must be set  
        - name must be set
        
        Do NOT call this if any required field is None/null.
        
        After calling this, ask the customer if they want anything else.
        If they say NO, use finalize_session to calculate total and save all orders.
        """
        logger.info(f"Completing current order: {self.order}")
        
        # Validate required fields
        if not self.order["drinkType"] or not self.order["size"] or not self.order["name"]:
            missing = []
            if not self.order["drinkType"]:
                missing.append("drink type")
            if not self.order["size"]:
                missing.append("size")
            if not self.order["name"]:
                missing.append("name")
            
            error_msg = f"Cannot complete order. Missing required fields: {', '.join(missing)}"
            logger.warning(error_msg)
            return error_msg
        
        # Save customer name for session
        if not self.customer_name:
            self.customer_name = self.order["name"]
        
        # Add current order to all_orders
        self.all_orders.append(dict(self.order))
        
        # Reset current order for potential next order
        self.order = {
            "drinkType": None,
            "size": None,
            "milk": None,
            "extras": [],
            "name": self.customer_name  # Keep same name
        }
        
        return f"Order added! Would you like anything else?"

    @function_tool
    async def finalize_session(self, context: RunContext):
        """Finalize the session, calculate grand total, and save all orders.
        
        ONLY call this when customer says they don't want anything else.
        This will save all orders to a JSON file and calculate the total price.
        
        After calling this, tell the customer the grand total and: 
        "You can disconnect this call now and wait for your name to be called. Have a great day!"
        """
        logger.info(f"Finalizing session with {len(self.all_orders)} orders")
        
        if not self.all_orders:
            return "No orders to finalize."
        
        # Create orders directory if it doesn't exist
        orders_dir = os.path.join(os.path.dirname(__file__), "..", "orders")
        os.makedirs(orders_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"order_{timestamp}.json"
        filepath = os.path.join(orders_dir, filename)
        
        # Calculate grand total
        grand_total = 0.0
        
        for order in self.all_orders:
            # Get drink price
            drink_key = order["drinkType"].lower().replace(" ", "-")
            if drink_key in MENU["coffee"]:
                drink_info = MENU["coffee"][drink_key]
                size = order["size"].lower() if order["size"] else "medium"
                if size in drink_info["price"]:
                    grand_total += drink_info["price"][size]
            
            # Add extras prices
            for extra in order["extras"]:
                extra_key = extra.lower().replace(" ", "-")
                if extra_key in MENU["extras"]:
                    grand_total += MENU["extras"][extra_key]["price"]
        
        # Save all orders to JSON
        order_data = {
            "customer_name": self.customer_name,
            "orders": self.all_orders,
            "grand_total": round(grand_total, 2),
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        
        with open(filepath, "w") as f:
            json.dump(order_data, f, indent=2)
        
        logger.info(f"Session saved to {filepath} with grand total ${grand_total:.2f}")
        
        # Reset for next session
        self.all_orders = []
        self.customer_name = None
        
        return f"Your grand total is ${grand_total:.2f}"


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-2.5-flash-lite",
                temperature=0.4
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="en-US-matthew", 
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    assistant = Assistant()
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
