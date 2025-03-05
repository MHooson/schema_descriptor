"""
Text utility functions.
Provides common functionality for working with text.
"""

def merge_descriptions(old_desc, new_desc, replace=False):
    """
    Merges or replaces text descriptions.
    
    Args:
        old_desc: The original description text
        new_desc: The new description text
        replace: If True, replace the old description with the new one.
                If False, merge them with a divider.
        
    Returns:
        A merged or replaced description string
    """
    old_desc = old_desc.strip() if old_desc else ""
    new_desc = new_desc.strip() if new_desc else ""
    
    if not old_desc:
        return new_desc
    if not new_desc:
        return old_desc
        
    if replace:
        return new_desc
    else:
        return f"{old_desc}\n\n---\n{new_desc}"

def _serialize_unknown_type(obj):
    """
    Serializes an object of unknown type to a string.
    
    Args:
        obj: The object to serialize
        
    Returns:
        A string representation of the object
    """
    return str(obj)