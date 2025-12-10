# Jarvis — a JARVIS-style Telegram bot (Python + Gemini API)

IMPORTANT: Examples in this repository are for illustration only and do not represent exhaustive security or production hardening. Before deploying to production:
- Lock ADMIN_IDS to specific Telegram numeric IDs only.
- Use a VM or container with restricted filesystem permissions.
- Never expose the Gemini API key or Telegram token publicly.

## Overview

Jarvis is a self-modifying Telegram bot that can be controlled through natural language commands. Admin users can instruct the bot to modify its own code, add features, or change behavior without traditional slash commands.

## Features

- Natural language interface for both users and admin
- Self-modification capabilities for admin users
- Safety mechanisms including backups and validation
- Reload Mode C: prefer soft reloads for small changes but perform a full restart when necessary
- Sandbox enforcement to prevent unauthorized file access
- Docker support for easy deployment

## Prerequisites

- Python 3.11+
- A Telegram bot token (from @BotFather)
- A Gemini API key

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd jarvis
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   make install
   ```

4. Copy the example environment file and edit it with your values:
   ```bash
   cp .env.example .env
   nano .env  # or your preferred editor
   ```

5. Run the bot:
   ```bash
   python app.py
   ```

## Environment Variables

- `TELEGRAM_TOKEN`: Your Telegram bot token
- `GEMINI_API_KEY`: Your Gemini API key
- `ADMIN_IDS`: Comma-separated list of Telegram user IDs with admin privileges
- `ALLOWED_ROOT`: Root directory for file operations (default: ./jarvis)
- `LOG_LEVEL`: Logging level (default: INFO)

## Usage

### For Regular Users

Regular users can chat with the bot naturally. The bot will respond using the Gemini API.

### For Admin Users

Admin users can instruct the bot to modify itself using natural language. For example:
- "Change the welcome message to be more friendly"
- "Add a new command that responds with the current time"
- "Modify the help text to include examples"

The bot will:
1. Interpret your instruction
2. Generate the necessary code changes
3. Validate the changes (linting, testing)
4. Apply the changes
5. Reload the bot if necessary
6. Confirm the changes are live

## Deployment

See `deploy/README.md` for detailed deployment instructions using either:
- Systemd service
- Docker with docker-compose

## Security Notes

- Only give ADMIN_IDS to trusted persons
- The bot enforces a sandbox to prevent file access outside the project directory
- All changes are backed up before applying
- Failed changes are automatically rolled back

## Development

### Running Tests

```bash
make test
```

### Linting

```bash
make lint
```

## License

See LICENSE file for details.

NOTE: This project enables code editing via natural-language. Only give ADMIN_IDS to trusted persons. Use backups and monitoring. Test changes in a staging environment before enabling production auto-apply.