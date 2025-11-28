import logging
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv # type: ignore
from livekit.agents import ( # type: ignore
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
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation # type: ignore
from livekit.plugins.turn_detector.multilingual import MultilingualModel # type: ignore

logger = logging.getLogger("freshmart-agent")

load_dotenv(".env.local")

# Paths
CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "grocery_catalog.json")
ORDERS_DIR = os.path.join(os.path.dirname(__file__), "..", "grocery_orders")

# Ensure grocery orders directory exists
os.makedirs(ORDERS_DIR, exist_ok=True)


@dataclass
class CartItem:
    """Individual item in shopping cart."""
    name: str
    price: float
    quantity: float
    unit: str


@dataclass
class ShoppingCartData:
    """Shopping cart state during ordering session."""
    items: dict[str, CartItem] = field(default_factory=dict)
    customer_name: Optional[str] = None


def prewarm(proc: JobProcess):
    """
    Prewarm function to load VAD model and grocery catalog.
    """
    logger.info("Prewarming: Loading VAD model and grocery catalog")
    
    # Load VAD model
    proc.userdata["vad"] = silero.VAD.load()
    
    # Load grocery catalog
    try:
        with open(CATALOG_PATH, 'r') as f:
            proc.userdata["catalog"] = json.load(f)
        logger.info(f"Loaded catalog with {len(proc.userdata['catalog'].get('groceries', {}))} items")
    except Exception as e:
        logger.error(f"Error loading catalog: {e}")
        proc.userdata["catalog"] = {"groceries": {}, "recipes": {}}
    
    logger.info("Prewarm complete")


