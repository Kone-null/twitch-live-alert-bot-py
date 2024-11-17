# Twitch Live Alert Bot
Twitch Live Alert Bot is Discord Webhook bot the periodly checks a Twitch channel(s) 'live' status. 
Then send an Live alert when a channels is detected as live. Additionally, if an already live channel is detected to be offline, an update message will also be sent to let the user know the channel is offline.


## Setup
1. clone repo
2. cd `twitch-live-alert-bot-py`
3. Create envirnment: `python3 -m venv .`
4. Install dependacies:`pip install -r requirements.txt`
5. fill out `channels.txt ` with list of twitch channel names (not urls/links)

## Configuration

Make `.env` file:
```
DISCORD_WEBHOOK_URL=""
TWITCH_ROLE_ID=""
CHANNEL_LIST="channels.txt"
UPDATE_DELAY_MIN=
SAVE_FILE="save_data.json"
```


## Add or Follow Channel
- usage:`python add-channel.py --help`
- add single channel: `python add-channel.py  --channel <channelname>`
- add many channels: `python add-channel.py --file <path/to/listofchannels.txt>`

## Use
run `python3 bot.py`
