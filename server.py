import requests
from mastodon import Mastodon
import os
from dotenv import load_dotenv
import datetime
import time 
import sys
import openai

print("Starting server", file=sys.stderr)

load_dotenv()
os.environ['TZ'] = 'Europe/Stockholm'
time.tzset()
print(f"Timezone: {time.tzname}", file=sys.stderr)

testing = os.getenv("env") == "test"
print(f"Testing: {testing}", file=sys.stderr)

# Login to Mastodon
session = requests.Session()
session.verify = False
m = Mastodon(
    client_id="clientcred.secret",
    session=session,
)
m.log_in(
    os.getenv("email"),
    password=os.getenv("password"),
    to_file="usercred.secret"
)
m = Mastodon(access_token="usercred.secret", session=session)
print("Login successful", file=sys.stderr)

# Login to OpenAI
openai.organization = os.getenv("openai_org")
openai.api_key = os.getenv("openai_secret")

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


    if os.getenv("openai_enabled") == "true":
        # Use OpenAI to generate a toot based on the message

        sys_message = "You are the mastodon status bot for kthcloud, a cloud provider by students for students. Please rewrite the following message in a creative and funny way. make sure to include the link. Do not change the date. make sure to include the date."
        if mode == "update":
            sys_message = "You are the mastodon status bot for kthcloud, a cloud provider by students for students. Please rewrite the following message in a creative and funny way. Do not change the date. make sure to include the date"

        res = requests.post("https://llama.app.cloud.cbh.kth.se/completion", json={"prompt": sys_message + " " + message})
        json = res.json()
        res_message = json["content"]

        # response = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #             {"role": "system", "content": sys_message},
        #             {"role": "assistant", "content": message},
        #         ]
        #     )
        
        # message = response["choices"][0]["message"]["content"]


    if testing:
        print(res_message, file=sys.stderr)
    else:
        m.toot(res_message)


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

def main():

    ## import endpoints from endpoints.csv, skip header
    endpoints = []
    with open("endpoints.csv", "r") as f:
        for line in f:
            endpoints.append(line.strip().split(","))
    endpoints = endpoints[1:]

    print(f'Imported {len(endpoints)} endpoints', file=sys.stderr)

    down = []

    while True:
        ## check if last_summary file exists
        if os.path.exists("lastupdate"):
            with open("lastupdate", "r") as f:
                last_summary = datetime.datetime.strptime(f.read(), '%Y-%m-%d %H:%M:%S')
                print(f"Last summary: {last_summary.strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
        else:
            last_summary = datetime.datetime.now()

        ## get current time
        now = datetime.datetime.now()
        print(now.strftime('%Y-%m-%d %H:%M:%S'), file=sys.stderr)

        ## send summary if it's been 24 hours 
        if (now - last_summary).total_seconds() > 86400:
            last_summary = now
            print("Sending summary", file=sys.stderr)
            if len(down) == 0:
                toot(f"Summary as of {now.strftime('%Y-%m-%d')}. All endpoints up 🌞", mode="update")
            else:
                toot(f"Summary as of {now.strftime('%Y-%m-%d')}. {len(down)} endpoints down: {down}", mode="update")
            
            ## save last_summary to file
            with open("lastupdate", "w") as f:
                f.write(last_summary.strftime('%Y-%m-%d %H:%M:%S'))
            
    
        ## check endpoints
        for endpoint in endpoints:
            if check_endpoint(endpoint):
                print(f"{endpoint[0]} is up" , file=sys.stderr)
                if endpoint[0] in down:
                    toot(f"{endpoint[1]} is back up as of {now.strftime('%Y-%m-%d %H:%M:%S')} 🛠️ {endpoint[0]}")
                    down.remove(endpoint[0])
            else:
                print(f"{endpoint[0]} is down" , file=sys.stderr)
                if endpoint[0] not in down:
                    toot(f"{endpoint[1]} is down as of {now.strftime('%Y-%m-%d %H:%M:%S')} 💔 {endpoint[0]}")
                    down.append(endpoint[0])

        print("sleeping..." , file=sys.stderr)

        bio(down, endpoints)
        
        ## sleep 1 minute
        time.sleep(60)

## main
if __name__ == "__main__":
    main()