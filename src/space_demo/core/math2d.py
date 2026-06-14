# 2D Vector Math Utilities - To Boldly Respawn

import math

def calculate_distance(x1, y1, x2, y2):
    """Calculates radial distance between two points."""
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def clamp_value(val, min_val, max_val):
    """Clamps a numeric value between min and max bounds."""
    return max(min_val, min(val, max_val))

def check_circle_overlap(x1, y1, r1, x2, y2, r2):
    """Returns True if two radial circles intersect."""
    dist = calculate_distance(x1, y1, x2, y2)
    return dist <= (r1 + r2)
