import requests
import yaml

# configuration
config = yaml.safe_load(open("config.yaml"))
TELEGRAM_TOKEN = config["telegram"]["token"]
TELEGRAM_CHAT_ID = config["telegram"]["chat_id"]

# data
standards_yaml = yaml.safe_load(open("standards.yaml"))
standards = {s["tag"]:{"name":s["name"], "text":s["text"]} for s in standards_yaml["standards"]}

# send a text
def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram send error: {e}")

# main loop
offset = None
queue = []
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
            cmd, tag = update.get("message", {}).get("text", "").strip().lower().split(" ", 1)

            if cmd == "/help":
                send_telegram("/help : list commands\n/std [tag] : list standard by tag, e.g. \"/st 1a\" for Standard I(A)\n/next : give next part of example\n/stats : list stats so far")

            elif cmd == "/std":
                send_telegram(standards[tag]["name"])
                send_telegram(standards[tag]["text"])

            elif cmd == "/stats":
                #TODO: send stats (how many examples read already)
                pass

            elif cmd == "/next":
                #TODO: if there is next in queue - send next
                # if queue is empty - process another example and send
                if len(queue) == 0:
                    # populate queue with an example that has not been sent yet
                    pass

                send_telegram(queue.pop())

    except Exception as e:
        print(f"Telegram poll error: {e}")
        import time;

        time.sleep(5)