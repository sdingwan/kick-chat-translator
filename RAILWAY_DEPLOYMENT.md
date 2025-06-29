# Railway Deployment Guide

This guide will help you deploy your Kick Chat Translator bot to Railway for 24/7 operation.

## Prerequisites

1. **Azure Translator Account**: You need Azure Translator credentials
2. **Kick Auth Token**: You need your Kick authentication token
3. **Railway Account**: Sign up at [railway.app](https://railway.app)

## Step-by-Step Deployment

### 1. Prepare Your Code

Make sure your project has these files:
- `kick-chat-translator.py` (your main bot file)
- `requirements.txt` (Python dependencies)
- `Procfile` (tells Railway how to run your bot)
- `railway.toml` (Railway configuration)

### 2. Deploy to Railway

#### Option A: Deploy from GitHub (Recommended)

1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. **Connect to Railway**:
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will automatically detect it's a Python project

#### Option B: Deploy via Railway CLI

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and deploy**:
   ```bash
   railway login
   railway init
   railway up
   ```

### 3. Configure Environment Variables

In your Railway dashboard, go to your project and add these environment variables:

#### Required Variables:
```
KICK_CHANNEL=your_channel_name
KICK_AUTH_TOKEN=your_kick_auth_token
AZURE_TRANSLATOR_KEY=your_azure_key
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=your_azure_region
```

#### Optional Variables (with defaults):
```
TARGET_LANGUAGE=en
MIN_MESSAGE_LENGTH=1
TRANSLATION_PREFIX=🌐 
RATE_LIMIT_DELAY=0
BOT_USERNAME=your_bot_username
BLACKLISTED_LANGUAGES=af,it,cy,sw,so,pl,ro,fr,no,sv,tl,de,es,id,et,sq,ca,fi,nl,da,vi,pt,hr,sl,hu,sk,lv,lt,cs
```

### 4. How to Get Required Credentials

#### Get Your Kick Auth Token:
1. Go to [kick.com](https://kick.com) and log in
2. Open browser dev tools (F12)
3. Go to Network tab
4. Send a chat message in any channel
5. Look for a request to `/messages/send/`
6. Copy the `Authorization` header value
7. Remove the `Bearer ` prefix - that's your token

#### Get Azure Translator Credentials:
1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new "Translator" resource
3. Once created, go to "Keys and Endpoint"
4. Copy:
   - **Key**: One of the subscription keys
   - **Endpoint**: Usually `https://api.cognitive.microsofttranslator.com`
   - **Region**: The region you selected (e.g., `eastus`)

### 5. Monitor Your Bot

- **Logs**: Check Railway dashboard for real-time logs
- **Status**: Make sure the service is running (not crashed)
- **Usage**: Monitor your Azure Translator usage in Azure Portal

### 6. Cost Estimation

#### Railway Costs:
- **Free Tier**: 500 hours/month (~20 days of 24/7 operation)
- **Hobby Plan**: $5/month for unlimited usage

#### Azure Translator Costs:
- **Free Tier**: 2 million characters/month
- **Paid**: $10 per million characters after free tier

### 7. Troubleshooting

#### Bot Not Starting:
- Check environment variables are set correctly
- Verify your Kick auth token is valid
- Check Azure credentials are correct

#### Bot Not Translating:
- Check logs for error messages
- Verify the channel name is correct
- Make sure Azure Translator has quota remaining

#### WebSocket Disconnections:
- The bot has auto-reconnect built-in
- Check Railway logs for connection issues

### 8. Updating Your Bot

To update your bot:
1. Push changes to GitHub (if using GitHub deployment)
2. Railway will automatically redeploy
3. Or use `railway up` if using CLI

## Example Environment Variables

Here's what your Railway environment variables should look like:

```
KICK_CHANNEL=xqc
KICK_AUTH_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...
AZURE_TRANSLATOR_KEY=abc123def456...
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=eastus
TARGET_LANGUAGE=en
BOT_USERNAME=yourbotname
```

## Support

If you run into issues:
1. Check Railway logs first
2. Verify all environment variables are set
3. Test your Azure credentials locally
4. Make sure your Kick auth token hasn't expired

Your bot should now be running 24/7 on Railway! 🚀 