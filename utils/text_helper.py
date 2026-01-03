def normalize_modify(modify_str):
    """Converts 'id=20;is_internal=true' into {'id': '20', 'is_internal': 'true'}"""
    if not modify_str:
        return {}
    pairs = [item.split('=') for item in modify_str.split(';') if '=' in item]
    return {k.strip(): v.strip() for k, v in pairs}