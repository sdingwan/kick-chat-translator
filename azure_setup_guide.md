# Azure Translator Setup Guide

## Why Switch to Azure Translator?

**Cost Comparison:**
- **Google Translate**: $20 per 1M characters (~500K free per month)
- **Azure Translator**: $10 per 1M characters (~2M free per month)

**Azure offers 4x more free translation and costs 50% less than Google!**

## Setting up Azure Translator

### 1. Create Azure Account
1. Go to [portal.azure.com](https://portal.azure.com)
2. Sign up for free (requires credit card but you won't be charged during free tier)

### 2. Create Translator Resource
1. In Azure Portal, click "Create a resource"
2. Search for "Translator" and select "Translator"
3. Click "Create"
4. Fill in the details:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create new or use existing
   - **Region**: Choose closest to you (e.g., East US, West Europe)
   - **Name**: Choose a unique name (e.g., "kick-chat-translator")
   - **Pricing Tier**: Choose "Free F0" for free tier or "Standard S1" for paid

### 3. Get Your Credentials
1. After creation, go to your Translator resource
2. In the left menu, click "Keys and Endpoint"
3. Copy the following:
   - **Key 1** (or Key 2) - this is your `AZURE_TRANSLATOR_KEY`
   - **Endpoint** - this is your `AZURE_TRANSLATOR_ENDPOINT`
   - **Location/Region** - this is your `AZURE_TRANSLATOR_REGION`

### 4. Update Your .env File
Create or update your `.env` file with these values:

```env
# Kick.com authentication token
KICK_AUTH_TOKEN=your_kick_auth_token_here

# Azure Translator API credentials
AZURE_TRANSLATOR_KEY=your_subscription_key_here
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=your_region_here

# Optional bot configuration
TARGET_LANGUAGE=en
MIN_MESSAGE_LENGTH=1
TRANSLATION_PREFIX=🌐 
RATE_LIMIT_DELAY=0
BOT_USERNAME=your_bot_username
BLACKLISTED_LANGUAGES=af,it,cy,sw,so,pl,ro,fr,no,sv,tl,de,es,id,et,sq,ca,fi,nl,da,vi,pt,hr,sl,hu,sk,lv
```

### 5. Install Dependencies
Remove old Google Cloud dependencies and install the updated ones:

```bash
pip install -r requirements.txt
```

### 6. Test Your Setup
Run the bot to make sure everything works:

```bash
python kick-chat-translator.py your_channel_name
```

## Pricing Details

### Free Tier (Perfect for most chat bots)
- **2 million characters per month** for free
- Roughly 40,000-80,000 chat messages per month
- No credit card charged until you exceed free tier

### Paid Tier (If you exceed free tier)
- **$10 per 1 million characters**
- 50% cheaper than Google Translate
- Pay only for what you use above the free tier

## Migration Benefits

✅ **4x larger free tier** (2M vs 500K characters)  
✅ **50% lower cost** ($10 vs $20 per 1M chars)  
✅ **No service account files** needed  
✅ **Simple API key authentication**  
✅ **Same translation quality**  
✅ **Faster API responses**  

## Security Notes

- Keep your `AZURE_TRANSLATOR_KEY` secret
- Don't commit your `.env` file to version control
- Regenerate keys if compromised (available in Azure Portal)
- Use environment variables in production deployments 