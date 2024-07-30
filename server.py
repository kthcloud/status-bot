import requests
import os
from dotenv import load_dotenv
import datetime
import time
from openai import OpenAI
import logging

import bsky
from mastodon import Mastodon

# Inititalise the logger
logger = logging.getLogger(__name__)
logger.setLevel("INFO")
console_handler = logging.StreamHandler()
formatter = logging.Formatter("{asctime} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.info("Starting server")

load_dotenv(override=True)
os.environ["TZ"] = "Europe/Stockholm"
time.tzset()
logger.info(f"Timezone: {time.tzname}")

testing = os.getenv("env") == "test"
logger.info(f"Testing: {testing}")

# Login to Mastodon
m = Mastodon(access_token=os.getenv("mastodon_access_token"),api_base_url=os.getenv("mastodon_base_url"))
logger.info("Mastodon Login Successful")

# Login to OpenAI
client = OpenAI(api_key=os.getenv("openai_secret"), organization=os.getenv("openai_org"))
# Allow up to 3 retries

def check_endpoint(endpoint):
    tries = 0
    while tries < 5:
        time.sleep(60)
        try:
            r = requests.get(endpoint[0], timeout=5)
            if r.status_code == 200:
                return True
            else:
                tries += 1
        except:
            logger.exception(f"Exception in endpoint check. Tries = {tries}")
            tries += 1
    return False


def toot(message, mode="alert"):
    """
    Send a toot to kthcloud mastodon account.
    """
    try:
        if os.getenv("openai_enabled") == "true":
            # test if llama is up, otherwise use gpt-3
            # Use llama to generate a toot based on the message
            sys_message = "You are the mastodon status bot for kthcloud, a cloud provider by students for students. Please rewrite the following message in a creative and funny way. make sure to include the link. Do not change the date. make sure to include the date."
            try:
                if mode == "update":
                    sys_message = "You are the mastodon status bot for kthcloud, a cloud provider by students for students. Please rewrite the following message in a creative and funny way. Do not change the date. make sure to include the date"

                res = requests.post(
                    "https://llama.app.cloud.cbh.kth.se/completion",
                    json={
                        "prompt": sys_message + 'Message: "' + message + '"\n\n\nllama:'
                    },
                )
                json = res.json()
                message = json["content"]
                logger.info(f"llama: {message}")
            except Exception:
                logger.exception("llama is down")
                # Use openai to generate a toot based on the message
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": sys_message},
                        {"role": "assistant", "content": message},
                    ],
                )
                message = response.choices[0].message.content
    except Exception as e:
        logger.exception(f"Error: {e}")
        # No genAI is fine, post the bare message

    # Remove any quotes, newlines, and double spaces
    message = message.replace('"', "").replace("\n", " ").replace("  ", " ").strip()

    if testing:
        logger.error(f"{message}")
    else:
        try:
            # Limit to 500 characters
            m.toot(message[:500])
        except Exception as e:
            logger.exception(f"Mastodon error {e}")
        try:
            # Limit to 300 characters
            bsky.toot(message[:300])
        except Exception as e:
            logger.exception(f"Bsky error {e}")


def bio(down, endpoints):
    bio_msg = "Stay informed on maintenance and outages of our free and open source cloud service, run by students.\nStatus:"
    down_msg = "🟢 All systems operational."
    if 0 < len(down) < 3:
        down_msg = "⚠️ Some services down: " + ", ".join(down)
    elif len(down) == len(endpoints):
        down_msg = "❌ Major outage. All services are currently down."
    elif len(down) > 0:
        down_msg = f"{len(down)} services are currently down."

    if testing:
        logger.debug(f"UPDATING BIO:\n{bio_msg} {down_msg}")
    else:
        m.account_update_credentials(note=f"{bio_msg} {down_msg}")


def get_last_summary():
    if os.path.exists("lastupdate"):
        with open("lastupdate", "r") as f:
            last_summary = datetime.datetime.strptime(f.read(), "%Y-%m-%d %H:%M:%S")
            logger.info(f"Last summary: {last_summary.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        last_summary = datetime.datetime.now()
    return last_summary


def get_endpoints():
    endpoints = []
    with open("endpoints.csv", "r") as f:
        for line in f:
            # strip line, split by comma, strip each element, and append to endpoints
            elements = line.strip().split(",")
            elements = [x.strip() for x in elements]
            endpoints.append(elements)
    endpoints = endpoints[1:]
    return endpoints


def main():
    # import endpoints from endpoints.csv, skip header
    endpoints = get_endpoints()
    logger.info(f"Imported {len(endpoints)} endpoints")
    down = []

    while True:
        last_summary = get_last_summary()

        # get current time
        now = datetime.datetime.now()
        logger.info({now.strftime("%Y-%m-%d %H:%M:%S")})

        # send summary if it's been 24 hours
        if (now - last_summary).total_seconds() > 86400:
            last_summary = now
            logger.debug("Sending summary")
            # print("Sending summary", file=sys.stderr)
            if len(down) == 0:
                toot(f"Summary as of {now.strftime('%Y-%m-%d')}. All endpoints up 🌞",mode="update",)
            else:
                toot(f"Summary as of {now.strftime('%Y-%m-%d')}. {len(down)} endpoints down: {down}",mode="update",)

            # save last_summary to file
            with open("lastupdate", "w") as f:
                f.write(last_summary.strftime("%Y-%m-%d %H:%M:%S"))

        # check endpoints
        for endpoint in endpoints:
            if check_endpoint(endpoint):
                logger.info(f"{endpoint[0]} is up")
                if endpoint[0] in down:
                    url = endpoint[0]
                    if endpoint[2] == "false":
                        url = "https://cloud.cbh.kth.se"
                    toot(f"{endpoint[1]} is back up as of {now.strftime('%Y-%m-%d %H:%M:%S')} 🛠️ {url}")
                    down.remove(endpoint[0])
            else:
                # print(f"{endpoint[0]} is down", file=sys.stderr)
                logger.info(f"{endpoint[0]} is down")
                if endpoint[0] not in down:
                    url = endpoint[0]
                    if endpoint[2] == "false":
                        url = "https://cloud.cbh.kth.se"
                    toot(f"{endpoint[1]} is down as of {now.strftime('%Y-%m-%d %H:%M:%S')} 💔 {url}")
                    down.append(endpoint[0])

        logger.info("sleeping...")

        bio(down, endpoints)

        # sleep 1 minute
        time.sleep(60)


# main
if __name__ == "__main__":
    main()
