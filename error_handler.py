import logging
import traceback

class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: str = ""):
        """Handle and log errors"""
        error_msg = f"Error in {context}: {str(error)}"
        self.logger.error(error_msg)
        self.logger.error(traceback.format_exc())
        return error_msg