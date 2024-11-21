import os
import sys
import json
import time
import httpx
import asyncio
import logging
import traceback
from datetime import datetime, timedelta
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
CLIENT_ID: str = os.getenv("CLIENT_ID")
AUTH_KEY: str = os.getenv("AUTH_KEY")


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


def check_env_vars():
    # List of required environment variables
    required_vars = [
        "DISCORD_WEBHOOK_URL",
        "TWITCH_ROLE_ID",
        "CHANNEL_LIST",
        "UPDATE_DELAY_MIN",
        "SAVE_FILE",
        "AUTH_KEY",
        "CLIENT_ID",
    ]

    # Check for missing environment variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    # If any environment variables are missing, print them and exit
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        sys.exit(1)


check_env_vars()


def log_error(e: Exception):
    """Logs detailed error information including function and line number."""
    exc_type, exc_value, exc_tb = e.__class__, e, e.__traceback__
    # Format the traceback into a readable string
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    # Log the error with the function name and line number
    logger.error("".join(tb_lines))


def save_file_with_auto_dirs(channelname, content, status):
    try:
        # Extract the directory path
        # Get the current time
        now = datetime.now()

        formatted_time = now.strftime("%Y.%m.%dT%H.%M.%S")

        outfile = f"{channelname}[{formatted_time}]({status}).json"
        file_path = os.path.join("troubleshooting", "status-responses" ,channelname, outfile)
        dir_path = os.path.dirname(file_path)

        # Create the directories if they don't exist
        os.makedirs(dir_path, exist_ok=True)

        # Write the content to the file
        # with open(file_path, "w") as file:
        #     file.write(content)
        # Write the content to the file
        with open(file_path, "w") as file:
            json.dump(content, file, indent=4)  # `content` must be a dictionary or list

    except OSError as e:
        logging.error(f"OS error occurred while saving the file: {e}")
        # print(f"Failed to save the file: {e}")

    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
        # print(f"An unexpected error occurred: {e}")


async def is_live(channel_name: str) -> bool:
    """Check if the Twitch channel is live."""
    try:
        async with httpx.AsyncClient() as client:
            # response = await client.get(f"https://www.twitch.tv/{channel_name}")

            headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {AUTH_KEY}"}

            url = f"https://api.twitch.tv/helix/search/channels?query={channel_name}"
            response = await client.get(url=url, headers=headers)
            response.raise_for_status()

            # Parse the JSON response
            data = response.json().get("data", [])

            # Search for the channel in the response data
            for channel in data:
                if channel.get("broadcaster_login", "").lower() == channel_name.lower():
                    is_live = channel.get("is_live", None)
                    
                    if is_live is None:
                        
                        save_file_with_auto_dirs(
                            channelname=channel_name, 
                            content=channel, 
                            status="null"
                        )
                    return is_live
        return None
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
        detect_time = int(time.time())
        webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL)

        live_message = f"<@&{TWITCH_ROLE_ID}> <t:{detect_time}:F> <t:{detect_time}:R> - [{channel_name}]({'https://www.twitch.tv/'+channel_name}) is {status}!"

        # live_message = f"<@&{TWITCH_ROLE_ID}> <t:{detect_time}> <t:{detect_time}:R> - {channel_name} is {status}!"

        offline_message = f"<@&{TWITCH_ROLE_ID}> <t:{detect_time}> <t:{detect_time}:R> - {channel_name} is {status}!"

        message = live_message if status == "live" else offline_message
        webhook.send(message)

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

def update_time():
    """
    Checks if the current time is at an interval of 5 minutes.
    Logs the next update time.
    
    Returns:
        bool: True if the current minute is divisible by the interval, otherwise False.
    """
    minute_interval: int = 5

    # Get the current time
    now = datetime.now()

    # Calculate the next update time
    update_time = now + timedelta(minutes=minute_interval)
    
    # Extract the current minute
    minute_now = now.minute

    # Format the next update time for logging
    formatted_time = update_time.strftime("%Y-%m-%dT%H:%M:%S")

    # Log the next update time
    logger.info(f"Waiting for next update @ {formatted_time}")

    # Check if the current minute is divisible by the interval
    if (minute_now % minute_interval) == 0:
        return True
    return False



def save_data(channels: List[Channel], save_json_file: str) -> None:
    """Save the current channel statuses to a JSON file."""
    try:
        # data = {
        #     "meta": {"saved": time.time()},
        #     "channels": [channel.data() for channel in channels],
        # }
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
    
                if is_channel_live is None:
                    logger.info(f"{channel.name}'s channel status not found!")
                    continue

                if is_channel_live and not channel.live: # channel is live
                    logger.info(f"{channel.name} is now live!")
                    channel.set_live()
                    send_webhook(channel.name, "live")
                elif is_channel_live and channel.live: # Channel is already live
                    logger.info(f"{channel.name} is live.")

                elif not is_channel_live and channel.live: # channel becomes offline
                    logger.info(f"{channel.name} is now offline!")
                    channel.set_offline()
                    send_webhook(channel.name, "offline")

                elif not is_channel_live and not channel.live: # channel was already off
                    logger.info(f"{channel.name} is offline.")


            save_data(channels, SAVE_FILE)
            logger.info(f"Waiting for {UPDATE_DELAY} seconds before the next check...")
            countdown(UPDATE_DELAY)

            

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
