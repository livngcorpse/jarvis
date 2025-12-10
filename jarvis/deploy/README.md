# Deployment Instructions

## Systemd Deployment

1. Create a dedicated user for the bot:
   ```bash
   sudo useradd -r -s /bin/false jarvis
   ```

2. Copy the jarvis directory to `/opt/jarvis`:
   ```bash
   sudo cp -r /path/to/jarvis /opt/jarvis
   ```

3. Set ownership:
   ```bash
   sudo chown -R jarvis:jarvis /opt/jarvis
   ```

4. Create `/etc/jarvis` directory and copy `.env` file:
   ```bash
   sudo mkdir -p /etc/jarvis
   sudo cp /opt/jarvis/.env.example /etc/jarvis/.env
   sudo chown -R jarvis:jarvis /etc/jarvis
   ```

5. Edit the environment file with your actual values:
   ```bash
   sudo nano /etc/jarvis/.env
   ```

6. Copy the systemd service file:
   ```bash
   sudo cp /opt/jarvis/deploy/jarvis.service /etc/systemd/system/
   ```

7. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable jarvis
   sudo systemctl start jarvis
   ```

## Docker Deployment

Use the provided docker-compose.yml file:

```bash
docker-compose up -d
```

Make sure to set the environment variables in the `.env` file before starting.