import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timezone


load_dotenv()

# code "borrowed" from https://atproto.com/blog/create-post

def toot(message):
    resp = requests.post(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        json={"identifier": os.getenv(
            "bsky_user"), "password": os.getenv("bsky_password")},
    )
    resp.raise_for_status()
    session = resp.json()

    # Fetch the current time
    # Using a trailing "Z" is preferred over the "+00:00" format
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    post = {
        "$type": "app.bsky.feed.post",
        "text": message,
        "createdAt": now,
    }

    resp = requests.post(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": "Bearer " + session["accessJwt"]},
        json={
            "repo": session["did"],
            "collection": "app.bsky.feed.post",
            "record": post,
        },
    )
    print(json.dumps(resp.json(), indent=2))
    resp.raise_for_status()
