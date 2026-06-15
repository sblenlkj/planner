source .env

curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://outlast-alongside-professed.ngrok-free.dev/telegram/webhook\",
    \"secret_token\": \"${TELEGRAM_WEBHOOK_SECRET}\"
  }"