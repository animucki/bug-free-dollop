import requests
import time
import yaml
import json
import random
import os

# configuration
config = yaml.safe_load(open("config.yaml"))
TELEGRAM_TOKEN = config["telegram"]["token"]
TELEGRAM_CHAT_ID = config["telegram"]["chat_id"]
STATE_FILE = "state.json"

# data
standards_yaml = yaml.safe_load(open("standards.yaml"))
standards = {s["tag"]: {"name": s["name"], "text": s["text"]} for s in standards_yaml["standards"]}

# build flat list of all examples with a stable identity key
all_examples = []
for s in standards_yaml["standards"]:
    for i, ex in enumerate(s.get("examples", [])):
        all_examples.append({
            "id": f"{s['tag']}_{i}",
            "title": ex["title"],
            "text": ex["text"],
            "comment": ex["comment"],
        })

total_examples = len(all_examples)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"sent": [], "prestige": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def build_queue(state):
    sent_ids = set(state["sent"])
    remaining = [ex for ex in all_examples if ex["id"] not in sent_ids]
    random.shuffle(remaining)
    return remaining

def example_to_messages(ex):
    """
    Returns an ordered list of message strings for an example.
    Splits text and comment on '<...>', prefixes comment's first chunk with 'Comment: '.
    All messages except the last end with ' (...)'.
    """
    parts = []
    parts.append(ex["title"])

    text_chunks = [c.strip() for c in ex["text"].split("<...>")]
    parts.extend(text_chunks)

    comment_chunks = [c.strip() for c in ex["comment"].split("<...>")]
    comment_chunks[0] = "Comment: " + comment_chunks[0]
    parts.extend(comment_chunks)

    # append (...) to all but last
    result = []
    for i, p in enumerate(parts):
        if i < len(parts) - 1:
            result.append(p + " (...)")
        else:
            result.append(p)
    return result


def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram send error: {e}")


# initialize state and queue
state = load_state()
queue = build_queue(state)      # list of example dicts, not yet sent
msg_queue = []                  # list of strings: messages for current in-progress example
current_example_id = None       # id of example currently being sent

offset = None

while True:
    try:
        params = {"timeout": 30}
        if offset is not None:
            params["offset"] = offset
        r = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
            params=params,
            timeout=40
        )
        for update in r.json().get("result", []):
            offset = update["update_id"] + 1
            text = update.get("message", {}).get("text", "").strip()
            if not text:
                continue

            parts = text.lower().split(" ", 1)
            cmd = parts[0]
            tag = parts[1] if len(parts) > 1 else ""

            if cmd == "/help":
                send_telegram(
                    "/help : list commands\n"
                    "/std [tag] : show standard by tag, e.g. \"/std 1a\"\n"
                    "/next : send next message of the current example\n"
                    "/stats : show progress"
                )

            elif cmd == "/std":
                if tag in standards:
                    send_telegram(standards[tag]["name"])
                    send_telegram(standards[tag]["text"])
                else:
                    send_telegram(f"Unknown tag: {tag}")

            elif cmd == "/stats":
                count = len(state["sent"])
                prestige = state["prestige"]
                if prestige > 0:
                    send_telegram(f"{count}/{total_examples}, prestige level {prestige}")
                else:
                    send_telegram(f"{count}/{total_examples}")

            elif cmd == "/next":
                # if no messages buffered, load next example
                if not msg_queue:
                    if not queue:
                        # all examples done — prestige up and reset
                        state["prestige"] += 1
                        state["sent"] = []
                        save_state(state)
                        queue = build_queue(state)
                        send_telegram(
                            f"You've completed all examples! "
                            f"Starting prestige level {state['prestige']}."
                        )

                    ex = queue.pop(0)
                    current_example_id = ex["id"]
                    msg_queue = example_to_messages(ex)

                msg = msg_queue.pop(0)
                send_telegram(msg)

                # if we just sent the last message of this example, mark as done
                if not msg_queue and current_example_id is not None:
                    state["sent"].append(current_example_id)
                    save_state(state)
                    current_example_id = None

    except Exception as e:
        print(f"Telegram poll error: {e}")
        time.sleep(5)