import asyncio
import os
import httpx
from pyrogram import Client, filters, idle
from pyrogram.types import Message

API_ID    = int(os.environ["TELEGRAM_API_ID"])
API_HASH  = os.environ["TELEGRAM_API_HASH"]
SESSION   = os.environ["SESSION_STRING"]
WEBHOOK   = os.environ["WEBHOOK_URL"]
SECRET    = os.environ["WEBHOOK_SECRET"]
SOURCE    = os.environ.get("SOURCE_CHANNEL", "@WalterBloomberg")

app = Client("sniper_forwarder", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

@app.on_message(filters.channel & filters.chat(SOURCE))
async def forward_to_webhook(client: Client, message: Message):
    text = message.text or message.caption
    if not text or len(text.strip()) < 5:
        return

    payload = {
        "channel_post": {
            "message_id": message.id,
            "text": text,
            "chat": {"id": message.chat.id, "type": "channel"},
            "date": int(message.date.timestamp()),
        }
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=15) as http:
                r = await http.post(
                    WEBHOOK,
                    json=payload,
                    headers={"x-telegram-bot-api-secret-token": SECRET},
                )
            print(f"Forwarded [{r.status_code}]: {text[:80]}...")
            return
        except Exception as e:
            print(f"Webhook attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)

    print(f"All webhook attempts failed for message {message.id}")


async def main():
    print(f"Starting forwarder — listening to {SOURCE}")
    await app.start()
    print("Connected to Telegram ✓")
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
