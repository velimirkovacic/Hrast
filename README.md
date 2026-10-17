
# Discord Music Bot

A Python Discord music bot that lets users search for and play music in voice channels.

## Features

- Play music from search queries or supported URLs
- Join and leave Discord voice channels
- Queue and manage music playback
- Search for tracks using YouTube
- Stream audio using `yt-dlp` and FFmpeg
- Run in Docker for easy deployment
- Deploy updates to the server using GitHub Actions

## Requirements

- Python 3.12+
- A Discord bot application and token
- Docker
- FFmpeg
- A Discord server where the bot can be invited

## Configuration

The bot uses an environment file named `.env` on the server.

Create `.env` with the following variable:

```env
DISCORD_TOKEN=your_discord_bot_token
```

**Never commit `.env` or share your Discord token.** The real token should remain on the server.

## Run with Docker

Build the image:

```bash
docker build -t discord-bot .
```

Run the container:

```bash
docker run -d \
  --name discord-bot \
  --restart unless-stopped \
  --env-file .env \
  discord-bot
```

View the bot logs:

```bash
docker logs -f discord-bot
```

Stop the bot:

```bash
docker stop discord-bot
```

## Development

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the bot locally:

```bash
python bot.py
```

Make sure FFmpeg is installed and your `.env` file contains a valid Discord token.

## Deployment

The production bot runs in a Docker container named `discord-bot`.

GitHub Actions will be configured to deploy updates when changes are pushed to the `main` branch. Deployment should rebuild and restart only the `discord-bot` container and preserve the server's `.env` file.

## Security

- Never commit `.env` or Discord tokens.
- Keep deployment SSH credentials in GitHub Actions secrets.
- Do not store music downloads, logs, or Python cache files in version control.
