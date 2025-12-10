"""
Message router for the Jarvis Telegram bot.
Routes messages to appropriate handlers based on user type and message content.
"""

from telegram import Update
from telegram.ext import ContextTypes
from utils.security import is_admin
from bot.admin_interpreter import classify_admin_message, is_dev_instruction
from bot.handlers.normal_chat import handle_normal_chat
from agent.self_modifier import self_modifier, DevRequest
from utils.logger import app_logger

async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Route incoming messages to appropriate handlers.
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    if not update.message or not update.message.text:
        return
        
    user_id = update.effective_user.id
    message_text = update.message.text
    
    app_logger.info(f"Routing message from user {user_id}: {message_text[:50]}...")
    
    # Check if user is admin
    if is_admin(user_id):
        # For admins, check if it's a dev instruction or normal chat
        classification = await classify_admin_message(message_text)
        
        if is_dev_instruction(classification):
            # Handle as dev instruction
            await handle_dev_instruction(update, context, message_text, classification)
        else:
            # Handle as normal chat
            await handle_normal_chat(update, context)
    else:
        # For non-admins, always handle as normal chat
        await handle_normal_chat(update, context)

async def handle_dev_instruction(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    message_text: str, 
    classification: dict
) -> None:
    """
    Handle a dev instruction from an admin.
    
    Args:
        update: Telegram update object
        context: Telegram context object
        message_text: The original message text
        classification: Classification result
    """
    from utils.logger import app_logger
    app_logger.info(f"Handling dev instruction: {classification.get('summary', message_text)}")
    
    # Notify admin that we're processing the request
    await update.message.reply_text(
        "I received your request and I'm preparing changes. "
        "I will validate them and let you know when complete. "
        "(This may take a few seconds.)"
    )
    
    # Create a DevRequest
    from agent.self_modifier import DevRequest
    dev_request = DevRequest(
        intent="modify",
        target_files=classification.get("targets", []),
        goal_description=message_text
    )
    
    # Process the request
    from agent.self_modifier import self_modifier
    result = self_modifier.process_dev_request(dev_request)
    
    # Send result back to admin
    if result["status"] == "success":
        message = f"Done. {result['message']}"
        if result.get("restart_required"):
            message += " The bot will now restart."
    else:
        message = (
            f"Action failed. {result['message']} "
            f"See logs at jarvis/logs/self_modify.log for details."
        )
        
    await update.message.reply_text(message)