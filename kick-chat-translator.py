#!/usr/bin/env python3
import sys
import json
import requests
import websocket
import os
import html
import uuid
from langdetect import detect
import time
import threading
from typing import Optional
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()

# ─── CONFIG ────────────────────────────────────────────────────────────────────
APP_KEY          = "32cbd69e4b950bf97679"          # Kick's public Pusher key
CLUSTER          = "us2"                          # Kick's Pusher cluster (us2 = Ohio)
WS_URL_TEMPLATE  = "wss://ws-{cluster}.pusher.com/app/{key}?protocol=7&client=js&version=7.6.0&flash=false"
CHANNEL_INFO_URL = "https://kick.com/api/v2/channels/{slug}"
CHAT_API_URL_TEMPLATE = "https://kick.com/api/v2/messages/send/{chatroom_id}"

# Azure Translator API setup
AZURE_TRANSLATOR_KEY = os.getenv('AZURE_TRANSLATOR_KEY')  # Your Azure Translator subscription key
AZURE_TRANSLATOR_ENDPOINT = os.getenv('AZURE_TRANSLATOR_ENDPOINT', 'https://api.cognitive.microsofttranslator.com')  # Your Azure Translator endpoint
AZURE_TRANSLATOR_REGION = os.getenv('AZURE_TRANSLATOR_REGION')  # Your Azure Translator region (e.g., 'eastus')

# Bot configuration - Load from environment variables
KICK_AUTH_TOKEN = os.getenv('KICK_AUTH_TOKEN')  # Load from .env file
TARGET_LANGUAGE = os.getenv('TARGET_LANGUAGE', 'en')  # Translate to English
MIN_MESSAGE_LENGTH = int(os.getenv('MIN_MESSAGE_LENGTH', '1'))  # Allow very short messages
TRANSLATION_PREFIX = os.getenv('TRANSLATION_PREFIX', '🌐 ')  # Prefix for translated messages
RATE_LIMIT_DELAY = int(os.getenv('RATE_LIMIT_DELAY', '0'))  # No rate limiting
BOT_USERNAME = os.getenv('BOT_USERNAME', '').lower()  # Your bot's username to avoid self-translation

# Languages to allow translating (top 20 most spoken, one per country)
ALLOWED_LANGUAGES = {
    'zh',   # Chinese (Mandarin)
    'es',   # Spanish
    'en',   # English
    'hi',   # Hindi
    'ar',   # Arabic
    'ru',   # Russian
    'ja',   # Japanese
    'de',   # German
    'jv',   # Javanese (Indonesia)
    'tr',   # Turkish
    'ko',   # Korean
    'fr',   # French
    'vi',   # Vietnamese
    'th',   # Thai
}

# Common English chat phrases to skip translation
COMMON_ENGLISH_PHRASES = {
    'lol', 'gg', 'wp', 'ez', 'kekw', 'pog', 'poggers', 'omegalul', 'lul', 'xd', 'lmao',
    'rofl', 'wtf', 'brb', 'afk', 'hi', 'hello', 'bye', 'thanks', 'thank you', 'ok', 'okay',
    'nice', 'good', 'bad', 'cool', 'great', 'awesome', 'amazing', 'wow', 'yes', 'no',
    'yo', 'sup', 'yo!', 'yo.', 'yo?', 'yo~', 'yo-', 'yo_', 'yo,', 'yo;', 'yo:', 'yo!',
    'hii', 'hiii', 'hiiii', 'hiiiii', 'hi!', 'hi.', 'hi,', 'hi;', 'hi:', 'hi~', 'hi-', 'hi_',
    'bye!', 'bye.', 'bye,', 'bye;', 'bye:', 'bye~', 'bye-', 'bye_',
}

# ────────────────────────────────────────────────────────────────────────────────

