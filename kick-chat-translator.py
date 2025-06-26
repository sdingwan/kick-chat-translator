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
BROADCASTER_USER_ID = None  # Will be fetched automatically
TARGET_LANGUAGE = os.getenv('TARGET_LANGUAGE', 'en')  # Translate to English
MIN_MESSAGE_LENGTH = int(os.getenv('MIN_MESSAGE_LENGTH', '1'))  # Allow very short messages
TRANSLATION_PREFIX = os.getenv('TRANSLATION_PREFIX', '🌐 ')  # Prefix for translated messages
RATE_LIMIT_DELAY = int(os.getenv('RATE_LIMIT_DELAY', '0'))  # No rate limiting
BOT_USERNAME = os.getenv('BOT_USERNAME', '').lower()  # Your bot's username to avoid self-translation

# Languages to skip translating (comma-separated language codes)
BLACKLISTED_LANGUAGES = set(os.getenv('BLACKLISTED_LANGUAGES', 'af,it,cy,sw,so,pl,ro,fr,no,sv,tl,de,es,id,et,sq,ca,fi,nl,da,vi,pt,hr,sl,hu,sk,lv,lt,cs').split(','))

# ────────────────────────────────────────────────────────────────────────────────

class KickChatTranslator:
    def __init__(self, channel_slug: str, auth_token: str):
        self.channel_slug = channel_slug
        self.auth_token = auth_token
        self.chatroom_id = None
        self.broadcaster_user_id = None
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
        headers = {"User-Agent": "Mozilla/5.0 (compatible; TranslatorBot/1.0)"}
        resp = requests.get(CHANNEL_INFO_URL.format(slug=self.channel_slug), headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        self.chatroom_id = data["chatroom"]["id"]
        self.broadcaster_user_id = data["user"]["id"]
        print(f"📺 Channel: {data['user']['username']} (ID: {self.broadcaster_user_id})")
        print(f"💬 Chatroom ID: {self.chatroom_id}")
        
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
                
            # Skip common English words/expressions that might be misdetected
            english_words = {
                'nice', 'good', 'bad', 'lol', 'wow', 'yes', 'no', 'ok', 'okay', 'hi', 'hello', 
                'bye', 'thanks', 'thank', 'you', 'cool', 'great', 'awesome', 'amazing',
                'kekw', 'poggers', 'pog', 'omegalul', 'lul', 'ez', 'gg', 'wp', 'nt',
                'morning', 'what', 'how', 'are', 'whats', 'up', 'well', 'time', 'here',
                'about', 'watch', 'happy', 'streaming', 'breakfast', 'sleep', 'hiiiii'
            }
            if clean_text.lower() in english_words:
                return 'en'  # Force English for these words
                
            # Skip Kick emotes format [emote:id:name]
            if clean_text.startswith('[emote:') and clean_text.endswith(']'):
                return 'en'  # Treat emotes as English to skip translation
            
            # For all-caps text, convert to lowercase for better language detection
            detection_text = clean_text.lower() if clean_text.isupper() else clean_text
            lang = detect(detection_text)
            
            # Additional check: if detected as non-English but text looks English-ish
            if lang != 'en' and len(clean_text) < 15:
                # Count English-looking words
                words = clean_text.lower().split()
                english_looking = sum(1 for word in words if word in english_words)
                # Override if most words are in our English words list
                if len(words) > 0 and english_looking >= len(words) * 0.8:  # 80% or more are English words
                    return 'en'
            
            return lang
        except Exception as e:
            print(f"⚠️ Language detection error: {e}")
            return None
            
    def clean_text_for_translation(self, text: str) -> str:
        """Clean text by removing emotes and other non-translatable content."""
        import re
        
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
            
        # Detect language
        detected_lang = self.detect_language(clean_message)
        if not detected_lang:
            return
            
        print(f"👤 {username} [{detected_lang}]: {message}")
        
        # Debug: Show why messages aren't being translated
        if detected_lang == TARGET_LANGUAGE:
            print(f"   ⏭️ Skipped: Already in {TARGET_LANGUAGE}")
            return
            
        # Skip blacklisted languages
        if detected_lang in BLACKLISTED_LANGUAGES:
            print(f"   ⏭️ Skipped: Language {detected_lang} is blacklisted")
            return
            
        # Additional check: Don't translate obviously English phrases misdetected as other languages
        obvious_english_phrases = [
            'good morning', 'how are you', 'whats up', 'hello', 'hi there',
            'morning', 'how was your sleep', 'did you sleep well', 'happy streaming'
        ]
        if any(phrase in clean_message.lower() for phrase in obvious_english_phrases):
            print(f"   ⏭️ Skipped: Obvious English phrase misdetected as {detected_lang}")
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
        flag, lang_name = self.get_language_info(detected_lang)
        translation_msg = f"[by {username}] {translated} ({detected_lang} > {TARGET_LANGUAGE})"
        
        # Send translation to chat immediately (no artificial delay)
        def send_async():
            self.send_chat_message(translation_msg)
            
        threading.Thread(target=send_async, daemon=True).start()
        
    def get_language_info(self, lang_code: str) -> tuple:
        """Get emoji flag and language name for language code."""
        language_info = {
            'es': ('🇪🇸', 'Spanish'),
            'fr': ('🇫🇷', 'French'),
            'de': ('🇩🇪', 'German'),
            'it': ('🇮🇹', 'Italian'),
            'pt': ('🇵🇹', 'Portuguese'),
            'ru': ('🇷🇺', 'Russian'),
            'ja': ('🇯🇵', 'Japanese'),
            'ko': ('🇰🇷', 'Korean'),
            'zh': ('🇨🇳', 'Chinese'),
            'ar': ('🇸🇦', 'Arabic'),
            'hi': ('🇮🇳', 'Hindi'),
            'tr': ('🇹🇷', 'Turkish'),
            'pl': ('🇵🇱', 'Polish'),
            'nl': ('🇳🇱', 'Dutch'),
            'sv': ('🇸🇪', 'Swedish'),
            'da': ('🇩🇰', 'Danish'),
            'no': ('🇳🇴', 'Norwegian'),
            'fi': ('🇫🇮', 'Finnish'),
            'th': ('🇹🇭', 'Thai'),
            'vi': ('🇻🇳', 'Vietnamese'),
            'uk': ('🇺🇦', 'Ukrainian'),
            'bg': ('🇧🇬', 'Bulgarian'),
            'cs': ('🇨🇿', 'Czech'),
            'sk': ('🇸🇰', 'Slovak'),
            'hr': ('🇭🇷', 'Croatian'),
            'sl': ('🇸🇮', 'Slovenian'),
            'et': ('🇪🇪', 'Estonian'),
            'lv': ('🇱🇻', 'Latvian'),
            'lt': ('🇱🇹', 'Lithuanian'),
            'hu': ('🇭🇺', 'Hungarian'),
            'ro': ('🇷🇴', 'Romanian'),
            'el': ('🇬🇷', 'Greek'),
            'he': ('🇮🇱', 'Hebrew'),
            'fa': ('🇮🇷', 'Persian'),
            'ur': ('🇵🇰', 'Urdu'),
            'bn': ('🇧🇩', 'Bengali'),
            'ta': ('🇮🇳', 'Tamil'),
            'te': ('🇮🇳', 'Telugu'),
            'ml': ('🇮🇳', 'Malayalam'),
            'kn': ('🇮🇳', 'Kannada'),
            'gu': ('🇮🇳', 'Gujarati'),
            'pa': ('🇮🇳', 'Punjabi'),
            'mr': ('🇮🇳', 'Marathi'),
            'ne': ('🇳🇵', 'Nepali'),
            'si': ('🇱🇰', 'Sinhala'),
            'my': ('🇲🇲', 'Myanmar'),
            'km': ('🇰🇭', 'Khmer'),
            'lo': ('🇱🇦', 'Lao'),
            'ka': ('🇬🇪', 'Georgian'),
            'am': ('🇪🇹', 'Amharic'),
            'sw': ('🇰🇪', 'Swahili'),
            'zu': ('🇿🇦', 'Zulu'),
            'af': ('🇿🇦', 'Afrikaans'),
            'is': ('🇮🇸', 'Icelandic'),
            'mt': ('🇲🇹', 'Maltese'),
            'cy': ('🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'Welsh'),
            'ga': ('🇮🇪', 'Irish'),
            'eu': ('🏴󠁥󠁳󠁰󠁶󠁿', 'Basque'),
            'ca': ('🏴󠁥󠁳󠁣󠁴󠁿', 'Catalan'),
            'gl': ('🏴󠁥󠁳󠁧󠁡󠁿', 'Galician'),
            'id': ('🇮🇩', 'Indonesian'),
            'ms': ('🇲🇾', 'Malay'),
            'tl': ('🇵🇭', 'Filipino'),
        }
        return language_info.get(lang_code, ('🌍', 'Unknown'))
        
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
    if len(sys.argv) < 2:
        print("Usage: python kick-chat-translator.py <channel_slug> [auth_token]")
        print("\nAuth token options:")
        print("1. Set KICK_AUTH_TOKEN in .env file (recommended)")
        print("2. Pass as command line argument")
        print("\nTo get your auth token:")
        print("1. Go to kick.com and log in")
        print("2. Open browser dev tools (F12)")
        print("3. Go to Network tab")
        print("4. Send a chat message")
        print("5. Look for a request to '/chat' and copy the Authorization header")
        print("6. The token is the part after 'Bearer '")
        sys.exit(1)
        
    channel_slug = sys.argv[1]
    
    # Try to get auth token from command line argument, then from .env file
    auth_token = None
    if len(sys.argv) > 2:
        auth_token = sys.argv[2]
        print("🔑 Using auth token from command line argument")
    elif KICK_AUTH_TOKEN:
        auth_token = KICK_AUTH_TOKEN
        print("🔑 Using auth token from .env file")
    
    if not auth_token:
        print("⚠️ No auth token found. Bot will translate messages but won't post them to chat.")
        print("Add KICK_AUTH_TOKEN to .env file or pass as argument to enable posting.")
        
    # Check if Azure Translator credentials are provided
    if not AZURE_TRANSLATOR_KEY:
        print("⚠️ Azure Translator key not found.")
        print("Please set AZURE_TRANSLATOR_KEY in your .env file.")
        print("\nTo get Azure Translator credentials:")
        print("1. Go to Azure Portal (portal.azure.com)")
        print("2. Create a Translator resource")
        print("3. Get the subscription key and endpoint from the resource")
        print("4. Add them to your .env file:")
        print("   AZURE_TRANSLATOR_KEY=your_subscription_key")
        print("   AZURE_TRANSLATOR_ENDPOINT=your_endpoint")
        print("   AZURE_TRANSLATOR_REGION=your_region")
        sys.exit(1)
        
    translator = KickChatTranslator(channel_slug, auth_token)
    translator.start()

if __name__ == "__main__":
    main() 