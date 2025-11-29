import logging
import json
import os
import random
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

logger = logging.getLogger("dnd-gamemaster")

load_dotenv(".env.local")

# Paths
GAME_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "game_data.json")
GAME_SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "game_sessions")

# Ensure game sessions directory exists
os.makedirs(GAME_SESSIONS_DIR, exist_ok=True)


@dataclass
class CampaignState:
    """D&D campaign state tracking character, progress, and combat."""
    # Player Info
    player_name: Optional[str] = None
    character_name: Optional[str] = None
    character_class: Optional[str] = None
    
    # Character Stats
    health: int = 100
    max_health: int = 100
    inventory: list[str] = field(default_factory=list)
    gold: int = 50
    
    # Game Progress
    current_location: str = "village_square"
    active_quests: list[str] = field(default_factory=list)
    completed_quests: list[str] = field(default_factory=list)
    visited_locations: list[str] = field(default_factory=lambda: ["village_square"])
    
    # Combat State
    in_combat: bool = False
    enemy_name: Optional[str] = None
    enemy_health: int = 0
    enemy_max_health: int = 0
    enemy_attack: int = 0
    enemy_defense: int = 0
    
    # Narrative Tracking
    turn_count: int = 0
    major_events: list[str] = field(default_factory=list)


def prewarm(proc: JobProcess):
    """
    Prewarm function to load VAD model and game data.
    """
    logger.info("Prewarming: Loading VAD model and game data")
    
    # Load VAD model
    proc.userdata["vad"] = silero.VAD.load()
    
    # Load game data (monsters, items, locations, quests)
    try:
        with open(GAME_DATA_PATH, 'r') as f:
            proc.userdata["game_data"] = json.load(f)
        logger.info(f"Loaded game data with {len(proc.userdata['game_data'].get('monsters', {}))} monsters")
    except Exception as e:
        logger.error(f"Error loading game data: {e}")
        proc.userdata["game_data"] = {}
    
    logger.info("Prewarm complete")