class KickChatTranslator:
    def __init__(self, channel_slug: str, auth_token: str):
        self.channel_slug = channel_slug
        self.auth_token = auth_token
        self.chatroom_id = None
        self.azure_translator_key = AZURE_TRANSLATOR_KEY
        self.azure_translator_endpoint = AZURE_TRANSLATOR_ENDPOINT
        self.azure_translator_region = AZURE_TRANSLATOR_REGION
        self.last_translation_time = 0
        self.translated_messages = set()  # Track translated messages to avoid loops
        
        # Create persistent HTTP session for faster requests
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://kick.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })
        
    def fetch_channel_info(self):
        """Fetch channel information including chatroom ID and broadcaster user ID."""
        print(f"🔍 Checking channel: {self.channel_slug}")
        
        # Try multiple methods to get channel info
        methods = [
            self._fetch_via_api,
            self._fetch_via_manual_config
        ]
        
        for method in methods:
            try:
                if method():
                    return
            except Exception as e:
                print(f"⚠️ Method failed: {e}")
                continue
        
        print(f"❌ Could not access channel '{self.channel_slug}' using any method.")
        print("💡 Possible solutions:")
        print("   1. Wait a few minutes and try again (Kick may be rate limiting)")
        print("   2. Try a different channel")
        print("   3. Use manual configuration (set CHATROOM_ID and BROADCASTER_ID env vars)")
        sys.exit(1)
    
    def _fetch_via_api(self):
        """Try to fetch channel info via API."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://kick.com/",
            "Origin": "https://kick.com"
        }
        
        url = CHANNEL_INFO_URL.format(slug=self.channel_slug)
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 403:
            error_data = resp.json() if resp.content else {}
            if "security policy" in error_data.get("error", "").lower():
                print("🚫 Kick API blocked by security policy - trying alternative method...")
                return False
            else:
                print(f"🚫 Access forbidden to channel '{self.channel_slug}'")
                return False
        elif resp.status_code == 404:
            print(f"❌ Channel '{self.channel_slug}' not found via API")
            return False
        elif resp.status_code == 429:
            print("⏱️ Rate limited by Kick API")
            return False
        
        resp.raise_for_status()
        data = resp.json()
        
        if "chatroom" not in data or "user" not in data:
            print(f"⚠️ Unexpected API response structure")
            return False
        
        self.chatroom_id = data["chatroom"]["id"]
        print(f"✅ Channel found via API: {data['user']['username']} (ID: {data['user']['id']})")
        print(f"💬 Chatroom ID: {self.chatroom_id}")
        return True
    
    def _fetch_via_manual_config(self):
        """Try to use manual configuration from environment variables."""
        manual_chatroom_id = os.getenv('CHATROOM_ID')
        manual_broadcaster_id = os.getenv('BROADCASTER_ID')
        
        if manual_chatroom_id and manual_broadcaster_id:
            self.chatroom_id = int(manual_chatroom_id)
            print(f"✅ Using manual configuration:")
            print(f"💬 Chatroom ID: {self.chatroom_id}")
            print(f"📺 Broadcaster ID: {manual_broadcaster_id}")
            return True
        
        return False
        
    def detect_language(self, text: str) -> Optional[str]:
        """Detect the language of the given text."""
        try:
            # Remove common chat elements that might confuse detection
            clean_text = text.strip()
            if len(clean_text) < MIN_MESSAGE_LENGTH:
                return None
                
            # Skip if text is mostly emojis or special characters
            alpha_chars = sum(c.isalpha() for c in clean_text)
            if alpha_chars < 1:  # Allow single character words
                return None
                
            # Skip Kick emotes format [emote:id:name]
            if clean_text.startswith('[emote:') and clean_text.endswith(']'):
                return 'en'  # Treat emotes as English to skip translation
            
            # For all-caps text, convert to lowercase for better language detection
            detection_text = clean_text.lower() if clean_text.isupper() else clean_text
            lang = detect(detection_text)
            
            return lang
        except Exception as e:
            print(f"⚠️ Language detection error: {e}")
            return None
            
    def clean_text_for_translation(self, text: str) -> str:
        """Clean text by removing emotes and other non-translatable content."""
        # Remove Kick emotes [emote:id:name]
        cleaned = re.sub(r'\[emote:\d+:[^\]]+\]', '', text)
        
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def translate_text(self, text: str, source_lang: str) -> Optional[str]:
        """Translate text from source language to target language using Azure Translator."""
        try:
            # Clean the text before translation to save on character costs
            clean_text = self.clean_text_for_translation(text)
            
            # Don't translate if nothing left after cleaning
            if not clean_text:
                return None
            
            if not self.azure_translator_key:
                print("⚠️ Azure Translator key not provided - cannot translate")
                return None
            
            # Azure Translator API endpoint
            path = '/translate'
            constructed_url = self.azure_translator_endpoint + path
            
            params = {
                'api-version': '3.0',
                'from': source_lang,
                'to': TARGET_LANGUAGE
            }
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.azure_translator_key,
                'Ocp-Apim-Subscription-Region': self.azure_translator_region,
                'Content-type': 'application/json',
                'X-ClientTraceId': str(uuid.uuid4())
            }
            
            # Request body
            body = [{
                'text': clean_text
            }]
            
            # Make the translation request using the persistent session
            response = self.session.post(constructed_url, params=params, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            
            # Parse response
            translation_result = response.json()
            if translation_result and len(translation_result) > 0:
                translated_text = translation_result[0]['translations'][0]['text']
                # Decode HTML entities (like &#39; -> ')
                translated_text = html.unescape(translated_text)
                return translated_text
            else:
                print("⚠️ Empty translation response from Azure")
                return None
                
        except Exception as e:
            print(f"⚠️ Translation error: {e}")
            return None
            
    def should_translate(self, text: str, detected_lang: str, username: str = "") -> bool:
        """Determine if a message should be translated."""
        # Don't translate if already in target language
        if detected_lang == TARGET_LANGUAGE:
            print(f"   🔍 should_translate: Already in target language ({TARGET_LANGUAGE})")
            return False
            
        # Don't translate very short messages
        if len(text.strip()) < MIN_MESSAGE_LENGTH:
            print(f"   🔍 should_translate: Too short ({len(text.strip())} < {MIN_MESSAGE_LENGTH})")
            return False
            
        # Don't translate if message starts with translation prefix (avoid loops)
        if text.strip().startswith(TRANSLATION_PREFIX):
            print(f"   🔍 should_translate: Starts with translation prefix")
            return False
            
        # Don't translate messages from known translation bots (including our own bot)
        bot_names = ['chattranslator', 'aitranslatorbot', 'translator', 'translate_bot', 'kickbot']
        if username.lower() in bot_names:
            print(f"   🔍 should_translate: Known translation bot: {username}")
            return False
            
        # Rate limiting
        if RATE_LIMIT_DELAY > 0:  # Only check rate limiting if delay is set
            current_time = time.time()
            time_since_last = current_time - self.last_translation_time
            if time_since_last < RATE_LIMIT_DELAY:
                print(f"   🔍 should_translate: Rate limited ({time_since_last:.2f}s < {RATE_LIMIT_DELAY}s)")
                return False
            
        print(f"   ✅ should_translate: All checks passed - will translate")
        return True
        
    def send_chat_message(self, message: str):
        """Send a message to the chat using Kick API."""
        if not self.auth_token:
            print("⚠️ No auth token provided - cannot send messages")
            return False
            
        # Use the correct API endpoint format
        api_url = CHAT_API_URL_TEMPLATE.format(chatroom_id=self.chatroom_id)
        
        # Add auth and referer headers to the session for this request
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Referer": f"https://kick.com/{self.channel_slug}"
        }
        
        # Use the correct payload format based on your request
        payload = {
            "content": message,
            "type": "message"
        }
        
        try:
            # Use persistent session for faster requests with longer timeout
            resp = self.session.post(api_url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                print(f"✅ Translation sent: {message}")
                self.last_translation_time = time.time()
                return True
            else:
                print(f"⚠️ Failed to send message. Status: {resp.status_code}, Response: {resp.text}")
                return False
        except Exception as e:
            print(f"⚠️ Error sending message: {e}")
            return False
            
    def process_message(self, username: str, message: str):
        """Process an incoming chat message for translation."""
        # Skip messages from the bot itself
        if BOT_USERNAME and username.lower() == BOT_USERNAME:
            return
            
        # Skip very short messages
        if len(message.strip()) < MIN_MESSAGE_LENGTH:
            return
            
        # Clean message for language detection (remove emotes)
        clean_message = self.clean_text_for_translation(message)
        if not clean_message:
            return
            
        # Skip common English chat phrases
        if clean_message.lower() in COMMON_ENGLISH_PHRASES:
            print(f"   ⏭️ Skipped: Common English phrase '{clean_message}'")
            return
            
        # Skip messages that start with '!'
        if clean_message.startswith('!'):
            print(f"   ⏭️ Skipped: Command message '{clean_message}'")
            return
            
        # Detect language
        detected_lang = self.detect_language(clean_message)
        if not detected_lang:
            return
            
        print(f"👤 {username} [{detected_lang}]: {message}")
        
        # Debug: Show why messages aren't being translated
        if detected_lang == TARGET_LANGUAGE:
            print(f"   ⏭️ Skipped: Already in {TARGET_LANGUAGE}")
            return
            
        # Only allow top 20 most spoken languages
        if detected_lang not in ALLOWED_LANGUAGES:
            print(f"   ⏭️ Skipped: Language {detected_lang} not in allowed list")
            return
        
        # Check if translation is needed
        should_translate_result = self.should_translate(clean_message, detected_lang, username)
        if not should_translate_result:
            # More detailed debugging
            print(f"   ⏭️ Skipped: should_translate() returned False")
            print(f"   📝 Debug info - Text: '{clean_message}', Lang: {detected_lang}, User: {username}")
            return
            
        # Translate the cleaned message
        translated = self.translate_text(clean_message, detected_lang)
        if not translated:
            return
            
        # Create translation message with new format
        translation_msg = f"[by {username}] {translated} ({detected_lang} > {TARGET_LANGUAGE})"
        
        # Send translation to chat immediately (no artificial delay)
        def send_async():
            self.send_chat_message(translation_msg)
            
        threading.Thread(target=send_async, daemon=True).start()
        
    # WebSocket event handlers
    def on_open(self, ws):
        print("🔗 Connection opened, waiting for handshake…")

    def on_message(self, ws, raw):
        msg = json.loads(raw)
        ev = msg.get("event")

        # 1) Handshake → subscribe to v2 channel
        if ev == "pusher:connection_established":
            data = json.loads(msg["data"])
            socket_id = data["socket_id"]
            channel = f"chatrooms.{self.chatroom_id}.v2"
            sub = {
                "event": "pusher:subscribe",
                "data": {
                    "auth": "",
                    "channel": channel
                }
            }
            ws.send(json.dumps(sub))
            print(f"✅ Subscribed to {channel}")

        # 2) Keep-alive - respond to ping immediately
        elif ev == "pusher:ping":
            pong_response = {"event": "pusher:pong", "data": {}}
            ws.send(json.dumps(pong_response))
            print("💓 Pong sent")

        # 3) Chat message event
        elif ev == "App\\Events\\ChatMessageEvent":
            payload = json.loads(msg["data"])
            user = payload["sender"]["username"]
            text = payload["content"]
            
            # Process message for translation
            self.process_message(user, text)

    def on_error(self, ws, err):
        print("⚠️ WebSocket Error:", err)

    def on_close(self, ws, code, reason):
        print(f"🔌 Connection closed: {code} {reason}")
        if code != 1000:  # 1000 = normal closure
            print("⚠️ Unexpected closure - will attempt to reconnect in 5 seconds...")
            time.sleep(5)
            self.start()  # Auto-reconnect
        
    def start(self):
        """Start the translator bot."""
        print(f"🤖 Starting Kick Chat Translator for channel: {self.channel_slug}")
        
        # Fetch channel information
        self.fetch_channel_info()
        
        # Setup WebSocket connection
        ws_url = WS_URL_TEMPLATE.format(cluster=CLUSTER, key=APP_KEY)
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        print(f"📡 Connecting to {ws_url}…")
        print(f"🌐 Translation enabled: Non-English → English")
        
        if self.auth_token:
            print("✅ Auth token provided - translations will be posted to chat")
        else:
            print("⚠️ No auth token - will only display translations (not post them)")
            
        ws.run_forever()

def main():
    channel = os.getenv("KICK_CHANNEL")
    if not channel and len(sys.argv) >= 2:
        channel = sys.argv[1]
    if not channel:
        print("Usage: python kick-chat-translator.py <channel> [auth_token]")
        sys.exit(1)

    auth_token = None
    if len(sys.argv) >= 3:
        auth_token = sys.argv[2]
    elif KICK_AUTH_TOKEN:
        auth_token = KICK_AUTH_TOKEN

    if auth_token:
        print("🗝️  Auth token provided – translations will be posted to chat.")
    else:
        print("👀 No auth token – read-only mode.")

    if not AZURE_TRANSLATOR_KEY:
        print("⚠️ Azure Translator key not found. Please set AZURE_TRANSLATOR_KEY in your .env file.")
        sys.exit(1)

    translator = KickChatTranslator(channel, auth_token)
    translator.start()

if __name__ == "__main__":
    main() 
