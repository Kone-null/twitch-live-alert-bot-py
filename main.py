# https://realpython.com/how-to-make-a-discord-bot-python/

import requests
import httpx
import time
import asyncio
from discord import SyncWebhook


# channelName = "oliviamonroe"

# contents = requests.get("https://www.twitch.tv/" + channelName).content.decode("utf-8")


# # with open('out.html','w',encoding='utf-8') as f:
# #     f.write(contents)

# if "isLiveBroadcast" in contents:
#     print(channelName + " is live")
# else:
#     print(channelName + " is not live")


STREAMER_LIST_FILE: str = "streamers.txt"
LIVE_CHECK_DELAY: int = (60) * 10  # IN SECONDS
DISCORD_WEBHOOK_URL: str = (
    "https://discord.com/api/webhooks/1307137959337918494/29XOtqNHZH72ISMqoXQc10Hpw8MPk4IFvnZ2-1ABZmUiqm1QKsCpFtIu0YXnBTDMjBh9"
)

TWITCH_ROLE_ID = "1305260106417569812"

async def isLive(channelName: str) -> bool:
    try:

        client = httpx.AsyncClient()
        response = await client.get("https://www.twitch.tv/" + channelName)
        response.raise_for_status()

        contents = response.text

        if "isLiveBroadcast" in contents:
            return True
        else:
            return False

    except httpx.RequestError as exc:
        raise httpx.RequestError(
            f"An error occurred while requesting {exc.request.url!r}."
        )
    except httpx.HTTPStatusError as exc:
        raise httpx.HTTPStatusError(
            f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
        )


def get_streamers(filename: str) -> list:
    with open(filename, "r") as f:
        streamers = f.read().split("\n")
        return streamers


def send_webhook(channelName, status) -> None:
    webhook = SyncWebhook.from_url(DISCORD_WEBHOOK_URL)
    webhook.send(f" <@&{TWITCH_ROLE_ID}>{channelName} is {status}!")


async def main():

    streamers: list[str] = get_streamers(STREAMER_LIST_FILE)
    live_streamers: list[str] = []

    while True:
        print(f"Status :{len(live_streamers)} of {len(streamers)} is live")

        

        # check streamer status
        for streamer in streamers:

            if await isLive(streamer):
                print(f"{streamer} is Live!")

                if streamer in live_streamers:
                    continue

                send_webhook(streamer, "live")
                live_streamers.append(streamer)
                streamers = [item for item in streamers if item != streamer]
                print(f"{streamer} moveed to Live Streamer list")

            else:
                print(f"{streamer} is Offline! ")
                if streamer in live_streamers:
                    streamers.append(streamer)
                    live_streamers = [
                        item for item in live_streamers if item != streamer
                    ]
                    print(f"{streamer} moveed to Streamer list")
                    send_webhook(streamer, "Offline")
        print("Waiting 10 min")
        time.sleep(LIVE_CHECK_DELAY)


if __name__ == "__main__":

    asyncio.run(main())
