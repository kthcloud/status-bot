# status-bot
Mastodon status bot for kthcloud

## Listen to new endpoints
- Add the endpoint to `endpoints.csv` in the appropriate format.
- Redeploy (Notify whoever is running the service)

## Development
- Local python3 installation
- Install pip requirements `python3 -m pip install -r requirements.txt`
- Create a .env file with `env=test` and appropriate API keys (Mastodon credentials are in KTH social wiki)

## Deployment
- Ensure this is run outside kthcloud, otherwise it will be down aswell and cannot report outages.
- Currently deployed on a Raspberry Pi by **pierrelf@kth.se**
