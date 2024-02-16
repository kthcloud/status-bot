import requests
from mastodon import Mastodon
import os
from dotenv import load_dotenv
import datetime
import time
import sys
from openai import OpenAI

import bsky

print("Starting server", file=sys.stderr)

load_dotenv()
os.environ["TZ"] = "Europe/Stockholm"
time.tzset()
print(f"Timezone: {time.tzname}", file=sys.stderr)

testing = os.getenv("env") == "test"
print(f"Testing: {testing}", file=sys.stderr)

# Login to Mastodon
m = Mastodon(client_id="clientcred.secret")
m.log_in(
    username=os.getenv("mastodon_user"),
    password=os.getenv("mastodon_password"),
    to_file="usercred.secret",
)
m = Mastodon(access_token="usercred.secret")
print("Login successful", file=sys.stderr)


# Login to OpenAI
client = OpenAI(
    api_key=os.getenv("openai_secret"), organization=os.getenv("openai_org")
)


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
            tries += 1
    return False


def toot(message, mode="alert"):
    try:
        if os.getenv("openai_enabled") == "true":
            # test if llama is up, otherwise use gpt-3
            try:
                # Use llama to generate a toot based on the message
                sys_message = "You are the mastodon status bot for kthcloud, a cloud provider by students for students. Please rewrite the following message in a creative and funny way. make sure to include the link. Do not change the date. make sure to include the date."
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
                print(f"llama: {message}", file=sys.stderr)
            except Exception:
                print("llama is down", file=sys.stderr)
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
        print(f"Error: {e}", file=sys.stderr)
        # No genAI is fine, post the bare message

    # Remove any quotes, newlines, and double spaces
    message = message.replace('"', "").replace("\n", " ").replace("  ", " ").strip()

    if testing:
        print(message, file=sys.stderr)
    else:
        try:
            # Limit to 500 characters
            m.toot(message[:500])
        except Exception as e:
            print("Mastodon error " + e, file=sys.stderr)

        try:
            # Limit to 300 characters
            bsky.toot(message[:300])
        except Exception as e:
            print("Bsky error " + e, file=sys.stderr)


def bio(down, endpoints):
    bio_msg = "Stay informed on maintenance and outages of our free and open source cloud service, run by students.\nStatus:"
    down_msg = "🟢 All systems operational."
    if len(down) > 0 and len(down) < 3:
        down_msg = "⚠️ Some services down: " + ", ".join(down)
    elif len(down) == len(endpoints):
        down_msg = "❌ Major outage. All services are currently down."
    elif len(down) > 0:
        down_msg = f"{len(down)} services are currently down."

    if testing:
        print(f"UPDATING BIO:\n{bio_msg} {down_msg}", file=sys.stderr)
    else:
        m.account_update_credentials(note=f"{bio_msg} {down_msg}")


def get_last_summary():
    if os.path.exists("lastupdate"):
        with open("lastupdate", "r") as f:
            last_summary = datetime.datetime.strptime(f.read(), "%Y-%m-%d %H:%M:%S")
            print(
                f"Last summary: {last_summary.strftime('%Y-%m-%d %H:%M:%S')}",
                file=sys.stderr,
            )
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

    print(f"Imported {len(endpoints)} endpoints", file=sys.stderr)

    down = []

    while True:
        last_summary = get_last_summary()

        # get current time
        now = datetime.datetime.now()
        print(now.strftime("%Y-%m-%d %H:%M:%S"), file=sys.stderr)

        # send summary if it's been 24 hours
        if (now - last_summary).total_seconds() > 86400:
            last_summary = now
            print("Sending summary", file=sys.stderr)
            if len(down) == 0:
                toot(
                    f"Summary as of {now.strftime('%Y-%m-%d')}. All endpoints up 🌞",
                    mode="update",
                )

            else:
                toot(
                    f"Summary as of {now.strftime('%Y-%m-%d')}. {len(down)} endpoints down: {down}",
                    mode="update",
                )

            # save last_summary to file
            with open("lastupdate", "w") as f:
                f.write(last_summary.strftime("%Y-%m-%d %H:%M:%S"))

        # check endpoints
        for endpoint in endpoints:
            if check_endpoint(endpoint):
                print(f"{endpoint[0]} is up", file=sys.stderr)
                if endpoint[0] in down:
                    url = endpoint[0]
                    if endpoint[2] == "false":
                        url = "https://cloud.cbh.kth.se"
                    toot(
                        f"{endpoint[1]} is back up as of {now.strftime('%Y-%m-%d %H:%M:%S')} 🛠️ {url}"
                    )
                    down.remove(endpoint[0])
            else:
                print(f"{endpoint[0]} is down", file=sys.stderr)
                if endpoint[0] not in down:
                    url = endpoint[0]
                    if endpoint[2] == "false":
                        url = "https://cloud.cbh.kth.se"
                    toot(
                        f"{endpoint[1]} is down as of {now.strftime('%Y-%m-%d %H:%M:%S')} 💔 {url}"
                    )
                    down.append(endpoint[0])

        print("sleeping...", file=sys.stderr)

        bio(down, endpoints)

        # sleep 1 minute
        time.sleep(60)


# main
if __name__ == "__main__":
    main()
