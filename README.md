# 🤖 Kick Chat Translator Bot

A real-time chat translator bot for Kick.com that automatically detects non-English messages and translates them to English using Azure Translator API.

## ✨ Features

- **Real-time monitoring**: Connects to Kick chat via WebSocket
- **Language detection**: Automatically detects the language of incoming messages
- **Smart translation**: Only translates non-English messages above a minimum length
- **Rate limiting**: Prevents spam with configurable delays between translations
- **Flag emojis**: Shows country flags for detected languages
- **User mentions**: References the original message author in translations
- **Loop prevention**: Avoids translating its own messages
- **Fast & Efficient**: Uses persistent HTTP sessions and parallel processing
- **Auto-reconnect**: Handles WebSocket disconnections gracefully
- **Cloud Ready**: Deploy to Railway, Google Cloud Run, or other platforms
- **Cost Effective**: Uses Azure Translator (2M free chars/month, then 50% cheaper than Google)

## 🚀 Quick Start

1. **Setup the bot**:
   ```bash
   python setup.py
   ```

2. **Configure your auth token**:
   ```bash
   python setup_env.py
   ```

3. **Run the bot**:
   ```bash
   python kick-chat-translator.py <channel_name>
   ```

## 📋 Requirements

- Python 3.7+
- Azure Translator API credentials
- Kick.com account (for posting translations)

## 🔧 Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Azure Translator Setup
**🎉 Azure offers 4x more free translation (2M chars/month) and costs 50% less than Google!**

See the detailed setup guide in `azure_setup_guide.md`, or quick setup:

1. Go to [Azure Portal](https://portal.azure.com) and create a free account
2. Create a "Translator" resource 
3. Get your subscription key, endpoint, and region
4. Add them to your `.env` file

### 3. Configure Authentication Token

The easiest way to set up your auth token is using the setup script:

```bash
python setup_env.py
```

This will guide you through creating a `.env` file with your token.

#### Manual .env Setup
Create a `.env` file in the project directory:
```bash
# .env file
KICK_AUTH_TOKEN=your_token_here

# Azure Translator credentials
AZURE_TRANSLATOR_KEY=your_subscription_key
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=your_region

# Optional customization
TARGET_LANGUAGE=en
MIN_MESSAGE_LENGTH=3
RATE_LIMIT_DELAY=2
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
# Monitor XQC's chat and display translations
python kick-chat-translator.py xqc

# Monitor any channel
python kick-chat-translator.py trainwreckstv
```

### Full Bot Mode
```bash
# Post translations to chat
python kick-chat-translator.py xqc eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 🛠️ Configuration

You can modify these settings in `kick-chat-translator.py`:

```python
TARGET_LANGUAGE = "en"           # Translate to English
MIN_MESSAGE_LENGTH = 3           # Don't translate very short messages
TRANSLATION_PREFIX = "🌐 "       # Prefix for translated messages
RATE_LIMIT_DELAY = 2             # Seconds between translations
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
✅ Translation sent: 🌐 🇪🇸 @user123: Hello! How is everyone?

👤 user456 [fr]: Cette stream est incroyable!
✅ Translation sent: 🌐 🇫🇷 @user456: This stream is amazing!
```

## 🌍 Supported Languages

The bot automatically detects and translates from many languages including:
- Spanish (🇪🇸), French (🇫🇷), German (🇩🇪), Italian (🇮🇹)
- Portuguese (🇵🇹), Russian (🇷🇺), Japanese (🇯🇵), Korean (🇰🇷)
- Chinese (🇨🇳), Arabic (🇸🇦), Hindi (🇮🇳), Turkish (🇹🇷)
- And many more...

## ⚠️ Important Notes

- **Rate Limiting**: The bot waits 2 seconds between translations to avoid spam
- **Message Length**: Only messages with 3+ characters are translated
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

## 📄 License

This project is for educational purposes. Please respect Kick.com's Terms of Service and API usage guidelines.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the bot!

## 🚀 Deploy to Railway (Recommended)

Railway is the easiest and cheapest way to deploy your bot 24/7.

### Step 1: Prepare Your Code
1. Make sure all your code is pushed to a GitHub repository
2. Your project should have these files (already included):
   - `requirements.txt`
   - `Procfile`
   - `railway.toml`

### Step 2: Deploy to Railway
1. Go to [Railway.app](https://railway.app/) and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will automatically detect it's a Python project

### Step 3: Set Environment Variables
In your Railway dashboard, go to Variables tab and add:

```
KICK_CHANNEL=your_channel_name
KICK_AUTH_TOKEN=your_kick_token_here
AZURE_TRANSLATOR_KEY=your_azure_key_here
AZURE_TRANSLATOR_ENDPOINT=your_azure_endpoint_here
AZURE_TRANSLATOR_REGION=your_azure_region_here
```

### Step 4: Deploy
- Railway will automatically build and deploy your bot
- Check the logs to make sure it's working
- Your bot will run 24/7!

### Railway Pricing
- **Free**: 500 hours/month (~20 days if running 24/7)
- **Pro**: $5/month for unlimited usage
- Perfect for small bots like this!

## Configuration

You can customize the bot behavior with these environment variables:

```bash
# Required
KICK_CHANNEL=your_channel_name
KICK_AUTH_TOKEN=your_kick_token
AZURE_TRANSLATOR_KEY=your_azure_key
AZURE_TRANSLATOR_ENDPOINT=your_azure_endpoint
AZURE_TRANSLATOR_REGION=your_azure_region

# Optional
TARGET_LANGUAGE=en                    # Language to translate to
MIN_MESSAGE_LENGTH=1                  # Minimum message length to translate
TRANSLATION_PREFIX=🌐                # Prefix for translated messages
BOT_USERNAME=your_bot_username        # Your bot's username (to avoid self-translation)
BLACKLISTED_LANGUAGES=af,it,cy,sw,so,pl,ro,fr,no,sv,tl,de,es,id,et,sq,ca,fi,nl,da,vi,pt,hr,sl,hu,sk,lv,lt,cs
```

## Other Deployment Options

### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT/kick-translator
gcloud run deploy --image gcr.io/YOUR_PROJECT/kick-translator --set-env-vars KICK_CHANNEL=your_channel,...
```

### Docker
```bash
# Build
docker build -t kick-translator .

# Run
docker run -e KICK_CHANNEL=your_channel -e KICK_AUTH_TOKEN=... kick-translator
```

## How It Works

1. **Connects** to Kick's WebSocket API to listen for chat messages
2. **Detects** the language of each message using langdetect
3. **Filters** out English messages, emotes, and short messages
4. **Translates** non-English messages using Azure Translator API
5. **Posts** the translation back to chat with format: `🌐 [by username] translated message (source > target)`

## Cost Estimation

Azure Translator pricing:
- **Free tier**: 2M characters/month
- **Paid**: $10 per 1M characters
- A typical message is ~50 characters
- Free tier = ~40,000 translated messages/month
- Very cost-effective for small to medium channels!

## Troubleshooting

### Bot not translating messages
- Check your Azure Translator credentials
- Verify your Kick auth token is valid
- Check the logs for error messages

### WebSocket disconnections
- The bot has auto-reconnect built-in
- Check your internet connection
- Railway/cloud platforms handle this automatically

### Translation accuracy
- Very short messages may not translate well
- Emotes and usernames are automatically filtered out
- The bot learns common English words to avoid false positives

## Support

If you run into issues:
1. Check the Railway logs in your dashboard
2. Verify all environment variables are set correctly
3. Make sure your Azure Translator resource is active
4. Test your Kick auth token by sending a manual chat message

Happy translating! 🌐 