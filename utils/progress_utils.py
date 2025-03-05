"""
Progress tracking utility functions.
Provides common functionality for tracking and displaying progress.
"""

def get_completion_percentage(current, total):
    """
    Calculate percentage completion.
    
    Args:
        current: Current progress value
        total: Total progress value
        
    Returns:
        Integer percentage value between 0 and 100
    """
    if total == 0:
        return 100
    return min(int((current / total) * 100), 100)

class ProgressTracker:
    """
    A class for tracking and reporting progress of operations.
    """
    
    def __init__(self, callback=None):
        """
        Initialize a new progress tracker.
        
        Args:
            callback: A function to call with progress messages
        """
        self.callback = callback
        self.state = {
            "current": 0,
            "total": 0,
            "stage": "initializing"
        }
        
    def update(self, message, current=None, total=None, stage=None):
        """
        Update the progress tracker state and send a message.
        
        Args:
            message: The message to send
            current: The current progress value (optional)
            total: The total progress value (optional)
            stage: The current stage of progress (optional)
        """
        if current is not None:
            self.state["current"] = current
        if total is not None:
            self.state["total"] = total
        if stage is not None:
            self.state["stage"] = stage
            
        if self.callback:
            self.callback(message)
            
    def get_percentage(self):
        """
        Get the current completion percentage.
        
        Returns:
            Integer percentage value between 0 and 100
        """
        return get_completion_percentage(self.state["current"], self.state["total"])