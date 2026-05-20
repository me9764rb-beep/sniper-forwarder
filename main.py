import asyncio
import os
import time
import httpx
from pyrogram import Client, filters, idle
from pyrogram.types import Message

API_ID  = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION  = os.environ["SESSION_STRING"]
WEBHOOK  = os.environ["WEBHOOK_URL"]
SECRET   = os.environ["WEBHOOK_SECRET"]
SOURCE   = os.environ.get("SOURCE_CHANNEL", "@WalterBloomberg").lstrip('@').lower()

app = Client("sniper_forwarder", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

_last_message_ts: float = time.time()
_message_count: int = 0


@app.on_message(filters.channel)
async def forward_to_webhook(client: Client, message: Message):
    global _last_message_ts, _message_count

    if (message.chat.username or '').lower() != SOURCE:
        return

    text = message.text or message.caption
    if not text or len(text.strip()) < 5:
        return

    _last_message_ts = time.time()
    _message_count += 1
    print(f"[WB #{_message_count}] {text[:100]}")

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
            print(f"  ✓ Forwarded [{r.status_code}]: {text[:60]}")
            return
        except Exception as e:
            print(f"  ✗ Webhook attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)

    print(f"  ✗ All webhook attempts failed for message {message.id}")


async def heartbeat():
    """Logs a heartbeat every 10 minutes so Railway logs confirm the process is alive."""
    while True:
        await asyncio.sleep(600)
        idle_mins = int((time.time() - _last_message_ts) / 60)
        print(f"[HEARTBEAT] alive ✓ | forwarded: {_message_count} msgs | last WB message: {idle_mins}m ago")


async def main():
    print(f"[BOOT] Starting forwarder — source: @{SOURCE}")
    print(f"[BOOT] Webhook: {WEBHOOK[:60]}...")
    await app.start()

    me = await app.get_me()
    print(f"[BOOT] Logged in as: {me.first_name} (@{me.username}) ✓")

    # Join the source channel (required to receive updates + cache peer ID)
    try:
        await app.join_chat(SOURCE)
        print(f"[BOOT] Joined @{SOURCE} ✓")
    except Exception as e:
        print(f"[BOOT] join_chat: {e} (may already be a member)")

    # Verify channel is accessible
    try:
        chat = await app.get_chat(SOURCE)
        print(f"[BOOT] Source channel confirmed: {chat.title} ({chat.members_count} members) ✓")
    except Exception as e:
        print(f"[BOOT] FATAL — cannot access @{SOURCE}: {e}")
        raise

    asyncio.create_task(heartbeat())
    print("[BOOT] Listening for new messages...")
    await idle()
    await app.stop()


if __name__ == "__main__":
    app.run(main())
