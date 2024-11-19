# Twitch Live Alert Bot

The **Twitch Live Alert Bot** is a Discord webhook bot that periodically checks the live status of specified Twitch channels. It sends an alert to a Discord channel when a Twitch channel goes live. Additionally, if a previously live channel is detected as offline, it sends an update message to notify users.

This bot is a personal project created to address the limitations of existing free Twitch live alert Discord bots.

Developed using Python 3.12.

---

## How It Works

This bot does not use the Twitch API. Instead, it performs a GET request to the channel's page at `https://www.twitch.tv/[channel_name]`. The response (HTML) contains a boolean field, `isLiveBroadcast`. If this field is present in the HTML response, the bot considers the channel to be live. If the field is absent, the channel is considered offline.

---

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   ```
2. **Navigate to the project directory**:
   ```bash
   cd twitch-live-alert-bot-py
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv .
   ```
4. **Activate the virtual environment**:
   - On Windows:
     ```bash
     .\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source ./bin/activate
     ```
5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
6. **Add Twitch channels**:
   - Populate `channels.txt` with the list of Twitch channel names (one name per line, no URLs).
   - *Optional*: Use the following command to add channels from a file:
     ```bash
     python add-channel.py --file channels.txt
     ```

---

## Configuration

Create a `.env` file in the project root with the following structure:

```
DISCORD_WEBHOOK_URL=""
TWITCH_ROLE_ID=""
CHANNEL_LIST="channels.txt"
UPDATE_DELAY_MIN=
SAVE_FILE="save_data.json"
```

### Configuration Options:
- **DISCORD_WEBHOOK_URL**: The Discord webhook URL to send alerts. Learn how to create a webhook [here](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).
- **TWITCH_ROLE_ID**: The Discord role ID to mention in alerts. Follow this [guide](https://readybot.io/help/how-to/find-discord-user-and-role-ids) to find the role ID.
- **CHANNEL_LIST**: The path to the text file containing the list of Twitch channel names (one name per line, no URLs).
- **UPDATE_DELAY_MIN**: The interval (in minutes) between each check for channel status.
- **SAVE_FILE**: The JSON file where the bot stores its state, e.g., `{ "name": "twitch", "live": false }`.

---

## Managing Channels

- **View usage instructions**:
  ```bash
  python add-channel.py --help
  ```

- **Add a single channel**:
  ```bash
  python add-channel.py --channel <channel_name>
  ```

- **Add multiple channels from a file**:
  ```bash
  python add-channel.py --file <path/to/channels.txt>
  ```

---

## Running the Bot

To start the bot, run the following command:

```bash
python bot.py
```
