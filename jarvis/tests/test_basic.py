"""
Basic tests for the Jarvis Telegram bot.
"""

import sys
import os
import pytest

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def test_normal_chat_reply():
    """Test that the normal chat handler can generate a reply."""
    from bot.handlers.normal_chat import reply_to_text
    
    # Test with a simple message
    result = reply_to_text("Hello")
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Hello" in result

def test_imports():
    """Test that we can import key modules without errors."""
    # These imports should not raise exceptions
    from bot.handlers.normal_chat import handle_normal_chat
    from bot.handlers.health import handle_health_check
    from bot.dispatcher import setup_dispatcher
    from config import ADMIN_IDS
    
    # Just verifying imports work - no assertions needed
    assert True

if __name__ == "__main__":
    pytest.main([__file__])