import os
import json
import sys
import httpx
from typing import List
from twitch.channel import Channel
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CHANNEL_LIST_FILE: str = os.getenv("CHANNEL_LIST")
SAVE_FILE: str = os.getenv("SAVE_FILE")


def is_live(channel_name: str) -> bool:
    """Check if the Twitch channel is live."""
    try:
        response = httpx.get(f"https://www.twitch.tv/{channel_name}")
        response.raise_for_status()
        return "isLiveBroadcast" in response.text
    except httpx.RequestError as exc:
        print(f"Request error for channel {channel_name}: {exc}")
    except httpx.HTTPStatusError as exc:
        print(f"HTTP error for channel {channel_name}: {exc.response.status_code}")
    except Exception as exc:
        print(f"Unexpected error while checking {channel_name}: {exc}")
    return False


def load_save_data(save_json_file: str) -> List[Channel]:
    """Load channel statuses from a JSON file."""
    try:
        with open(save_json_file, "r") as json_file:
            data = json.load(json_file)
        channels = [
            Channel(channel_data["name"], channel_data["live"]) for channel_data in data
        ]
        print(f"Loaded {len(channels)} channels from {save_json_file}.")
        return channels
    except FileNotFoundError:
        print(f"No previous data found, starting fresh.")
    except json.JSONDecodeError as je:
        print(f"Error decoding JSON in {save_json_file}: {je}")
    except Exception as e:
        print(f"Error loading {save_json_file}: {e}")
    return []  # Return empty list if anything goes wrong


def save_channels(channels: List[Channel], save_json_file: str) -> None:
    """Save the list of channels to a JSON file."""
    try:
        with open(save_json_file, "w") as json_file:
            json.dump([channel.data() for channel in channels], json_file, indent=4)
        print(f"Data saved successfully to {save_json_file}.")
    except Exception as e:
        print(f"Error saving data to {save_json_file}: {e}")


def add_channel(channel_name: str, channels: List[Channel], save_json_file: str) -> None:
    """Add a new channel to the list and save the updated list to the file."""
    if any(channel.name == channel_name for channel in channels):
        print(f"Channel {channel_name} is already in the list.")
        return

    new_channel = Channel(name=channel_name, live=is_live(channel_name))
    channels.append(new_channel)
    save_channels(channels, save_json_file)
    print(f"Added new channel {channel_name}.")


def add_many_channels(channel_names: List[str], channels: List[Channel], save_json_file: str) -> None:
    """Add many new channels to the list and save the updated list to the file."""
    for channel_name in channel_names:
        if any(channel.name == channel_name for channel in channels):
            print(f"Channel {channel_name} is already in the list.")
            continue
        new_channel = Channel(name=channel_name, live=is_live(channel_name))
        channels.append(new_channel)
    
    save_channels(channels, save_json_file)
    print(f"Added new channels to the list.")


# Create the parser
parser = argparse.ArgumentParser(description="Add a channel name to Twitch alert database")

# Add --file argument to specify a file to read from
parser.add_argument("--file", type=str, help="Path to a file to read channel names to add")
# Positional argument for a single channel
parser.add_argument("--channel", type=str, help="Name of channel (not URL)")

# Parse the arguments
args = parser.parse_args()

# Initialize channels from save file
channels = load_save_data(SAVE_FILE)

# Handle single channel addition
if args.channel:
    add_channel(channel_name=args.channel, channels=channels, save_json_file=SAVE_FILE)

# Handle file-based addition of channels
if args.file:
    try:
        with open(args.file, 'r') as file:
            channel_names = [line.strip() for line in file.readlines() if line.strip()]
            add_many_channels(channel_names=channel_names, channels=channels, save_json_file=SAVE_FILE)
    except FileNotFoundError:
        print(f"Error: The file {args.file} was not found.")
    except Exception as e:
        print(f"Error reading file {args.file}: {str(e)}")

