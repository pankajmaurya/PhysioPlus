import numpy as np


def calculate_signed_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    angle = np.arctan2(bc[1], bc[0]) - np.arctan2(ba[1], ba[0])
    angle = np.degrees(angle)

    # Normalize angle to [-180, 180]
    if angle > 180:
        angle -= 360
    elif angle < -180:
        angle += 360

    return angle

# Calculate angles between 3 given points
def calculate_angle(a, b, c):
    a = np.array(a)  # First point
    b = np.array(b)  # Midpoint
    c = np.array(c)  # Endpoint
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

# Calculate distance between two landmarks
def calculate_distance(lm1,lm2,height,width):
    x1 = lm1.x * width
    y1 = lm1.y * height
    x2 = lm2.x * width
    y2 = lm2.y * height
    dist = ((x1-x2)**2 + (y1-y2)**2) ** 0.5
    return dist

# Calculate midpoint of two points
def calculate_mid_point(a,b):
    x = (a[0] + b[0]) / 2
    y = (a[1] + b[1]) / 2
    return((x,y))

def between(lower, value, upper):
    return lower <= value and value <= upper

def rnd2(v):
    return round(v, 2)