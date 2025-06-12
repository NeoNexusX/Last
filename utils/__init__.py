def format_object_for_log(obj):
    """
    Format an object's attributes for pretty logging.
    
    Args:
        obj: Object whose attributes need to be formatted
        
    Returns:
        str: Formatted string representation of object attributes
    """
    outputs = []
    for k, v in obj.__dict__.items():
        if isinstance(v, dict):
            outputs.append(f"{k}:")
            for k_d, v_d in v.items():
                outputs.append(f"    {k_d}: {v_d}")
        elif isinstance(v, list):
            outputs.append(f"{k}:")
            for item in v:
                outputs.append(f"    {item}")
        else:
            outputs.append(f"{k}: {v}")
            
    return '\n'.join(outputs) 