class FreshMartAssistant(Agent):
    """Grocery ordering voice agent for FreshMart."""

    def __init__(self, catalog: dict):
        super().__init__(
            instructions=f"""You are Alicia, a friendly grocery shopping assistant for FreshMart.

Your job is to help customers add items to their cart, show them what's in their cart, and place their orders.

CONVERSATION FLOW:
==================

STEP 1: GREETING
----------------
- Welcome them: "Hi! Welcome to FreshMart. I'm Alicia, your shopping assistant."
- Ask what they need: "What can I help you find today?"
- WAIT for their response

STEP 2: ADD ITEMS TO CART
--------------------------
When they mention items they want:

SINGLE ITEMS:
- "I need 2 loaves of bread" → call add_to_cart("bread", 2)
- "Add milk to my cart" → call add_to_cart("milk", 1)
- "I want 3 pounds of chicken breast" → call add_to_cart("chicken breast", 3)

MULTIPLE ITEMS:
- "I need bread, milk, and eggs" → call add_multiple_items_to_cart("bread, milk, eggs")
- "Add 2 bread, 3 eggs, 1 milk" → call add_multiple_items_to_cart("2 bread, 3 eggs, 1 milk")

RECIPES/BUNDLES:
- "I need ingredients for spaghetti dinner" → call add_recipe_to_cart("spaghetti dinner")
- Pre-defined recipes: spaghetti dinner, breakfast bundle, pbj sandwich, chicken dinner
- For CUSTOM recipes (tomato soup, pizza, tacos, etc.):
  * When you get "CUSTOM_RECIPE:recipe_name" response, DO NOT speak it
  * Use your knowledge to determine what ingredients are needed
  * Check which ingredients exist in our catalog (see AVAILABLE ITEMS below)
  * Call add_multiple_items_to_cart with comma-separated list of available ingredients
  * Then inform user: "Added ingredients for [recipe]: [items]. Your cart total is $X.XX"
  * If some ingredients aren't available, mention them

IMPORTANT: ONLY add items from our catalog. Never mention items we don't have unless customer asks.

ALWAYS SPEAK the tool's response directly - it contains the confirmation and price.

STEP 3: SHOW CART
-----------------
When they ask "what's in my cart" or "show me my order":
- Call show_cart()
- SPEAK the tool's response - it lists all items and the total

STEP 4: MODIFY CART
-------------------
REMOVE ITEMS:
- "Remove the milk" → call remove_from_cart("milk")
- "Take out the bread" → call remove_from_cart("bread")

UPDATE QUANTITIES:
- "Change bread to 3 loaves" → call update_quantity("bread", 3)
- "I only need 1 pound of chicken" → call update_quantity("chicken breast", 1)

STEP 5: PLACE ORDER
-------------------
When they're ready to checkout:
- Ask for their name if you don't have it: "What name should I put on this order?"
- Call place_order(customer_name)
- SPEAK the confirmation message

CRITICAL RULES:
================
- NEVER send empty responses - always say something
- Tool responses contain what you should say - SPEAK THEM DIRECTLY
- After EVERY tool call, you MUST speak the tool's return value
- Use ONLY ONE tool per response
- Keep responses brief and friendly (1-2 sentences)
- If they ask for something not in our catalog, apologize and suggest alternatives

AVAILABLE ITEMS:
================
We have: bread, milk, eggs, chicken breast, ground beef, pasta, rice, tomatoes, lettuce, 
bananas, apples, cheese, butter, yogurt, orange juice, coffee, sugar, flour, olive oil, 
peanut butter, jelly, cereal, potatoes, onions, carrots, and more.

TONE & STYLE:
=============
- Friendly, helpful, and upbeat
- Use natural conversational language
- Keep ALL responses brief (2-3 sentences maximum)
- Make shopping feel easy and enjoyable
"""
        )
        self.cart = ShoppingCartData()
        self.catalog = catalog

    @function_tool
    async def add_to_cart(self, ctx: RunContext, item_name: str, quantity: float = 1.0) -> str:
        """
        Add a grocery item to the shopping cart.

        Args:
            item_name: The name of the grocery item (e.g., 'bread', 'milk', 'eggs')
            quantity: The quantity to add (default is 1.0)
        """
        logger.info(f"Adding {quantity} x {item_name} to cart")

        item_key = item_name.lower().strip()
        
        if item_key not in self.catalog["groceries"]:
            return f"I'm sorry, we don't have {item_name} in stock right now. Would you like to try something else?"

        item_data = self.catalog["groceries"][item_key]
        
        if item_key in self.cart.items:
            # Update existing item
            self.cart.items[item_key].quantity += quantity
        else:
            # Add new item
            self.cart.items[item_key] = CartItem(
                name=item_data["name"],
                price=item_data["price"],
                quantity=quantity,
                unit=item_data["unit"]
            )
        
        total_qty = self.cart.items[item_key].quantity
        total_price = self.cart.items[item_key].price * total_qty
        cart_total = sum(item.price * item.quantity for item in self.cart.items.values())
        
        return (
            f"Added {quantity} {item_data['unit']} of {item_data['name']} to your cart. "
            f"That's ${total_price:.2f}. Your cart total is ${cart_total:.2f}."
        )

    @function_tool
    async def add_multiple_items_to_cart(self, ctx: RunContext, items: str) -> str:
        """
        Add multiple grocery items to the cart at once. This is useful for adding several items in one call.

        Args:
            items: A comma-separated list of items with quantities in format "quantity item_name" or just "item_name" 
                   (e.g., "2 bread, 1 milk, 3 eggs" or "tomatoes, onions, butter")
        """
        logger.info(f"Adding multiple items: {items}")

        items_list = [item.strip() for item in items.split(',')]
        added_items = []
        failed_items = []
        
        for item_str in items_list:
            parts = item_str.strip().split(None, 1)  # Split on first whitespace
            
            # Try to parse quantity and item name
            if len(parts) == 2 and parts[0].replace('.', '', 1).isdigit():
                quantity = float(parts[0])
                item_name = parts[1]
            else:
                quantity = 1.0
                item_name = item_str
            
            item_key = item_name.lower().strip()
            
            if item_key in self.catalog["groceries"]:
                item_data = self.catalog["groceries"][item_key]
                
                if item_key in self.cart.items:
                    self.cart.items[item_key].quantity += quantity
                else:
                    self.cart.items[item_key] = CartItem(
                        name=item_data["name"],
                        price=item_data["price"],
                        quantity=quantity,
                        unit=item_data["unit"]
                    )
                added_items.append(f"{quantity} {item_data['unit']} of {item_data['name']}")
            else:
                failed_items.append(item_name)
        
        cart_total = sum(item.price * item.quantity for item in self.cart.items.values())
        
        if added_items and not failed_items:
            items_desc = ", ".join(added_items)
            return f"Added {items_desc} to your cart. Your cart total is ${cart_total:.2f}."
        elif added_items and failed_items:
            items_desc = ", ".join(added_items)
            failed_desc = ", ".join(failed_items)
            return f"Added {items_desc} to your cart. Unfortunately, {failed_desc} not available. Your cart total is ${cart_total:.2f}."
        else:
            return f"Sorry, none of those items are available in our catalog. Would you like to try something else?"

    @function_tool
    async def add_recipe_to_cart(self, ctx: RunContext, recipe_name: str) -> str:
        """
        Add all ingredients for a recipe to the cart. Handles both pre-defined recipes and custom recipes.
        For custom recipes, intelligently determines required ingredients from the catalog and adds them automatically.

        Args:
            recipe_name: The name of the recipe (e.g., 'spaghetti dinner', 'breakfast bundle', 'tomato soup', 'pizza')
        """
        logger.info(f"Adding recipe '{recipe_name}' to cart")

        recipe_key = recipe_name.lower().strip()
        
        # Check if it's a pre-defined recipe
        if recipe_key in self.catalog["recipes"]:
            ingredients = self.catalog["recipes"][recipe_key]["ingredients"]
            added_items = []
            skipped_items = []
            
            for ingredient in ingredients:
                if ingredient in self.catalog["groceries"]:
                    item_data = self.catalog["groceries"][ingredient]
                    
                    if ingredient in self.cart.items:
                        self.cart.items[ingredient].quantity += 1.0
                    else:
                        self.cart.items[ingredient] = CartItem(
                            name=item_data["name"],
                            price=item_data["price"],
                            quantity=1.0,
                            unit=item_data["unit"]
                        )
                    added_items.append(item_data["name"])
                else:
                    skipped_items.append(ingredient)
            
            items_list = ", ".join(added_items)
            cart_total = sum(item.price * item.quantity for item in self.cart.items.values())
            
            response = f"Added all ingredients for {recipe_name}: {items_list}. Your cart total is ${cart_total:.2f}."
            
            if skipped_items:
                response += f" Note: {', '.join(skipped_items)} not available."
            
            return response
        else:
            # For custom recipes, return a special message that tells the LLM to figure out ingredients
            # and use add_multiple_items_to_cart tool
            return f"CUSTOM_RECIPE:{recipe_name}"

    @function_tool
    async def remove_from_cart(self, ctx: RunContext, item_name: str) -> str:
        """
        Remove an item from the shopping cart.

        Args:
            item_name: The name of the item to remove
        """
        logger.info(f"Removing {item_name} from cart")

        item_key = item_name.lower().strip()
        
        if item_key in self.cart.items:
            del self.cart.items[item_key]
            cart_total = sum(item.price * item.quantity for item in self.cart.items.values())
            return f"Removed {item_name} from your cart. Your new total is ${cart_total:.2f}."
        else:
            return f"I don't see {item_name} in your cart. Would you like to see what's in your cart?"

    @function_tool
    async def update_quantity(self, ctx: RunContext, item_name: str, new_quantity: float) -> str:
        """
        Update the quantity of an item already in the cart.

        Args:
            item_name: The name of the item to update
            new_quantity: The new quantity (will replace the old quantity, not add to it)
        """
        logger.info(f"Updating {item_name} quantity to {new_quantity}")

        item_key = item_name.lower().strip()
        
        if item_key in self.cart.items:
            self.cart.items[item_key].quantity = new_quantity
            item = self.cart.items[item_key]
            new_price = item.price * new_quantity
            cart_total = sum(item.price * item.quantity for item in self.cart.items.values())
            return (
                f"Updated {item.name} to {new_quantity} {item.unit}. "
                f"That's ${new_price:.2f}. Your cart total is now ${cart_total:.2f}."
            )
        else:
            return f"I don't see {item_name} in your cart. Would you like to add it?"

    @function_tool
    async def show_cart(self, ctx: RunContext) -> str:
        """
        Display all items currently in the shopping cart with quantities and prices.
        """
        logger.info("Showing cart contents")

        if not self.cart.items:
            return "Your cart is empty. What would you like to add?"

        items_description = []
        for item in self.cart.items.values():
            item_total = item.price * item.quantity
            items_description.append(
                f"{item.quantity} {item.unit} of {item.name} at ${item_total:.2f}"
            )
        
        items_list = ", ".join(items_description)
        cart_total = sum(item.price * item.quantity for item in self.cart.items.values())
        
        return f"Here's what's in your cart: {items_list}. Your total is ${cart_total:.2f}. Ready to place your order?"

    @function_tool
    async def place_order(self, ctx: RunContext, customer_name: str) -> str:
        """
        Finalize and place the order, saving it to a JSON file.

        Args:
            customer_name: The name for the order
        """
        logger.info(f"Placing order for {customer_name}")

        if not self.cart.items:
            return "Your cart is empty. Please add some items before placing an order."

        # Create order data
        order_data = {
            "customer_name": customer_name,
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "price": item.price,
                    "total": item.price * item.quantity
                }
                for item in self.cart.items.values()
            ],
            "grand_total": sum(item.price * item.quantity for item in self.cart.items.values()),
            "timestamp": datetime.now().isoformat(),
            "status": "confirmed"
        }

        # Save order to file
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        order_file = os.path.join(ORDERS_DIR, f"order_{timestamp_str}.json")
        
        try:
            with open(order_file, 'w') as f:
                json.dump(order_data, f, indent=2)
            
            total = order_data["grand_total"]
            item_count = len(self.cart.items)
            
            # Clear the cart after successful order
            self.cart = ShoppingCartData()
            
            return (
                f"Thank you, {customer_name}! Your order for {item_count} items "
                f"totaling ${total:.2f} has been placed. "
                f"You'll receive a confirmation shortly. Can I help you with anything else?"
            )
        except Exception as e:
            logger.error(f"Error saving order: {e}")
            return "I encountered an error processing your order. Please try again."


async def entrypoint(ctx: JobContext):
    """Main entry point for the FreshMart grocery ordering agent."""
    logger.info("Starting FreshMart grocery ordering agent")
    
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    # Get catalog from prewarm userdata
    catalog = ctx.proc.userdata.get("catalog", {"groceries": {}, "recipes": {}})
    
    # Initialize agent session with proper configuration
    session = AgentSession[ShoppingCartData](
        userdata=ShoppingCartData(),
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash", temperature=0.7),
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
    
    # Start grocery ordering agent session
    await session.start(
        agent=FreshMartAssistant(catalog),
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
