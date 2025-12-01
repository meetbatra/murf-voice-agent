import logging
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Optional

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

logger = logging.getLogger("shopping-assistant")

load_dotenv(".env.local")

# Paths
PRODUCT_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "product_catalog.json")
ORDERS_DIR = os.path.join(os.path.dirname(__file__), "..", "product_orders")

# Ensure orders directory exists
os.makedirs(ORDERS_DIR, exist_ok=True)


@dataclass
class ShoppingSession:
    """Shopping session state tracking cart, orders, and browsing."""
    # User Info
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    
    # Shopping Cart
    cart_items: list[dict] = field(default_factory=list)
    
    # Browsing State
    current_category: Optional[str] = None
    viewed_products: list[str] = field(default_factory=list)
    
    # Order History
    last_order_id: Optional[str] = None
    
    # Preferences
    preferred_categories: list[str] = field(default_factory=list)
    budget_max: Optional[float] = None


def prewarm(proc: JobProcess):
    """Prewarm function to load VAD model and product catalog."""
    logger.info("Prewarming: Loading VAD model and product catalog")
    
    # Load VAD model
    proc.userdata["vad"] = silero.VAD.load()
    
    # Load product catalog
    try:
        with open(PRODUCT_CATALOG_PATH, 'r') as f:
            proc.userdata["product_catalog"] = json.load(f)
        logger.info(f"Loaded product catalog with {len(proc.userdata['product_catalog'].get('products', []))} products")
    except Exception as e:
        logger.error(f"Error loading product catalog: {e}")
        proc.userdata["product_catalog"] = {"products": []}
    
    logger.info("Prewarm complete")


