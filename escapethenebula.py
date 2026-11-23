import os
import streamlit as st
import random
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
 
client = genai.Client(api_key=api_key) if api_key else None
 
MODEL_NAME = "gemini-3.5-flash-lite"


#Page setup

st.set_page_config(page_title="Escape the Nebula", page_icon="🌌", layout="centered")
st.title("🌌 Escape the Nebula")


if "game_started" not in st.session_state:
    st.session_state.game_started = False

# Initialize the player's stats, inventory, rooms, and game state.
def start_game(name):
    st.session_state.game_started = True
    st.session_state.player_name = name
    st.session_state.health = 5
    st.session_state.max_health = 5
    st.session_state.inventory = []
    st.session_state.rooms = ["cryo_bay", "central_deck", "engeneering_bay", "reactor_core", "escape_pod"]
    st.session_state.room_number = 0
    st.session_state.result_type= ""
    st.session_state.result_message = ""
    st.session_state.result_value = ""
    st.session_state.action_complete = False

# Roll and return a random number from 1 through 6.
def roll_d6():
    return random.randint(1,6)

# Roll and return a random number from 1 through 20.
def roll_d20():
    return random.randint(1,20)

# Display the current room's title and description.
def show_room(title, description):
    st.header(title)
    st.write(description)

# Restarts the game by refreshing the page
def restart_game():
    st.session_state.clear()
    st.rerun()

# Return the room key for the player's current room.
def get_current_room():
    return st.session_state.rooms[st.session_state.room_number]

# Clear the completed action state and advance to the next room.
def continue_game():
    st.session_state.result_type= ""
    st.session_state.result_message = ""
    st.session_state.result_value = ""
    st.session_state.action_complete = False
    st.session_state.room_number += 1
    st.rerun()

# Add an item to the inventory if it is not already present.
def add_item(item):
        if item not in st.session_state.inventory:
            st.session_state.inventory.append(item)

# Return whether the inventory contains the given item.
def has_item(item):
    return item in st.session_state.inventory

# Remove an item from the inventory if it is present.
def remove_item(item):
        if item in st.session_state.inventory:
            st.session_state.inventory.remove(item)


# Subtract damage from health without allowing health below zero.
def take_damage(amount):
    st.session_state.health = st.session_state.health - amount
    if st.session_state.health < 0:
        st.session_state.health = 0

# Restore health up to the maximum and return the actual amount healed.
def heal_player(amount):
    old_health = st.session_state.health
    st.session_state.health = min(st.session_state.max_health, st.session_state.health + amount)
    return st.session_state.health - old_health

# Ask Gemini to narrate an action outcome, or return the fallback text.
def generate_story(room, action, outcome, fallback_message):
    if client is None:
        return fallback_message

    inventory_text = ", ".join(st.session_state.inventory)
    prompt = f"""
You are the storyteller for a dark fantasy
adventure game called Escape the Castle.
 
Player: {st.session_state.player_name}
Room: {room}
Health: {st.session_state.health}/{st.session_state.max_health}
Inventory: {inventory_text}
 
Action:
{action}
 
Outcome:
{outcome}
 
Describe what happens in 30-50 words.
Use second person.
Use Sci-Fi languae and speak like you are in a hurry
Do not change the outcome.
Do not change health or inventory.
Do not introduce new choices.
"""
    try:
        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=prompt,
            generation_config={"thinking_level": "minimal"}
        )
        if interaction.output_text:
            return interaction.output_text
        return fallback_message
    except Exception as error:
        st.error(f"Gemini error: {error}")
        return fallback_message


# Show an encounter button and resolve a chance roll as success or damage.
def chance_encounter(button_text, room, action, success_number, success_outcome, success_fallback, failure_outcome, failure_fallback, damage, bonus_item = ""):
    if st.button(button_text):
        roll = roll_d6()
        if bonus_item != "" and has_item(bonus_item):
            roll = roll + 2
        if roll >= success_number:
            story = generate_story(room, action, success_outcome, success_fallback)
            set_result("success", story)
        else:
            take_damage(damage)
            story = generate_story(room, action, failure_outcome, failure_fallback)
            set_result("damage", story, damage)
        st.rerun()

#Showing Player info
# Display the player's name, health, inventory, and current room position.
def show_player_info():
    st.subheader(f"👨 {st.session_state.player_name}")
    left, right = st.columns(2)
    with left:
        st.write(f"❤️ Health: {st.session_state.health} / {st.session_state.max_health}")
    with right:
        st.write(f"🎒 Inventory: {', '.join(st.session_state.inventory)}")
    st.caption(
        f"room {st.session_state.room_number +1}"
        f"of {len(st.session_state.rooms)}" 
    )
    st.divider()

# Store an action result, mark the action complete, and rerun the app.
def set_result(result_type, message, value = ""):
    st.session_state.result_type = result_type
    st.session_state.result_message = message
    st.session_state.result_value = value
    st.session_state.action_complete = True
    st.rerun()

# Display a styled message for the current action result.
def show_result():
    kind = st.session_state.result_type
    value = st.session_state.result_value
 
    if kind == "item":
        st.success(f"🎒 NEW ITEM: {value}")
    elif kind == "damage":
        st.error(f"💔 DAMAGE: You lose {value} health.")
    elif kind == "heal":
        st.success(f"💚 HEALED: You recover {value} health.")
    elif kind == "success":
        st.success("✅ Success!")
    else:
        st.info("The journey continues...")
 
    st.write(st.session_state.result_message)

# Display a button that advances the game when clicked.
def show_continue_button(text = "Continue"):
    if st.button(text):
        continue_game()
