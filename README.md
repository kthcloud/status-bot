# 🤖 kthcloud/status-bot
Mastodon & Bluesky status bot for kthcloud

## Links
- https://mastodon.social/@kthcloud
- https://bsky.app/profile/cloud.cbh.kth.se

## Listen to new endpoints
- Add the endpoint to `endpoints.csv` in the appropriate format.
- Redeploy (Notify whoever is running the service)

## Development
- Local python3 installation
- Install pip requirements `python3 -m pip install -r requirements.txt`
- Create a .env file with and appropriate API keys (Mastodon credentials are in KTH secure store on Keypass). Following is content for .env file

```
mastodon_access_token=""
mastodon_base_url="https://mastodon.social"

bsky_user=""
bsky_password=""

openai_secret=""
openai_org=""
openai_enabled="false"
```
## Deployment
- You'll need Docker installed on the target machine
- Ensure this is run outside kthcloud, otherwise it will be down as well and cannot report outages.
- Currently deployed on Linode by Harsha.
