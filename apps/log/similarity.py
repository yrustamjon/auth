import re


def log_similarity(cause):
    """Read the cosine similarity recorded by face verification."""
    match = re.search(r'\bsimilarity=(-?\d+(?:\.\d+)?)(?=\)|\s|$)', cause or '')
    if not match:
        return None
    value = float(match.group(1))
    return value if 0 <= value <= 1 else None
