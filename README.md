# Twitch Live Alert Bot

The **Twitch Live Alert Bot** is a Discord webhook bot that periodically checks the live status of specified Twitch channels. When a channel goes live, the bot sends an alert to Discord. Additionally, if a channel that was live goes offline, the bot sends an update message to notify the users.

This project was developed as a personal solution to overcome the limitations of free Twitch live alert Discord bots.


Developed using Python 3.12.

---

## How It Works

This bot & server equivalent uses the Twitch API. Instead, it checks a channel's live status by sending a GET request to the `https://api.twitch.tv/helix/search` API endpoint. The response HTML includes a boolean value `is_live`, which determines the live status of the channel.

---

## Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone <repo-url>
   ```

2. **Navigate to the Project Directory:**
   ```bash
   cd twitch-live-alert-bot-py
   ```

3. **Create a Virtual Environment:**
   ```bash
   python -m venv .
   ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Add Twitch Channels:**
   Fill the `channels.txt` file with a list of Twitch channel names (one per line, without URLs).

6. **Optional: Bulk Add Channels from a File:**
   ```bash
   python add-channel.py --file channels.txt
   ```

---

## Configuration

Create a `.env` file in the project directory with the following configurations:

```
DISCORD_WEBHOOK_URL=""
TWITCH_ROLE_ID=""
CHANNEL_LIST="channels.txt"
UPDATE_DELAY_MIN=
SAVE_FILE="save_data.json"
CLIENT_ID=
AUTH_KEY=
KEY_EXPIRE=
SECRET=
```

### Configuration Details:
- **DISCORD_WEBHOOK_URL**: The URL of the Discord webhook where alerts will be sent. [Learn how to create a webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).
- **TWITCH_ROLE_ID**: The Discord role ID to mention in alerts. [Learn how to find role IDs](https://readybot.io/help/how-to/find-discord-user-and-role-ids).
- **CHANNEL_LIST**: The path to the file containing the list of Twitch channel names.
- **UPDATE_DELAY_MIN**: The interval (in minutes) between live status checks.
- **SAVE_FILE**: The JSON file where the bot saves its state (e.g., `{"name": "twitch", "live": false}`).
- **CLIENT_ID**: The Twitch API APP Client ID.
- **AUTH_KEY**: The authentication key give to Twitch API APPs for Authorization.

---

## Managing Channels

- **View Usage Instructions:**
  ```bash
  python add-channel.py --help
  ```

- **Add a Single Channel:**
  ```bash
  python add-channel.py --channel <channel_name>
  ```

- **Add Multiple Channels from a File:**
  ```bash
  python add-channel.py --file <path/to/list/of/channels.txt>
  ```

---

## Running the Bot

Start the bot with the following command:

```bash
python bot.py
```


## Running the Server 

Start the server verion of the bot with the following command:

```bash
uvicorn server:app --reload
```

