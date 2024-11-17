## Setup
1. clone repo
2. fill out `channels.txt ` with list of twitch channel names (not urls/links)

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
- add single channel: `python add-channel.py <channelname>`
- add many channels: `python add-channel.py <path/to/listofchannels.txt>`

## Use
run `python3 bot.py`
