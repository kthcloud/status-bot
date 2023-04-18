import requests
from mastodon import Mastodon
import os
from dotenv import load_dotenv
import datetime
import time 
import sys

load_dotenv()


def check_endpoint(endpoint):
    try:
        r = requests.get(endpoint[0], timeout=5)
        if r.status_code == 200:
            return True
        else:
            return False
    except:
        return False


def main():
    session = requests.Session()
    session.verify = False

    # Authenticate the app
    m = Mastodon(
        client_id="clientcred.secret",
        session=session,
    )

    # Login as a user (with Password)
    m.log_in(
        os.getenv("email"),
        password=os.getenv("password"),
        to_file="usercred.secret"
    )

    m = Mastodon(access_token="usercred.secret", session=session)

    print("Login successful", file=sys.stderr)

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
                m.toot(f"Summary as of {now.strftime('%Y-%m-%d')}. All endpoints up 🌞")
            else:
                m.toot(f"Summary as of {now.strftime('%Y-%m-%d')}. {len(down)} endpoints down: {down}")
            
            ## save last_summary to file
            with open("lastupdate", "w") as f:
                f.write(last_summary.strftime('%Y-%m-%d %H:%M:%S'))
            
    
        ## check endpoints
        for endpoint in endpoints:

            if check_endpoint(endpoint):
                print(f"{endpoint[0]} is up" , file=sys.stderr)
                if endpoint[0] in down:
                    m.toot(f"{endpoint[1]} is back up as of {now.strftime('%Y-%m-%d %H:%M:%S')} 🛠️ {endpoint[0]}")
                    down.remove(endpoint[0])
            else:
                print(f"{endpoint[0]} is down" , file=sys.stderr)
                if endpoint[0] not in down:
                    m.toot(f"{endpoint[1]} is down as of {now.strftime('%Y-%m-%d %H:%M:%S')} 💔 {endpoint[0]}")
                    down.append(endpoint[0])

        print("sleeping..." , file=sys.stderr)
        
        ## sleep 15 minutes
        time.sleep(300)

## main
if __name__ == "__main__":
    main()