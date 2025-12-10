"""
Entrypoint for the Jarvis Telegram bot.
Can be used as a Docker entrypoint or run directly.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main() -> None:
    """Main entrypoint."""
    try:
        # Import and run the main function
        from main import main as run_bot
        import asyncio
        asyncio.run(run_bot())
    except ImportError as e:
        print(f"Failed to import main module: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Bot failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()