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
- Create a .env file with `env=test` and appropriate API keys (Mastodon credentials are in KTH social wiki)

## Deployment
- You'll need Docker installed on the target machine
- Ensure this is run outside kthcloud, otherwise it will be down aswell and cannot report outages.
- Currently deployed on a Raspberry Pi by **pierrelf@kth.se**
