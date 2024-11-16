## Setup
1. clone repo
2. fill out `streamers.txt ` with list of twitch channel names (not urls/links)
3. in main.py:
   - set `DISCORD_WEBHOOK_URL` to discord webhook url
   - set `TWITCH_ROLE_ID` to role id set for alerts
   - adjust `LIVE_CHECK_DELAY` to change delay time in seconds


## Use
python3 main.py
