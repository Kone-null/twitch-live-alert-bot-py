import os
import json
import time
import httpx
import asyncio
import logging
import traceback
from discord import SyncWebhook
from dotenv import load_dotenv
from typing import List


from twitch.channel import Channel

# Load environment variables
load_dotenv()

# Constants
CHANNEL_LIST_FILE: str = os.getenv("CHANNEL_LIST")
UPDATE_DELAY: float = float(os.getenv("UPDATE_DELAY_MIN", 1)) * 60  # Convert to seconds
DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL")
TWITCH_ROLE_ID: str = os.getenv("TWITCH_ROLE_ID")
SAVE_FILE: str = os.getenv("SAVE_FILE")

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # You can change this to DEBUG for more detailed logs

# Create handlers for logging to both the console and a file
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("twitch_bot.log")

# Set the log format
formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def log_error(e: Exception):
    """Logs detailed error information including function and line number."""
    exc_type, exc_value, exc_tb = e.__class__, e, e.__traceback__
    # Format the traceback into a readable string
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    # Log the error with the function name and line number
    logger.error("".join(tb_lines))


async def is_live(channel_name: str) -> bool:
    """Check if the Twitch channel is live."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://www.twitch.tv/{channel_name}")
            response.raise_for_status()

        return "isLiveBroadcast" in response.text

    except httpx.RequestError as exc:
        log_error(exc)  # Log error with function name and line
        logger.error(f"Request error for channel {channel_name}: {exc}")
        return False
    except httpx.HTTPStatusError as exc:
        log_error(exc)  # Log error with function name and line
        logger.error(
            f"HTTP error for channel {channel_name}: {exc.response.status_code}"
        )
        return False
    except Exception as exc:
        log_error(exc)  # Log error with function name and line
        logger.error(
            f"An unexpected error occurred while checking the status of {channel_name}: {exc}"
        )
        return False


def get_channels(filename: str) -> List[str]:
    """Read a list of streamers from a file."""
    try:
        with open(filename, "r") as f:
            streamers = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(streamers)} streamers from {filename}.")
            return streamers
    except FileNotFoundError as e:
        log_error(e)  # Log error with function name and line
        logger.error(f"Error: The file {filename} does not exist.")
        return []
    except Exception as e:
        log_error(e)  # Log error with function name and line
        logger.error(f"An unexpected error occurred while reading {filename}: {e}")
        return []


def send_webhook(channel_name: str, status: str) -> None:
    """Send a webhook notification to Discord."""
    try:
        webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
        webhook.send(f"<@&{TWITCH_ROLE_ID}> {channel_name} is {status}!")
        logger.info(f"Sent {status} status for {channel_name} to Discord.")
    except Exception as e:
        log_error(e)  # Log error with function name and line
        logger.error(f"Failed to send webhook for {channel_name}: {e}")


def countdown(seconds: float) -> None:
    """Sleep for the given number of seconds."""
    try:
        logger.info(f"Waiting for {seconds} seconds before the next update...")
        time.sleep(seconds)
    except Exception as e:
        log_error(e)  # Log error with function name and line
        logger.error(f"Error in countdown function: {e}")


def save_data(channels: List[Channel], save_json_file: str) -> None:
    """Save the current channel statuses to a JSON file."""
    try:
        with open(save_json_file, "w") as json_file:
            json.dump([channel.data() for channel in channels], json_file, indent=4)
        logger.info(f"Data saved successfully to {save_json_file}.")
    except Exception as e:
        log_error(e)  # Log error with function name and line
        logger.error(f"Error saving data to {save_json_file}: {e}")


def load_save_data(save_json_file: str) -> List[Channel]:
    """Load channel statuses from a JSON file."""
    try:
        with open(save_json_file, "r") as json_file:
            data = json.load(json_file)

        channels = [
            Channel(channel_data["name"], channel_data["live"]) for channel_data in data
        ]

        logger.info(f"Loaded {len(channels)} channels from {save_json_file}.")
        return channels
    except FileNotFoundError as e:
        # log_error(e)  # Log error with function name and line
        logger.warning(f"No previous data found, starting fresh.")
        return []  # If no previous save exists, return an empty list

    except json.JSONDecodeError as je:
        # log_error(je)
        logger.error(
            f"An unexpected error occurred while decoding {save_json_file}: {je}"
        )
        return []

    except Exception as e:
        log_error(e)  # Log error with function name and line
        logger.error(
            f"An unexpected error occurred while loading {save_json_file}: {e}"
        )
        return []


# def add_channel(channel_name: str, channels: List[Channel], save_json_file: str) -> None:
#     """Add a new channel to the list and save the updated list to the file."""
#     try:
#         if any(channel.name == channel_name for channel in channels):
#             logger.warning(f"Channel {channel_name} is already in the list.")
#             return

#         new_channel = Channel(channel_name)
#         channels.append(new_channel)
#         save_data(channels, save_json_file)
#         logger.info(f"Added new channel {channel_name} to the list.")
#     except Exception as e:
#         log_error(e)  # Log error with function name and line
#         logger.error(f"Error adding channel {channel_name}: {e}")


async def main():
    """Main function to monitor live Twitch channels."""
    try:
        channels = load_save_data(SAVE_FILE)

        if not channels:
            channels = [
                Channel(name=channel) for channel in get_channels(CHANNEL_LIST_FILE)
            ]

        while True:
            for channel in channels:

                if not channel:
                    continue

                is_channel_live = await is_live(channel.name)
                if is_channel_live and not channel.live:
                    logger.info(f"{channel.name} is live!")
                    channel.set_live()
                    send_webhook(channel.name, "live")
                elif not is_channel_live and channel.live:
                    logger.info(f"{channel.name} is offline!")
                    channel.set_offline()
                    send_webhook(channel.name, "offline")

            logger.info(f"Waiting for {UPDATE_DELAY} seconds before the next check...")
            countdown(UPDATE_DELAY)

            save_data(channels, SAVE_FILE)

    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Saving data and exiting...")
        save = input("save current data [Y/n]:")
        if not save:
            save_data(channels, SAVE_FILE)
        exit()
    except Exception as e:
        log_error(e)  # Log error with function name and line
        logger.critical(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    try:
        logger.info("Twitch Bot started.")
        asyncio.run(main())
    except Exception as e:
        log_error(e)  # Log error with function name and line
        logger.critical(f"Critical error during startup: {e}")
        exit()