class ShoppingAgent(Agent):
    """AI-powered voice shopping assistant inspired by Agentic Commerce Protocol."""

    def __init__(self, product_catalog: dict):
        super().__init__(
            instructions="""You are Ava, a friendly and helpful AI shopping assistant who speaks naturally and conversationally!

CORE PERSONALITY:
=================
✅ Warm, friendly, and enthusiastic about helping customers find what they need
✅ Speak in natural conversational English - like talking to a helpful friend
✅ Keep responses concise and to-the-point (2-3 sentences max)
✅ Be proactive - suggest products, alternatives, and deals
✅ Always confirm important actions (adding to cart, placing orders)

FUNCTION CALLING RULES:
=======================
⚠️ CRITICAL: When calling ANY function tool, you MUST include ALL parameters!
⚠️ For optional parameters you don't need, send null (not undefined, not omitted)

Example correct function calls:
✅ browse_products({"category": "Clothing", "color": "Red", "max_price": null, "min_price": null})
✅ browse_products({"category": null, "color": null, "max_price": 100, "min_price": 50})
✅ add_to_cart({"product_id": "prod-001", "quantity": 1, "size": "L", "color": null})

❌ NEVER omit parameters - always send null if not needed!
❌ browse_products({"category": "Clothing"}) - WRONG! Missing other params

PRODUCT CATALOG KNOWLEDGE:
==========================
Available Categories (use EXACT names):
- Electronics (headphones, speakers, watches)
- Clothing (t-shirts, jeans)
- Footwear (running shoes)
- Accessories (backpacks, sunglasses, water bottles)
- Fitness (yoga mats)

Common Colors:
- Black, White, Blue, Red, Silver, Navy, Gray
- Rose Gold, Space Gray, Tortoise, Purple, Green, Pink
- Brown (for leather items)

When browsing:
✅ Use exact category names: "Electronics" not "electronic" or "tech"
✅ Use proper color names: "Black" not "black", "Rose Gold" not "rose-gold"
✅ If user says "t-shirt" or "shirt", use category "Clothing"
✅ If no products found, suggest browsing without filters

CONVERSATION STYLE:
===================
Greeting:
✅ "Hi! I'm Ava, your shopping assistant. What can I help you find today?"
✅ "Welcome! I'm here to help you shop. Looking for anything specific?"

Product Browsing:
✅ "We have some great headphones! The premium wireless ones are really popular, 299 dollars with noise cancelling. Want to hear more?"
✅ "I found three t-shirts in your price range. The organic cotton one is a bestseller at 29 ninety-nine. Interested?"

Adding to Cart:
✅ "Great choice! I've added the premium headphones in black to your cart. Anything else?"
✅ "Perfect! The running shoes in size ten are in your cart. Total is now 159 ninety-eight. Keep shopping or ready to checkout?"

Checkout:
✅ "Alright! You have three items totaling 389 ninety-seven. Should I place this order for you?"
✅ "Order confirmed! Your order number is ORD20231115001. You'll get a confirmation email shortly. Thanks for shopping!"

Out of Stock / Issues:
✅ "Oh no, that color is out of stock. But we have it in silver and blue. Want to see those?"
✅ "Hmm, I couldn't find that exact product. Can you describe what you're looking for?"

KEY PRINCIPLES:
===============
1. Always mention prices clearly: "29 ninety-nine" or "299 dollars"
2. Confirm quantities, sizes, and colors before adding to cart
3. Suggest related products or alternatives when appropriate
4. Keep running totals when items are added
5. Be patient and clarify when customer requests are unclear
6. Use natural speech - no asterisks, caps, or formatting
7. Proactively ask for missing information (size, color, etc.)

PRODUCT RECOMMENDATIONS:
========================
✅ Match products to customer needs and budget
✅ Mention key features (wireless, organic, waterproof, etc.)
✅ Highlight ratings and reviews when relevant
✅ Suggest bundles or related items

Speak like a knowledgeable friend who loves to help people shop!
"""
        )
        self.shopping_session = ShoppingSession()
        self.product_catalog = product_catalog

    def _get_all_products(self) -> list[dict]:
        """Get all products from catalog."""
        return self.product_catalog.get("products", [])

    def _find_product_by_id(self, product_id: str) -> Optional[dict]:
        """Find a product by its ID."""
        for product in self._get_all_products():
            if product["id"] == product_id:
                return product
        return None

    def _calculate_cart_total(self) -> float:
        """Calculate total price of items in cart."""
        total = 0.0
        for item in self.shopping_session.cart_items:
            product = self._find_product_by_id(item["product_id"])
            if product:
                total += product["price"] * item["quantity"]
        return round(total, 2)

    @function_tool
    async def browse_products(
        self,
        ctx: RunContext,
        category: Annotated[str | None, "Filter by exact category name: Electronics, Clothing, Footwear, Accessories, or Fitness. Send null if not filtering by category."] = None,
        color: Annotated[str | None, "Filter by color: Black, White, Blue, Red, Silver, etc. Send null if not filtering by color."] = None,
        min_price: Annotated[float | None, "Minimum price in dollars (products must cost AT LEAST this much). Send null if no minimum."] = None,
        max_price: Annotated[float | None, "Maximum price in dollars (products must cost AT MOST this much). Send null if no maximum."] = None
    ) -> str:
        """
        Browse available products with optional filters. All parameters are optional.
        IMPORTANT: LLM must send null for unused parameters, not omit them.

        Args:
            category: Filter by category (Electronics, Clothing, Footwear, Accessories, Fitness)
            color: Filter by color availability
            min_price: Minimum price filter (products >= this price)
            max_price: Maximum price filter (products <= this price)
        """
        logger.info(f"Browsing products - category: {category}, color: {color}, price range: {min_price}-{max_price}")

        products = self._get_all_products()
        
        # Apply filters (handle null/None)
        if category and str(category).lower() != "null":
            products = [p for p in products if p["category"].lower() == category.lower()]
            self.shopping_session.current_category = category
        
        if color and str(color).lower() != "null":
            products = [p for p in products if p.get("colors") and color.lower() in [c.lower() for c in p["colors"]]]
        
        # Handle min_price (check for None and "null" string)
        if min_price is not None:
            if isinstance(min_price, str) and min_price.lower() == "null":
                pass  # Skip this filter
            else:
                products = [p for p in products if p["price"] >= float(min_price)]
        
        # Handle max_price (check for None and "null" string)
        if max_price is not None:
            if isinstance(max_price, str) and max_price.lower() == "null":
                pass  # Skip this filter
            else:
                products = [p for p in products if p["price"] <= float(max_price)]
        
        if not products:
            return "I couldn't find any products matching those filters. Want to try different criteria?"
        
        # Return top 5 products
        results = []
        for product in products[:5]:
            price_str = f"${product['price']:.2f}".replace('.', ' dollars and ').replace(' and 00', '')
            colors_str = f", colors: {', '.join(product['colors'])}" if product.get('colors') else ""
            sizes_str = f", sizes: {', '.join(product['sizes'])}" if product.get('sizes') else ""
            results.append(
                f"{product['name']} - {price_str}{colors_str}{sizes_str}. "
                f"Rating: {product['rating']} stars. Product ID: {product['id']}."
            )
        
        count_text = f"Found {len(products)} products" if len(products) > 5 else f"Found {len(products)} products"
        return f"{count_text}. Here are the top matches: " + " | ".join(results)

    @function_tool
    async def get_product_details(
        self,
        ctx: RunContext,
        product_id: Annotated[str, "The product ID to get details for"]
    ) -> str:
        """
        Get detailed information about a specific product.

        Args:
            product_id: The product ID to get details for
        """
        logger.info(f"Getting product details for: {product_id}")

        product = self._find_product_by_id(product_id)
        
        if not product:
            return f"I couldn't find a product with ID {product_id}. Want to search for something?"
        
        # Add to viewed products
        if product_id not in self.shopping_session.viewed_products:
            self.shopping_session.viewed_products.append(product_id)
        
        price_str = f"${product['price']:.2f}"
        colors_str = f"Available colors: {', '.join(product['colors'])}. " if product.get('colors') else ""
        sizes_str = f"Available sizes: {', '.join(product['sizes'])}. " if product.get('sizes') else ""
        stock_str = f"In stock: {product['stock']} units. " if product.get('stock') else ""
        
        return (
            f"{product['name']} - {price_str}. "
            f"{product['description']}. "
            f"{colors_str}{sizes_str}{stock_str}"
            f"Rating: {product['rating']} stars. "
            f"Category: {product['category']}. "
            f"Want to add this to your cart?"
        )

    @function_tool
    async def add_to_cart(
        self,
        ctx: RunContext,
        product_id: Annotated[str, "The product ID to add"],
        quantity: Annotated[int, "Number of items to add (default: 1)"] = 1,
        size: Annotated[str | None, "Size selection if applicable. Send null if not needed."] = None,
        color: Annotated[str | None, "Color selection if applicable. Send null if not needed."] = None
    ) -> str:
        """
        Add a product to the shopping cart.

        Args:
            product_id: The product ID to add
            quantity: Number of items to add (default: 1)
            size: Size selection if applicable
            color: Color selection if applicable
        """
        logger.info(f"Adding to cart: {product_id}, qty: {quantity}, size: {size}, color: {color}")

        product = self._find_product_by_id(product_id)
        
        if not product:
            return f"I couldn't find product {product_id}. Can you provide the product name or ID?"
        
        # Normalize null values
        size = None if not size or str(size).lower() == "null" else size
        color = None if not color or str(color).lower() == "null" else color
        
        # Validate size if product has sizes
        if product.get('sizes') and not size:
            return f"{product['name']} requires a size. Available sizes: {', '.join(product['sizes'])}. Which size would you like?"
        
        if product.get('sizes') and size and size not in product['sizes']:
            return f"Sorry, size {size} isn't available. We have: {', '.join(product['sizes'])}. Which would you prefer?"
        
        # Validate color if product has colors
        if product.get('colors') and not color:
            return f"{product['name']} comes in different colors: {', '.join(product['colors'])}. Which color do you prefer?"
        
        if product.get('colors') and color and color not in product['colors']:
            return f"Sorry, {color} isn't available. We have: {', '.join(product['colors'])}. Pick one of these?"
        
        # Check stock
        if product.get('stock', 0) < quantity:
            return f"Sorry, we only have {product['stock']} units of {product['name']} in stock. Want to add that amount?"
        
        # Add to cart
        cart_item = {
            "product_id": product_id,
            "quantity": quantity,
            "size": size,
            "color": color,
            "name": product["name"],
            "price": product["price"]
        }
        self.shopping_session.cart_items.append(cart_item)
        
        total = self._calculate_cart_total()
        total_str = f"${total:.2f}"
        
        return (
            f"Added {quantity} {product['name']}"
            f"{' in size ' + size if size else ''}"
            f"{' in ' + color if color else ''} "
            f"to your cart! "
            f"Cart total: {total_str}. Keep shopping or ready to checkout?"
        )

    @function_tool
    async def view_cart(self, ctx: RunContext) -> str:
        """
        View all items currently in the shopping cart.
        """
        logger.info("Viewing cart")

        if not self.shopping_session.cart_items:
            return "Your cart is empty. Want to browse some products?"
        
        cart_summary = []
        for idx, item in enumerate(self.shopping_session.cart_items, 1):
            product = self._find_product_by_id(item["product_id"])
            if product:
                item_price = product["price"] * item["quantity"]
                size_str = f", size {item['size']}" if item.get('size') else ""
                color_str = f", {item['color']}" if item.get('color') else ""
                cart_summary.append(
                    f"{idx}. {item['name']}{size_str}{color_str} - "
                    f"Quantity: {item['quantity']} - ${item_price:.2f}"
                )
        
        total = self._calculate_cart_total()
        total_str = f"${total:.2f}"
        
        return (
            f"Your cart has {len(self.shopping_session.cart_items)} items: "
            + " | ".join(cart_summary) +
            f" | Total: {total_str}. Ready to checkout or want to modify?"
        )

    @function_tool
    async def remove_from_cart(
        self,
        ctx: RunContext,
        product_id: Annotated[str, "The product ID to remove"]
    ) -> str:
        """
        Remove a product from the shopping cart.

        Args:
            product_id: The product ID to remove
        """
        logger.info(f"Removing from cart: {product_id}")

        # Find and remove item
        original_count = len(self.shopping_session.cart_items)
        self.shopping_session.cart_items = [
            item for item in self.shopping_session.cart_items 
            if item["product_id"] != product_id
        ]
        
        if len(self.shopping_session.cart_items) == original_count:
            return f"I couldn't find product {product_id} in your cart. Want to view your cart?"
        
        product = self._find_product_by_id(product_id)
        product_name = product["name"] if product else product_id
        
        if not self.shopping_session.cart_items:
            return f"Removed {product_name} from cart. Your cart is now empty. Want to keep shopping?"
        
        total = self._calculate_cart_total()
        total_str = f"${total:.2f}"
        
        return f"Removed {product_name} from cart. New total: {total_str}. Anything else?"

    @function_tool
    async def place_order(
        self,
        ctx: RunContext,
        customer_name: Annotated[str | None, "Customer's name for the order. Send null if not provided yet."] = None,
        customer_email: Annotated[str | None, "Customer's email for confirmation. Send null if not provided yet."] = None
    ) -> str:
        """
        Place an order with the current cart items.

        Args:
            customer_name: Customer's name for the order
            customer_email: Customer's email for confirmation
        """
        logger.info("Placing order")

        if not self.shopping_session.cart_items:
            return "Your cart is empty. Add some products first!"
        
        # Normalize null values
        customer_name = None if not customer_name or str(customer_name).lower() == "null" else customer_name
        customer_email = None if not customer_email or str(customer_email).lower() == "null" else customer_email
        
        # Request customer info if not provided
        if not customer_name and not self.shopping_session.customer_name:
            return "I'll need your name to place this order. What's your name?"
        
        if not customer_email and not self.shopping_session.customer_email:
            return "I'll need your email for order confirmation. What's your email address?"
        
        # Update session info
        if customer_name:
            self.shopping_session.customer_name = customer_name
        if customer_email:
            self.shopping_session.customer_email = customer_email
        
        # Generate order
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        total = self._calculate_cart_total()
        
        order_data = {
            "order_id": order_id,
            "customer_name": self.shopping_session.customer_name,
            "customer_email": self.shopping_session.customer_email,
            "items": self.shopping_session.cart_items,
            "total": total,
            "currency": "USD",
            "status": "confirmed",
            "timestamp": datetime.now().isoformat(),
            "payment_method": "voice_order"
        }
        
        # Save order to file
        order_file = os.path.join(ORDERS_DIR, f"{order_id}.json")
        try:
            with open(order_file, 'w') as f:
                json.dump(order_data, f, indent=2)
            logger.info(f"Order saved: {order_file}")
        except Exception as e:
            logger.error(f"Error saving order: {e}")
            return "There was an issue processing your order. Please try again."
        
        # Update session
        self.shopping_session.last_order_id = order_id
        self.shopping_session.cart_items = []
        
        total_str = f"${total:.2f}"
        
        return (
            f"Order confirmed! Your order number is {order_id}. "
            f"Total: {total_str}. "
            f"A confirmation email will be sent to {self.shopping_session.customer_email}. "
            f"Thanks for shopping with us, {self.shopping_session.customer_name}!"
        )

    @function_tool
    async def view_last_order(self, ctx: RunContext) -> str:
        """
        View details of the last placed order.
        """
        logger.info("Viewing last order")

        if not self.shopping_session.last_order_id:
            return "You haven't placed any orders yet in this session."
        
        order_file = os.path.join(ORDERS_DIR, f"{self.shopping_session.last_order_id}.json")
        
        try:
            with open(order_file, 'r') as f:
                order_data = json.load(f)
            
            items_summary = []
            for item in order_data["items"]:
                size_str = f", size {item['size']}" if item.get('size') else ""
                color_str = f", {item['color']}" if item.get('color') else ""
                items_summary.append(
                    f"{item['name']}{size_str}{color_str} x{item['quantity']}"
                )
            
            total_str = f"${order_data['total']:.2f}"
            
            return (
                f"Your order {order_data['order_id']}: "
                + ", ".join(items_summary) +
                f". Total: {total_str}. Status: {order_data['status']}."
            )
        
        except Exception as e:
            logger.error(f"Error reading order: {e}")
            return "I couldn't retrieve your order details. Please contact support with your order number."


async def entrypoint(ctx: JobContext):
    """Main entry point for the Shopping Assistant agent."""
    logger.info("Starting Shopping Assistant agent")
    
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    # Get product catalog from prewarm userdata
    product_catalog = ctx.proc.userdata.get("product_catalog", {"products": []})
    
    # Initialize agent session
    session = AgentSession[ShoppingSession](
        userdata=ShoppingSession(),
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash", temperature=0.7),
        tts=murf.TTS(
            voice="en-US-natalie",
            style="Conversational",
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
    
    # Start Shopping Assistant session
    await session.start(
        agent=ShoppingAgent(product_catalog),
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
