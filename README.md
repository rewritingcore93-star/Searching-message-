# Searching-message-
A message of searching msti 
# Telegram Auto-Responder Userbot

A 24/7 Telegram userbot that automatically responds when you're mentioned or messaged.

## Features

- ✅ Messages from YOUR personal account (not a bot)
- ✅ 24/7 operation with auto-reconnect
- ✅ Rate limiting to prevent spam
- ✅ Whitelist/Blacklist support
- ✅ Multiple response triggers (DM, Mention, Reply)
- ✅ Health monitoring and auto-restart
- ✅ Railway deployment ready
- ✅ Logging and statistics

## Deployment on Railway

### Step 1: Fork/Clone the Repository

### Step 2: Get Telegram API Credentials
1. Go to https://my.telegram.org
2. Login with your phone number
3. Create an application
4. Note down API_ID and API_HASH

### Step 3: Deploy on Railway
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add environment variables (see `.env.example`)
5. Deploy!

### Step 4: Verify Code (First Run)
1. Check Railway logs
2. Enter verification code when prompted
3. Enter 2FA password if enabled

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | Yes | Your Telegram API ID |
| `API_HASH` | Yes | Your Telegram API Hash |
| `PHONE_NUMBER` | Yes | Your phone number with country code |
| `SESSION_NAME` | No | Session file name (default: my_account) |

## Response Triggers

Configure via `RESPOND_TO` (comma-separated):
- `dm`: Respond to direct messages
- `mention`: Respond when @username is mentioned
- `reply`: Respond when someone replies to your message

## Monitoring

Check Railway logs for:
- Bot startup/shutdown
- Messages processed
- Response counts
- Health check status

## Important Notes

⚠️ **WARNING**: Userbots may violate Telegram's ToS. Use responsibly!
- Don't use for spam
- Add rate limiting
- Monitor bot activity
- Respect Telegram's limits

## Support

For issues, check:
1. Railway logs for errors
2. Session file permissions
3. Environment variables
4. Telegram verification status
