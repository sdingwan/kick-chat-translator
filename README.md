# 🤖 Kick Chat Translator Bot

A real-time chat translator bot for Kick.com that automatically detects non-English messages and translates them to English using Azure Translator API by default. Optionally, you can use Hugging Face models for self-hosted translation.

## ✨ Features

- **Real-time monitoring**: Connects to Kick chat via WebSocket
- **Language detection**: Automatically detects the language of incoming messages
- **Smart translation**: Only translates non-English messages above a minimum length
- **Rate limiting**: Prevents spam with configurable delays between translations
- **Flag emojis**: Shows country flags for detected languages
- **User mentions**: References the original message author in translations
- **Loop prevention**: Avoids translating its own messages
- **Multi-language support**: Supports 40+ languages (Azure) or 200+ (Hugging Face NLLB-200)
- **Configurable translation backend**: Use Azure or Hugging Face models

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your environment**:
   - Copy `env.example` to `.env` and fill in your credentials.
   - Or use the setup script (if available):
   ```bash
   python setup_env.py
   ```

3. **Run the bot**:
   ```bash
   python kick-chat-translator.py <channel_name>
   ```

## 📋 Requirements

- Python 3.7+
- Azure Translator API credentials (default)
- Optionally: Hugging Face Transformers for local/self-hosted translation
- Kick.com account (for posting translations)

## 🔧 Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Azure Translator Setup (Default)
**Azure offers 2M free chars/month and is cost-effective for most users.**

1. Go to [Azure Portal](https://portal.azure.com) and create a Translator resource
2. Get your subscription key, endpoint, and region
3. Add them to your `.env` file:
   ```
   AZURE_TRANSLATOR_KEY=your_subscription_key
   AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
   AZURE_TRANSLATOR_REGION=your_region
   ```

### 3. Hugging Face Model Setup (Alternative)
If you want to avoid cloud APIs or need more language coverage, you can use Hugging Face models locally:

- **Recommended for speed and coverage:**
  - [`facebook/nllb-200-distilled-600M`](https://huggingface.co/facebook/nllb-200-distilled-600M) (200 languages, fast, distilled)
  - [`Helsinki-NLP/opus-mt-xx-yy`](https://huggingface.co/Helsinki-NLP) (many language pairs, extremely fast)

**To use Hugging Face models:**
1. Install extra dependencies:
```bash
   pip install transformers torch sentencepiece
   ```
2. Update your `.env`:
   ```
   TRANSLATION_BACKEND=huggingface
   HF_MODEL_NAME=facebook/nllb-200-distilled-600M  # or your preferred model
   ```
3. (You will need to update the code to use Hugging Face if not already implemented.)

### 4. Configure Authentication Token

Create a `.env` file in the project directory:
```bash
KICK_AUTH_TOKEN=your_token_here
KICK_CHANNEL=your_channel_slug
# Azure Translator credentials
AZURE_TRANSLATOR_KEY=your_subscription_key
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=your_region
# Optional customization
TARGET_LANGUAGE=en
MIN_MESSAGE_LENGTH=1
RATE_LIMIT_DELAY=0
TRANSLATION_PREFIX=🌐
BOT_USERNAME=your_bot_username
BLACKLISTED_LANGUAGES=af,it,cy,sw,so,pl,ro,fr,no,sv,tl,de,es,id,et,sq,ca,fi,nl,da,vi,pt,hr,sl,hu,sk,lv,lt,cs
```

#### Getting Your Kick Auth Token

1. Go to [kick.com](https://kick.com) and log in
2. Open browser developer tools (F12)
3. Go to the Network tab
4. Send a chat message in any stream
5. Look for a POST request to `/messages/send/`
6. Copy the `Authorization` header value (the part after "Bearer ")

⚠️ **Keep your token secure and don't share it!**

## 🎯 Usage Examples

### View-Only Mode
```bash
python kick-chat-translator.py xqc
```

### Full Bot Mode (Post translations to chat)
```bash
python kick-chat-translator.py xqc <your_auth_token>
```

## 🛠️ Configuration

You can modify these settings in `kick-chat-translator.py` or via environment variables:

```python
TARGET_LANGUAGE = "en"           # Translate to English
MIN_MESSAGE_LENGTH = 1           # Allow very short messages
TRANSLATION_PREFIX = "🌐 "       # Prefix for translated messages
RATE_LIMIT_DELAY = 0             # No rate limiting by default
BOT_USERNAME = ""               # Your bot's username to avoid self-translation
BLACKLISTED_LANGUAGES = set(...)
```

## 📝 Example Output

```
🤖 Starting Kick Chat Translator for channel: xqc
📺 Channel: xQc (ID: 743)
💬 Chatroom ID: 743
🔗 Connection opened, waiting for handshake…
✅ Subscribed to chatrooms.743.v2
📡 Connecting to wss://ws-us2.pusher.com/app/32cbd69e4b950bf97679...
🌐 Translation enabled: Non-English → English

👤 user123 [es]: ¡Hola! ¿Cómo están todos?
✅ Translation sent: [by user123] Hello! How is everyone? (es > en)

👤 user456 [fr]: Cette stream est incroyable!
✅ Translation sent: [by user456] This stream is amazing! (fr > en)
```

## 🌍 Supported Languages

- **Azure Translator**: 40+ languages (see [official docs](https://learn.microsoft.com/en-us/azure/ai-services/translator/language-support))
- **Hugging Face NLLB-200**: 200 languages ([model card](https://huggingface.co/facebook/nllb-200-distilled-600M))
- **Helsinki-NLP/opus-mt**: 40+ per model (see [Helsinki-NLP hub](https://huggingface.co/Helsinki-NLP))

## ⚠️ Important Notes

- **Rate Limiting**: The bot can wait between translations to avoid spam (configurable)
- **Message Length**: Only messages with the configured minimum length are translated
- **Loop Prevention**: The bot won't translate its own messages
- **API Costs**: Azure Translator offers 2M free chars/month, then $10/1M chars
- **Terms of Service**: Make sure bot usage complies with Kick.com's ToS

## 🔍 Troubleshooting

### "Language detection error"
- The message might be too short or contain mostly emojis/symbols
- This is normal and doesn't affect other messages

### "Failed to send message"
- Check your auth token is correct and not expired
- Verify you have permission to send messages in the channel
- Make sure your account isn't rate-limited or banned

### "Azure Translator key not found"
- Make sure you've added AZURE_TRANSLATOR_KEY to your .env file
- Verify your Azure subscription key is correct
- Check that your Azure Translator resource is active

### "Model not supported or slow"
- If you need more languages or want to self-host, use Hugging Face models as described above
- For fastest translation, use Helsinki-NLP/opus-mt-xx-yy for specific pairs, or NLLB-200 for broad coverage

## 📄 License

This project is for educational purposes. Please respect Kick.com's Terms of Service and API usage guidelines.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the bot! 