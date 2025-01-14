import os
import sys
import json
import time
import httpx
import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks
from discord import SyncWebhook
from dotenv import load_dotenv
from typing import List
from twitch.channel import Channel
import colorlog
import threading

# Load environment variables
load_dotenv()

# Constants
CHANNEL_LIST_FILE: str = os.getenv("CHANNEL_LIST")
UPDATE_DELAY: float = float(os.getenv("UPDATE_DELAY_MIN", 1)) * 60  # Convert to seconds
DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL")
TWITCH_ROLE_ID: str = os.getenv("TWITCH_ROLE_ID")
SAVE_FILE: str = os.getenv("SAVE_FILE")
CLIENT_ID: str = os.getenv("CLIENT_ID")
AUTH_KEY: str = os.getenv("AUTH_KEY")

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = colorlog.StreamHandler()
file_handler = logging.FileHandler("twitch_bot.log")

formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s [%(levelname)s] - %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
        'DISCORD': 'blue',  # Custom log level for Discord messages
    }
)

console_handler.setFormatter(formatter)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s"))

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Add custom log level for Discord messages
DISCORD_LOG_LEVEL = 25  # Custom log level between INFO (20) and WARNING (30)
logging.addLevelName(DISCORD_LOG_LEVEL, "DISCORD")

def discord_log(self, message, *args, **kws):
    if self.isEnabledFor(DISCORD_LOG_LEVEL):
        self._log(DISCORD_LOG_LEVEL, message, args, **kws)

logging.Logger.discord = discord_log

def check_env_vars():
    required_vars = [
        "DISCORD_WEBHOOK_URL", "TWITCH_ROLE_ID", "CHANNEL_LIST",
        "UPDATE_DELAY_MIN", "SAVE_FILE", "AUTH_KEY", "CLIENT_ID"
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

check_env_vars()

def log_error(e: Exception):
    exc_type, exc_value, exc_tb = e.__class__, e, e.__traceback__
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    logger.error("".join(tb_lines))

def save_file_with_auto_dirs(channelname, content, status):
    try:
        now = datetime.now()
        formatted_time = now.strftime("%Y.%m.%dT%H.%M.%S")
        outfile = f"{channelname}[{formatted_time}]({status}).json"
        file_path = os.path.join("troubleshooting", "status-responses", channelname, outfile)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            json.dump(content, file, indent=4)
    except OSError as e:
        logger.error(f"OS error occurred while saving the file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")

async def is_live(channel_name: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {AUTH_KEY}"}
            url = f"https://api.twitch.tv/helix/search/channels?query={channel_name}"
            for attempt in range(3):
                try:
                    response = await client.get(url=url, headers=headers, timeout=10.0)
                    response.raise_for_status()
                    break
                except (httpx.ConnectError, httpx.ReadTimeout) as exc:
                    logger.warning(f"Attempt {attempt + 1}: Connection issue: {exc}")
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        raise
            data = response.json().get("data", [])
            for channel in data:
                if channel.get("broadcaster_login", "").lower() == channel_name.lower():
                    is_live = channel.get("is_live", None)
                    if is_live is None:
                        save_file_with_auto_dirs(channelname=channel_name, content=channel, status="null")
                    return is_live
        return False
    except httpx.RequestError as exc:
        logger.error(f"Request error for channel '{channel_name}': {exc}")
        return False
    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTP status error for channel '{channel_name}': {exc.response.status_code}, {exc.response.text}")
        return False
    except Exception as exc:
        logger.error(f"Unexpected error while checking the status of '{channel_name}': {exc}")
        return False

def get_channels(filename: str) -> List[str]:
    try:
        with open(filename, "r") as f:
            streamers = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(streamers)} streamers from {filename}.")
            return streamers
    except FileNotFoundError as e:
        log_error(e)
        logger.error(f"Error: The file {filename} does not exist.")
        return []
    except Exception as e:
        log_error(e)
        logger.error(f"An unexpected error occurred while reading {filename}: {e}")
        return []

def send_webhook(channel_name: str, status: str) -> None:
    try:
        detect_time = int(time.time())
        webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
        message = f"<@&{TWITCH_ROLE_ID}> <t:{detect_time}:F> <t:{detect_time}:R> - [{channel_name}]({'https://www.twitch.tv/'+channel_name}) is {status}!"
        webhook.send(message)
        logger.discord(f"Sent {status} status for {channel_name} to Discord.")
    except Exception as e:
        log_error(e)
        logger.error(f"Failed to send webhook for {channel_name}: {e}")

def save_data(channels: List[Channel], save_json_file: str) -> None:
    try:
        with open(save_json_file, "w") as json_file:
            json.dump([channel.data() for channel in channels], json_file, indent=4)
        logger.info(f"Data saved successfully to {save_json_file}.")
    except Exception as e:
        log_error(e)
        logger.error(f"Error saving data to {save_json_file}: {e}")

def load_save_data(save_json_file: str) -> List[Channel]:
    try:
        with open(save_json_file, "r") as json_file:
            data = json.load(json_file)
        channels = [Channel(channel_data["name"], channel_data["live"]) for channel_data in data]
        logger.info(f"Loaded {len(channels)} channels from {save_json_file}.")
        return channels
    except FileNotFoundError:
        logger.warning(f"No previous data found, starting fresh.")
        return []
    except json.JSONDecodeError as je:
        logger.error(f"An unexpected error occurred while decoding {save_json_file}: {je}")
        return []
    except Exception as e:
        log_error(e)
        logger.error(f"An unexpected error occurred while loading {save_json_file}: {e}")
        return []

async def monitor_channels():
    global channels
    channels = load_save_data(SAVE_FILE)
    if not channels:
        channels = [Channel(name=channel) for channel in get_channels(CHANNEL_LIST_FILE)]
    while True:
        for channel in channels:
            if not channel:
                continue
            is_channel_live = await is_live(channel.name)
            if is_channel_live is None:
                logger.info(f"{channel.name}'s channel status not found!")
                continue
            if is_channel_live and not channel.live:
                logger.info(f"{channel.name} is now live!")
                channel.set_live()
                send_webhook(channel.name, "live")
            elif is_channel_live and channel.live:
                logger.info(f"{channel.name} is live.")
            elif not is_channel_live and channel.live:
                logger.info(f"{channel.name} is now offline!")
                channel.set_offline()
                send_webhook(channel.name, "offline")
            elif not is_channel_live and not channel.live:
                logger.info(f"{channel.name} is offline.")
        save_data(channels, SAVE_FILE)
        logger.info(f"Waiting for {UPDATE_DELAY} seconds before the next check...")
        await asyncio.sleep(UPDATE_DELAY)

def prompt_save_data():
    save = input("Do you want to save the current states of each channel to save_data.json? [Y/n]: ").strip().lower()
    if save in ['y', 'yes', '']:
        save_data(channels, SAVE_FILE)
        logger.info("Data saved successfully on shutdown.")
    else:
        logger.info("Data not saved on shutdown.")

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_channels())

@app.on_event("shutdown")
async def shutdown_event():
    thread = threading.Thread(target=prompt_save_data)
    thread.start()
    thread.join()

@app.get("/")
async def read_root():
    return {"message": "Twitch Bot is running"}

@app.get("/channels")
async def get_channels_status():
    channels = load_save_data(SAVE_FILE)
    return {"channels": [channel.data() for channel in channels]}

@app.post("/webhook")
async def trigger_webhook(channel_name: str, status: str):
    send_webhook(channel_name, status)
    return {"message": f"Webhook sent for {channel_name} with status {status}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)