#!/usr/bin/env python3
import sys
import json
import requests
import websocket

# ─── CONFIG ────────────────────────────────────────────────────────────────────
APP_KEY          = "32cbd69e4b950bf97679"          # Kick’s public Pusher key
CLUSTER          = "us2"                          # Kick’s Pusher cluster (us2 = Ohio)
# Use the same client & version Kick’s web client uses :contentReference[oaicite:0]{index=0}
WS_URL_TEMPLATE  = "wss://ws-{cluster}.pusher.com/app/{key}?protocol=7&client=js&version=7.6.0&flash=false"
CHANNEL_INFO_URL = "https://kick.com/api/v2/channels/{slug}"
# ────────────────────────────────────────────────────────────────────────────────

def fetch_chatroom_id(slug: str) -> int:
    """Fetch the numeric chatroom ID for a given channel slug."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"}
    resp = requests.get(CHANNEL_INFO_URL.format(slug=slug), headers=headers)
    resp.raise_for_status()
    return resp.json()["chatroom"]["id"]

def on_open(ws):
    print("🔗 Connection opened, waiting for handshake…")

def on_message(ws, raw):
    msg = json.loads(raw)
    ev  = msg.get("event")

    # 1) Handshake → subscribe to v2 channel
    if ev == "pusher:connection_established":
        data      = json.loads(msg["data"])
        socket_id = data["socket_id"]
        channel   = f"chatrooms.{CHATROOM_ID}.v2"
        sub = {
            "event": "pusher:subscribe",
            "data": {
                "auth": "",      # must include, even if empty :contentReference[oaicite:1]{index=1}
                "channel": channel
            }
        }
        ws.send(json.dumps(sub))
        print(f"✅ Subscribed to {channel}")

    # 2) Keep-alive
    elif ev == "pusher:ping":
        ws.send(json.dumps({"event": "pusher:pong", "data": {}}))

    # 3) Chat message event
    elif ev == "App\\Events\\ChatMessageEvent":
        payload = json.loads(msg["data"])
        user    = payload["sender"]["username"]
        text    = payload["content"]
        print(f"{user}: {text}")

def on_error(ws, err):
    print("⚠️ Error:", err)

def on_close(ws, code, reason):
    print("🔌 Connection closed:", code, reason)

def main(slug: str):
    global CHATROOM_ID
    CHATROOM_ID = fetch_chatroom_id(slug)
    ws_url = WS_URL_TEMPLATE.format(cluster=CLUSTER, key=APP_KEY)

    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    print(f"📡 Connecting to {ws_url}…")
    ws.run_forever()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kick-chat.py <channel_slug>")
        sys.exit(1)
    main(sys.argv[1])
