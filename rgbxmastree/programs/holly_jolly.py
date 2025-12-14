from __future__ import annotations

import random
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def holly_jolly(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Festive sparkles in Red, Green, and Gold.
    """
    # Speed handling
    s = max(0.001, float(speed))
    delay = max(0.01, 0.1 / s)
    
    colors = [
        (1.0, 0.0, 0.0), # Red
        (0.0, 1.0, 0.0), # Green
        (1.0, 0.8, 0.0), # Gold
    ]
    
    # Initialize tree with dim green background
    for pixel in tree:
        pixel.color = (0.0, 0.1, 0.0)
        
    while not stop.is_set():
        # Pick a random pixel to sparkle
        pixel = random.choice(list(tree))
        
        # Flash it bright
        color = random.choice(colors)
        pixel.color = color
        
        # Occasionally reset a random pixel to background to prevent saturation
        # Or just let them fade naturally? 
        # Let's just randomly set pixels.
        
        # To make it twinkle, we need to turn them off/dim them too.
        if random.random() < 0.5:
            off_pixel = random.choice(list(tree))
            off_pixel.color = (0.0, 0.1, 0.0)
            
        sleep(delay)
