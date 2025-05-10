# Gelato

This is a simple discord bot made to download and convert links into embeddable videos for discord.

For now this supports: 
- 9GAG
- Twitter/X
- Youtube
- Instagram

### Running it
Clone the repository:
```bash
git clone https://github.com/muji06/gelato
cd gelato
```

Then build the main image with docker compose and run it:
```bash
docker compose up --build
```

Create a `.env` file inside app/ folder for the discord token, or pass it as an environment variable:
```
TOKEN=<discord-token-here>
```

