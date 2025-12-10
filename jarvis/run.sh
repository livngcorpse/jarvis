#!/bin/bash

# Script to run the Jarvis Telegram bot

# Check if .env file exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file"
    export $(cat .env | xargs)
else
    echo "Warning: .env file not found. Using environment variables from system."
fi

# Run the bot
python app.py