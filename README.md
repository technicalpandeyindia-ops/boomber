# OTP BOMBER BOT — Telegram + Render

## Files
- `bomber.py` — core engine (SMS / WA / CALL APIs)
- `bot.py`    — Telegram bot
- `requirements.txt`
- `render.yaml`
- `Procfile`

## Deploy on Render

1. Push this folder to GitHub
2. Go to render.com → New → Background Worker
3. Connect your repo
4. Set env vars:
   - `BOT_TOKEN`  = your Telegram bot token (from @BotFather)
   - `OWNER_ID`   = your Telegram user ID (optional, locks bot to you)
5. Deploy

## Bot Commands

| Command  | Action                        |
|----------|-------------------------------|
| /bomb    | Start a bomb session          |
| /stop    | Stop running session          |
| /status  | Check if session active       |
| /help    | Show commands                 |

## CALL APIs — Add Your Keys

Open `bomber.py` and replace:

| Placeholder              | Get from          |
|--------------------------|-------------------|
| YOUR_MSG91_AUTHKEY       | msg91.com         |
| YOUR_MSG91_TEMPLATE_ID   | msg91.com         |
| YOUR_FAST2SMS_API_KEY    | fast2sms.com      |
| YOUR_ACCOUNT_SID         | twilio.com        |
| YOUR_BASE64_CREDENTIALS  | twilio.com        |
| YOUR_TWILIO_NUMBER       | twilio.com        |
| YOUR_SID (Exotel)        | exotel.com        |
| YOUR_EXOTEL_BASE64       | exotel.com        |
