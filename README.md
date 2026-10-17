
# Discord Music Bot

A Python Discord music bot that lets users search for and play music in voice channels. The bot runs in Docker and is deployed to a Linux server using GitHub Actions and GitHub Container Registry (GHCR).

## Features

- Play music from search queries or supported URLs
- Join and leave Discord voice channels
- Queue and manage music playback
- Search for tracks using YouTube
- Stream audio using `yt-dlp` and FFmpeg
- Run in Docker for isolated and consistent deployment
- Automatically build, publish, and deploy updates through GitHub Actions

## Requirements

- Python 3.12+
- A Discord bot application and token
- Docker and Docker Compose
- FFmpeg (included in the Docker image)
- A Discord server where the bot can be invited

## Project Structure

```text
.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── src/
│   ├── bot.py
│   ├── help_cog.py
│   └── music_cog.py
└── .github/
    └── workflows/
        └── ci.yml
```

## Configuration

The production server uses an environment file at `/opt/hrast/.env`.

Create a `.env` file for local development containing:

```env
DISCORD_TOKEN=your_discord_bot_token
```

**Never commit `.env` or share your Discord token.** The production environment file is stored on the server and is not included in the Docker image.

## Local Development

### Install dependencies

Python 3.12+ is recommended.

```bash
pip install -r requirements.txt
```

Make sure FFmpeg is installed and available on your system.

### Configure the environment

Create a `.env` file in the project root with a valid `DISCORD_TOKEN`.

### Run the bot

Run the bot as a Python module from the project root:

```bash
python -u -m src.bot
```

Using `-m` allows Python to resolve imports such as `from src.music_cog import music_cog`.

## Docker

### Build the image

```bash
docker build -t discord-music-bot .
```

### Run a local container

```bash
docker run -d \
  --name discord-music-bot \
  --restart unless-stopped \
  --env-file .env \
  discord-music-bot
```

### View logs

```bash
docker logs -f discord-music-bot
```

### Stop the container

```bash
docker stop discord-music-bot
```

### Remove the container

```bash
docker rm discord-music-bot
```

These commands are for local testing. The production container is managed separately by Docker Compose.

## Deployment

Production deployment uses GitHub Actions, GHCR, and a self-hosted GitHub Actions runner on the Linux server.

The workflow in `.github/workflows/ci.yml`:

1. Checks Python syntax.
2. Builds the Docker image to validate the Dockerfile.
3. Publishes the image to GHCR.
4. Deploys the new image to the server when changes are pushed to `main` or a workflow is manually triggered on `main`.

The production image is:

```text
ghcr.io/velimirkovacic/discord-music-bot
```

The production Compose configuration is located at `/opt/hrast/docker-compose.yml`, and the container is named `hrast`.

The deployment updates only the `hrast` service. It uses the existing `/opt/hrast/.env` file and does not require the Discord token to be stored in the repository.

### Check the production container

```bash
docker ps --filter "name=^/hrast$"
```

### View production logs

```bash
docker logs --tail 50 hrast
```

### Restart the production container manually

```bash
cd /opt/hrast
docker compose up -d --no-deps hrast
```

Normally, GitHub Actions handles deployment automatically, so manual restarts should not be necessary.

## Security

- Never commit `.env`, Discord tokens, or other secrets.
- Keep production environment variables on the server.
- Use GitHub Actions permissions and secrets appropriately.
- Do not store music downloads, logs, Python cache files, or other generated files in version control.
- Avoid broad Docker cleanup commands on the production server because other applications may use the same Docker host.