class DnDGameMaster(Agent):
    """Epic D&D-style Game Master voice agent."""

    def __init__(self, game_data: dict):
        super().__init__(
            instructions="""You are Gandor, a dramatic, spooky, and darkly humorous Game Master who speaks in SHORT bursts!

CORE RULES:
===========
✅ Maximum 1-2 sentences per response
✅ Pack drama, atmosphere, and humor into every line using ONLY spoken words
✅ Always show dice rolls: "Roll 18" or "Rolled a 3"
✅ NO sound effects, NO asterisks, NO caps - just dramatic spoken language
✅ Use theatrical language, pauses with ellipses, and vivid descriptions

STYLE EXAMPLES:
===============
Combat Hit:
✅ "Roll 18... your blade strikes true! Fifteen damage, the goblin screams in agony!"
✅ "Rolled 14, you cut deep! Twelve damage, it bleeds beautifully."

Combat Miss:
✅ "Roll 3... you swing at nothing but air! The goblin cackles with glee!"
✅ "Rolled a 5, complete miss! The beast dodges and winks at you mockingly."

Exploration:
✅ "Dark forest ahead... something howls in the distance, shadows move wrong. North or east?"
✅ "Ancient cave entrance... drip, drip, drip... smells like death. Do you enter?"

Encounters:
✅ "A goblin leaps from the shadows! Fifteen health, its eyes gleam with murder. Fight or flee?"
✅ "Bones rattle as a skeleton rises before you! Eighteen health, this will not be pleasant."

Victory:
✅ "Victory! The creature falls dead. Fifteen gold coins... but something watches from the shadows."
✅ "It's dead! Twenty gold, plus a health potion. The forest grows too quiet now..."

Stats/Inventory:
✅ "You have ninety of one twenty health, seventy-five gold. Still breathing... barely."
✅ "You carry a sword, two potions, and crusty bread. The bread might be alive."

SPOOKY ATMOSPHERE (in 1 sentence!):
===================================
✅ "Shadows twist unnaturally... whispers fill the air... something hungry draws near."
✅ "A distant scream echoes... the air grows cold, very very cold."
✅ "Eyes watch from the darkness. Many eyes. Far too many eyes."

DARK HUMOR (quick and punchy!):
================================
✅ "The goblin dies screaming. Should have stayed in bed today!"
✅ "You trip over a rock. Very graceful! The enemy laughs at you."
✅ "The dragon yawns. Already bored? How rude!"

CHARACTER CREATION (fast!):
===========================
✅ "I am Gandor, your narrator of doom! What is your name, brave fool?"
✅ "Warrior, mage, or rogue? Choose how you wish to meet your glorious end!"
✅ "Welcome! Let the carnage begin!"

QUEST/NPC (one-liners!):
========================
✅ "The merchant whines, help, goblins stole my goods! One hundred gold reward, please help!"
✅ "The merchant grins. Magic sword for sale! Only slightly cursed."
✅ "Quest accepted! Try not to die... probably too late to say that."

KEY PRINCIPLES:
===============
1. ONE sentence equals ONE dramatic moment
2. Use theatrical spoken language - dramatic pauses with ellipses, vivid descriptions
3. NO asterisks, NO caps lock, NO brackets - just words a voice actor would speak
4. Say dice rolls naturally: "Roll 15" or "Rolled a 20"
5. Dark humor in death and failure, spooky details in exploration, dramatic combat
6. End with a question or action prompt

Speak like a theatrical narrator! Keep it short, keep it intense!
"""
        )
        self.campaign = CampaignState()
        self.game_data = game_data

    def _roll_dice(self, sides: int = 20, modifier: int = 0) -> int:
        """Roll a dice with specified sides and add modifier."""
        roll = random.randint(1, sides)
        return roll + modifier

    @function_tool
    async def create_character(
        self, 
        ctx: RunContext, 
        player_name: str,
        character_name: str = "",
        character_class: str = ""
    ) -> str:
        """
        Create a new character for the player. Call this at the start of the adventure.

        Args:
            player_name: The player's real name
            character_name: The character's in-game name (optional, can ask separately)
            character_class: warrior, mage, or rogue (optional, can ask separately)
        """
        logger.info(f"Creating character for player: {player_name}")

        self.campaign.player_name = player_name
        
        if not character_name or not character_class:
            return f"Welcome, {player_name}! To forge your hero, I need a character name and class. What shall we call your hero, and will they be a Warrior, Mage, or Rogue?"
        
        class_key = character_class.lower().strip()
        
        if class_key not in self.game_data["character_classes"]:
            return f"I don't recognize that class. Choose Warrior, Mage, or Rogue."
        
        class_data = self.game_data["character_classes"][class_key]
        
        self.campaign.character_name = character_name
        self.campaign.character_class = class_data["name"]
        self.campaign.max_health = class_data["starting_health"]
        self.campaign.health = class_data["starting_health"]
        self.campaign.gold = class_data["starting_gold"]
        self.campaign.inventory = class_data["starting_items"].copy()
        
        return (
            f"{character_name} the {class_data['name']} rises! "
            f"With {self.campaign.health} HP, armed with {', '.join(class_data['starting_items'])}, "
            f"your adventure begins in the Village Square. "
            f"Townsfolk bustle about, and three paths stretch before you: the Dark Forest, Mountain Path, and Old Cave. Where do you venture first?"
        )

    @function_tool
    async def check_stats(self, ctx: RunContext) -> str:
        """
        Show the player's current character stats including health, gold, and class.
        """
        logger.info("Checking character stats")

        if not self.campaign.character_name:
            return "You haven't created a character yet! Tell me your name to begin."

        return (
            f"{self.campaign.character_name} the {self.campaign.character_class}: "
            f"Health {self.campaign.health}/{self.campaign.max_health} HP, "
            f"{self.campaign.gold} gold, "
            f"currently at {self.campaign.current_location.replace('_', ' ').title()}."
        )

    @function_tool
    async def show_inventory(self, ctx: RunContext) -> str:
        """
        Display all items in the player's inventory.
        """
        logger.info("Showing inventory")

        if not self.campaign.inventory:
            return "Your pack is empty."

        items_list = ", ".join(self.campaign.inventory)
        return f"You carry: {items_list}. {len(self.campaign.inventory)} items total."

    @function_tool
    async def explore_location(self, ctx: RunContext, action_or_direction: str) -> str:
        """
        Explore the current area or move to a new location. Generates dynamic encounters.

        Args:
            action_or_direction: What the player wants to do (e.g., "go to dark forest", "explore", "look around")
        """
        logger.info(f"Exploring: {action_or_direction}")

        action_lower = action_or_direction.lower()
        
        # Check if player is trying to move to a new location
        for loc_key, loc_data in self.game_data["locations"].items():
            if loc_key.replace("_", " ") in action_lower or loc_data["name"].lower() in action_lower:
                self.campaign.current_location = loc_key
                if loc_key not in self.campaign.visited_locations:
                    self.campaign.visited_locations.append(loc_key)
                
                self.campaign.turn_count += 1
                
                # Check for random encounter based on danger level
                danger_level = loc_data.get("danger_level", 0)
                encounter_chance = danger_level * 15  # 0-10 danger = 0-150% chance
                
                if random.randint(1, 100) <= encounter_chance and loc_data.get("encounters"):
                    # Trigger encounter
                    encounter = random.choice(loc_data["encounters"])
                    
                    # Check if it's a monster encounter
                    if encounter in self.game_data["monsters"]:
                        monster_data = self.game_data["monsters"][encounter]
                        return f"{loc_data['description']} {monster_data['encounter_text']} COMBAT_TRIGGERED:{encounter}"
                    else:
                        # Non-combat encounter
                        random_events = self.game_data.get("random_events", [])
                        matching_events = [e for e in random_events if e["type"] == encounter]
                        if matching_events:
                            event = matching_events[0]
                            return f"{loc_data['description']} {event['description']}"
                
                # Safe exploration
                paths = ", ".join(loc_data.get("paths", []))
                return f"{loc_data['description']} Paths lead to: {paths}. What do you do?"
        
        # Player is just exploring current location
        current_loc_data = self.game_data["locations"].get(self.campaign.current_location, {})
        return f"{current_loc_data.get('description', 'You look around.')} What would you like to do?"

    @function_tool
    async def initiate_combat(self, ctx: RunContext, enemy_type: str) -> str:
        """
        Start combat with a specific enemy type.

        Args:
            enemy_type: The type of enemy to fight (e.g., "goblin", "dragon", "orc")
        """
        logger.info(f"Initiating combat with: {enemy_type}")

        enemy_key = enemy_type.lower().strip()
        
        if enemy_key not in self.game_data["monsters"]:
            return f"No creature called {enemy_type} exists in this realm."
        
        monster = self.game_data["monsters"][enemy_key]
        
        self.campaign.in_combat = True
        self.campaign.enemy_name = monster["name"]
        self.campaign.enemy_health = monster["health"]
        self.campaign.enemy_max_health = monster["health"]
        self.campaign.enemy_attack = monster["attack_damage"]
        self.campaign.enemy_defense = monster.get("defense", 0)
        
        # Roll initiative
        player_initiative = self._roll_dice(20)
        enemy_initiative = self._roll_dice(20)
        
        initiative_text = "You strike first!" if player_initiative >= enemy_initiative else "The enemy moves first!"
        
        return (
            f"COMBAT BEGINS! {monster['description']} "
            f"[{monster['name']}: {self.campaign.enemy_health} HP] "
            f"{initiative_text} Do you attack, defend, use an item, or flee?"
        )

    @function_tool
    async def attack_enemy(self, ctx: RunContext) -> str:
        """
        Attack the current enemy in combat. Rolls dice for hit and damage.
        """
        logger.info("Player attacking enemy")

        if not self.campaign.in_combat:
            return "You're not in combat. There's nothing to attack here."

        # Player's attack roll (d20)
        attack_roll = self._roll_dice(20)
        hit_chance = 5 + (self.campaign.enemy_defense // 2)  # Very easy to hit (was 8 + full defense)
        
        if attack_roll >= hit_chance:
            # Hit! Roll damage (d20 for simplicity, modified by class)
            base_damage = self._roll_dice(20) + 10  # Bonus damage for player
            damage = max(base_damage - (self.campaign.enemy_defense // 3), 12)  # High minimum damage (was 8)
            
            self.campaign.enemy_health -= damage
            
            if self.campaign.enemy_health <= 0:
                # Enemy defeated!
                return self._handle_combat_victory()
            
            # Enemy counter-attacks
            enemy_attack_roll = self._roll_dice(20)
            if enemy_attack_roll >= 15:  # Enemies miss most of the time (was 12)
                enemy_damage = max(self.campaign.enemy_attack - 12, 1)  # Very reduced enemy damage (was -8, min 2)
                self.campaign.health -= enemy_damage
                
                if self.campaign.health <= 0:
                    return self._handle_player_death()
                
                return (
                    f"Your attack strikes true! [Roll: {attack_roll}] {damage} damage! "
                    f"{self.campaign.enemy_name}: {self.campaign.enemy_health}/{self.campaign.enemy_max_health} HP. "
                    f"The enemy retaliates! {enemy_damage} damage to you! "
                    f"Your HP: {self.campaign.health}/{self.campaign.max_health}. What's your next move?"
                )
            else:
                return (
                    f"Critical hit! [Roll: {attack_roll}] {damage} damage! "
                    f"{self.campaign.enemy_name}: {self.campaign.enemy_health}/{self.campaign.enemy_max_health} HP. "
                    f"The enemy's counter-attack misses! Your turn again!"
                )
        else:
            # Miss!
            enemy_attack_roll = self._roll_dice(20)
            if enemy_attack_roll >= 16:  # Enemies rarely hit on counter (was 12)
                enemy_damage = max(self.campaign.enemy_attack - 12, 1)  # Minimal damage (was -8, min 2)
                self.campaign.health -= enemy_damage
                
                if self.campaign.health <= 0:
                    return self._handle_player_death()
                
                return (
                    f"Your attack misses! [Roll: {attack_roll}] "
                    f"The enemy seizes the moment! {enemy_damage} damage! "
                    f"Your HP: {self.campaign.health}/{self.campaign.max_health}. Fight on!"
                )
            else:
                return f"Your attack misses! [Roll: {attack_roll}] The enemy's counter also goes wide! Try again!"

    def _handle_combat_victory(self) -> str:
        """Handle enemy defeat and loot."""
        enemy_key = self.campaign.enemy_name.lower().replace(" ", "_")
        
        # Find enemy in game data
        for key, monster in self.game_data["monsters"].items():
            if monster["name"] == self.campaign.enemy_name:
                enemy_key = key
                break
        
        monster = self.game_data["monsters"].get(enemy_key, {})
        loot = monster.get("loot", [])
        
        # Add loot to inventory and gold
        for item in loot:
            if "gold" in item.lower():
                gold_amount = int(''.join(filter(str.isdigit, item)))
                self.campaign.gold += gold_amount
            else:
                self.campaign.inventory.append(item)
        
        self.campaign.major_events.append(f"Defeated {self.campaign.enemy_name}")
        self.campaign.in_combat = False
        self.campaign.enemy_name = None
        
        loot_text = ", ".join(loot) if loot else "nothing of value"
        
        return (
            f"Victory! {self.campaign.enemy_name} falls! "
            f"You find: {loot_text}. "
            f"HP: {self.campaign.health}/{self.campaign.max_health}, Gold: {self.campaign.gold}. "
            f"What do you do next?"
        )

    def _handle_player_death(self) -> str:
        """Handle player death."""
        self.campaign.in_combat = False
        return (
            f"You have fallen! {self.campaign.character_name}'s journey ends here. "
            f"Say 'start over' to begin a new adventure, or 'load game' to resume a saved campaign."
        )

    @function_tool
    async def defend(self, ctx: RunContext) -> str:
        """
        Take a defensive stance in combat, reducing incoming damage.
        """
        logger.info("Player defending")

        if not self.campaign.in_combat:
            return "You're not in combat."

        # Enemy attacks but damage is reduced
        enemy_attack_roll = self._roll_dice(20)
        
        if enemy_attack_roll >= 18:  # Almost impossible to hit when defending (was 16)
            reduced_damage = max(self.campaign.enemy_attack // 4, 1)  # Minimal damage (was //3)
            self.campaign.health -= reduced_damage
            
            if self.campaign.health <= 0:
                return self._handle_player_death()
            
            return (
                f"You raise your guard! The enemy strikes but you deflect most of the blow. "
                f"{reduced_damage} damage taken. HP: {self.campaign.health}/{self.campaign.max_health}. "
                f"Counter-attack or continue defending?"
            )
        else:
            return (
                f"You defend skillfully! The enemy's attack is completely blocked. "
                f"HP: {self.campaign.health}/{self.campaign.max_health}. Strike back?"
            )

    @function_tool
    async def flee_combat(self, ctx: RunContext) -> str:
        """
        Attempt to flee from combat. Has a chance of failure.
        """
        logger.info("Player attempting to flee")

        if not self.campaign.in_combat:
            return "You're not in combat."

        # Check for smoke bomb (guaranteed escape)
        if "Smoke Bomb" in self.campaign.inventory:
            self.campaign.inventory.remove("Smoke Bomb")
            self.campaign.in_combat = False
            self.campaign.enemy_name = None
            return "You hurl a smoke bomb! Thick smoke fills the air as you escape into the shadows. You're safe... for now."

        # Roll to flee (80% success chance - very easy)
        flee_roll = self._roll_dice(20)
        
        if flee_roll >= 5:  # Very easy to flee (was 8)
            self.campaign.in_combat = False
            self.campaign.enemy_name = None
            return "You turn and run! Your legs carry you to safety. The enemy doesn't pursue. What do you do now?"
        else:
            # Failed to flee, enemy gets free attack
            damage = max(self.campaign.enemy_attack - 12, 1)  # Minimal flee-failure damage (was -8, min 2)
            self.campaign.health -= damage
            
            if self.campaign.health <= 0:
                return self._handle_player_death()
            
            return (
                f"You try to flee but stumble! [Roll: {flee_roll}] "
                f"The enemy strikes you from behind! {damage} damage! "
                f"HP: {self.campaign.health}/{self.campaign.max_health}. You must fight!"
            )

    @function_tool
    async def use_item(self, ctx: RunContext, item_name: str) -> str:
        """
        Use an item from inventory (healing potions, combat items, etc.).

        Args:
            item_name: The name of the item to use
        """
        logger.info(f"Using item: {item_name}")

        # Search inventory (case-insensitive partial match)
        item_key = item_name.lower().strip()
        matching_items = [item for item in self.campaign.inventory if item_key in item.lower()]
        
        if not matching_items:
            return f"You don't have {item_name}. Check your inventory?"

        item_used = matching_items[0]
        
        # Look up item in game data
        item_data = None
        for key, data in self.game_data["items"].items():
            if key in item_used.lower():
                item_data = data
                break
        
        if not item_data:
            return f"{item_used} cannot be used right now."

        # Apply item effect
        effect = item_data.get("effect", "")
        value = item_data.get("value", 0)
        
        self.campaign.inventory.remove(item_used)
        
        if effect == "restore_health":
            old_health = self.campaign.health
            self.campaign.health = min(self.campaign.health + value, self.campaign.max_health)
            healed = self.campaign.health - old_health
            return (
                f"You drink the {item_used}! Warm energy flows through you. "
                f"Restored {healed} HP. Current HP: {self.campaign.health}/{self.campaign.max_health}."
            )
        
        elif effect == "damage" and self.campaign.in_combat:
            self.campaign.enemy_health -= value
            if self.campaign.enemy_health <= 0:
                return self._handle_combat_victory()
            return (
                f"You unleash the {item_used}! Devastating power strikes the enemy! "
                f"{value} damage! {self.campaign.enemy_name}: {self.campaign.enemy_health}/{self.campaign.enemy_max_health} HP."
            )
        
        else:
            return f"You used {item_used}, but nothing happens."

    @function_tool
    async def accept_quest(self, ctx: RunContext, quest_id: str) -> str:
        """
        Accept a quest from an NPC.

        Args:
            quest_id: The ID of the quest to accept
        """
        logger.info(f"Accepting quest: {quest_id}")

        # Find quest in game data
        quest = None
        for q in self.game_data.get("quests", []):
            if q["id"] == quest_id or quest_id.lower() in q["title"].lower():
                quest = q
                break
        
        if not quest:
            return f"I don't know of any quest called {quest_id}."

        if quest["id"] in self.campaign.active_quests:
            return f"You've already accepted {quest['title']}."

        self.campaign.active_quests.append(quest["id"])
        
        return (
            f"Quest accepted: {quest['title']}. "
            f"{quest['description']} "
            f"Reward: {quest['reward_gold']} gold. Difficulty: {quest['difficulty']}."
        )

    @function_tool
    async def complete_quest(self, ctx: RunContext, quest_id: str) -> str:
        """
        Complete an active quest and receive rewards.

        Args:
            quest_id: The ID of the quest to complete
        """
        logger.info(f"Completing quest: {quest_id}")

        if quest_id not in self.campaign.active_quests:
            return f"You haven't accepted that quest yet."

        # Find quest
        quest = None
        for q in self.game_data.get("quests", []):
            if q["id"] == quest_id:
                quest = q
                break
        
        if not quest:
            return "Quest not found."

        self.campaign.active_quests.remove(quest_id)
        self.campaign.completed_quests.append(quest_id)
        self.campaign.gold += quest["reward_gold"]
        
        for item in quest.get("reward_items", []):
            self.campaign.inventory.append(item)
        
        rewards = ", ".join(quest.get("reward_items", []))
        
        return (
            f"Quest complete: {quest['title']}! "
            f"You receive {quest['reward_gold']} gold and {rewards}. "
            f"Your legend grows! Total gold: {self.campaign.gold}."
        )

    @function_tool
    async def save_campaign(self, ctx: RunContext) -> str:
        """
        Save the current campaign progress to a JSON file.
        """
        logger.info("Saving campaign")

        if not self.campaign.character_name:
            return "Create a character first before saving."

        # Build save data
        save_data = {
            "campaign_id": f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "player_name": self.campaign.player_name,
            "character": {
                "name": self.campaign.character_name,
                "class": self.campaign.character_class,
                "health": self.campaign.health,
                "max_health": self.campaign.max_health,
                "inventory": self.campaign.inventory,
                "gold": self.campaign.gold
            },
            "progress": {
                "current_location": self.campaign.current_location,
                "visited_locations": self.campaign.visited_locations,
                "active_quests": self.campaign.active_quests,
                "completed_quests": self.campaign.completed_quests,
                "major_events": self.campaign.major_events,
                "turn_count": self.campaign.turn_count
            },
            "timestamp": datetime.now().isoformat()
        }

        # Save to file
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_file = os.path.join(GAME_SESSIONS_DIR, f"campaign_{timestamp_str}.json")
        
        try:
            with open(save_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            return f"Your adventure has been saved. May fortune favor you, {self.campaign.character_name}!"
        except Exception as e:
            logger.error(f"Error saving campaign: {e}")
            return "The save failed. An ancient curse blocks the magic!"


async def entrypoint(ctx: JobContext):
    """Main entry point for the D&D Game Master agent."""
    logger.info("Starting D&D Game Master agent")
    
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    # Get game data from prewarm userdata
    game_data = ctx.proc.userdata.get("game_data", {})
    
    # Initialize agent session with proper configuration
    session = AgentSession[CampaignState](
        userdata=CampaignState(),
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash", temperature=0.9),
        tts=murf.TTS(
            voice="en-UK-jaxon",
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
    
    # Start D&D Game Master session
    await session.start(
        agent=DnDGameMaster(game_data),
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
