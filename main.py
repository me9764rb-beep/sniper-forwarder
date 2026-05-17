import asyncio
import os
import httpx
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID    = int(os.environ["TELEGRAM_API_ID"])
API_HASH  = os.environ["TELEGRAM_API_HASH"]
WEBHOOK   = os.environ["WEBHOOK_URL"]
SECRET    = os.environ["WEBHOOK_SECRET"]
SOURCE    = os.environ.get("SOURCE_CHANNEL", "@WalterBloomberg")

app = Client("sniper_forwarder", api_id=API_ID, api_hash=API_HASH)

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

    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(
            WEBHOOK,
            json=payload,
            headers={"x-telegram-bot-api-secret-token": SECRET},
        )
    print(f"Forwarded: {text[:60]}...")

if __name__ == "__main__":
    print(f"Listening to {SOURCE}...")
    app.run()
