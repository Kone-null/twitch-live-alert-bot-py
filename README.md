# Twitch Live Alert Bot

The **Twitch Live Alert Bot** is a Discord Webhook bot that periodically checks the live status of Twitch channel(s). It sends an alert to Discord when a channel goes live. Additionally, if a previously live channel is detected as offline, an update message is sent to inform the user that the channel is now offline.

Developed using Python 3.12.
Can run on Python 3.9.

## Setup

1. Clone the repository:
   ```bash
   git clone <repo-url>
   ```
2. Navigate into the project directory:
   ```bash
   cd twitch-live-alert-bot-py
   ```
3. Create a virtual environment:
   ```bash
   python -m venv .
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Fill out `channels.txt` with a list of Twitch channel names (not URLs/links).
6. OPTIONAL: Run the following command to add channels from a file:
   ```bash
   python add-channel.py --file channels.txt
   ```

## Configuration

Create a `.env` file with the following configuration:

```
DISCORD_WEBHOOK_URL=""
TWITCH_ROLE_ID=""
CHANNEL_LIST="channels.txt"
UPDATE_DELAY_MIN=
SAVE_FILE="save_data.json"
```

### Configuration Options:
- **DISCORD_WEBHOOK_URL**: The URL of the Discord webhook to send alerts to. You can create a webhook by following this [guide](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).
- **TWITCH_ROLE_ID**: The Discord role ID to mention in the alert. You can get the role ID by following this [guide](https://readybot.io/help/how-to/find-discord-user-and-role-ids).
- **CHANNEL_LIST**: The path to the text file that contains the list of Twitch channel names (not URLs).
- **UPDATE_DELAY_MIN**: The amount of time (in minutes) between each check for channel status.
- **SAVE_FILE**: The JSON file where the bot stores data, e.g., `{ 'name': 'twitch', 'live': false }`.

## Add or Follow Channels

- To see usage instructions, run:
  ```bash
  python add-channel.py --help
  ```

- To add a single channel:
  ```bash
  python add-channel.py --channel <channel_name>
  ```

- To add multiple channels from a file:
  ```bash
  python add-channel.py --file <path/to/list/of/channels.txt>
  ```

## Running the Bot

To start the bot, run:

```bash
python bot.py
```
