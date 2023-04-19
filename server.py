import requests
from mastodon import Mastodon
import os
from dotenv import load_dotenv
import datetime
import time 
import sys
import openai

load_dotenv()
os.environ['TZ'] = 'Europe/Stockholm'
time.tzset()

testing = os.getenv("env") == "test"

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
    while tries < 3:
        time.sleep(1)
        try:
            r = requests.get(endpoint[0], timeout=5)
            if r.status_code == 200:
                return True
            else:
                tries += 1
        except:
            tries += 1
    return False


def toot(message):

    if os.getenv("openai_enabled") == "true":
        # Use OpenAI to generate a toot based on the message
        response = openai.Completion.create(
            engine="gpt-4",
            prompt="You are the mastodon status bot for kthcloud, a cloud provider by students for students. Please rewrite the following message in a creative and funny way. make sure to include the link: " + message,
        )
        message = response["choices"][0]["text"]

    if testing:
        print(message, file=sys.stderr)
    else:
        m.toot(message)

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
                toot(f"Summary as of {now.strftime('%Y-%m-%d')}. All endpoints up 🌞")
            else:
                toot(f"Summary as of {now.strftime('%Y-%m-%d')}. {len(down)} endpoints down: {down}")
            
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
        
        ## sleep 1 minute
        time.sleep(60)

## main
if __name__ == "__main__":
    main()