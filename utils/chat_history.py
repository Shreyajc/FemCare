import os
import json
from datetime import datetime

HISTORY_FOLDER = "chat_history"

os.makedirs(HISTORY_FOLDER, exist_ok=True)


# ==========================================
# Generate Chat Title
# ==========================================

def generate_title(messages):

    if not messages:
        return "New Conversation"

    first = ""

    for msg in messages:

        if msg["role"] == "user":
            first = msg["content"].strip()
            break

    if first.lower() in ["hi", "hello", "hey", "hii", "yo"]:
        return "New Conversation"

    if len(first) > 40:
        return first[:40] + "..."

    return first.title()


# ==========================================
# Save Chat
# ==========================================

def save_chat(messages, conversation_id):

    if not messages:
        return

    filename = f"{conversation_id}.json"

    filepath = os.path.join(HISTORY_FOLDER, filename)

    chat = {

        "title": generate_title(messages),

        "created_at": datetime.now().strftime(
            "%d %b %Y %I:%M %p"
        ),

        "messages": messages

    }

    with open(filepath, "w", encoding="utf-8") as f:

        json.dump(
            chat,
            f,
            indent=4,
            ensure_ascii=False
        )

# ==========================================
# Get Chat List
# ==========================================

def get_history():

    chats = []

    if not os.path.exists(HISTORY_FOLDER):
        return chats

    for file in sorted(
        os.listdir(HISTORY_FOLDER),
        reverse=True
    ):

        if file.endswith(".json"):
            chats.append(file)

    return chats


# ==========================================
# Get Chat Information
# ==========================================

def get_chat_info(filename):

    path = os.path.join(HISTORY_FOLDER, filename)

    with open(path, "r", encoding="utf-8") as f:

        data = json.load(f)

    if isinstance(data, list):

        return {

            "title": filename,

            "created_at": ""

        }

    return {

        "title": data.get("title", filename),

        "created_at": data.get("created_at", "")

    }


# ==========================================
# Load Chat
# ==========================================

def load_chat(filename):

    path = os.path.join(HISTORY_FOLDER, filename)

    with open(path, "r", encoding="utf-8") as f:

        data = json.load(f)

    if isinstance(data, list):
        return data

    return data.get("messages", [])


def rename_chat(filename, new_title):

    path = os.path.join(HISTORY_FOLDER, filename)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):

        data = {
            "title": new_title,
            "created_at": "",
            "messages": data
        }

    else:
        data["title"] = new_title

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def delete_chat(filename):

    path = os.path.join(HISTORY_FOLDER, filename)

    if os.path.exists(path):
        os.remove(path)