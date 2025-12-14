from __future__ import annotations

import random
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def fireplace(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Cozy fireplace effect with flickering reds, oranges, and yellows.
    """
    # Speed affects flicker rate
    s = max(0.001, float(speed))
    delay = max(0.01, 0.08 / s)
    
    def get_fire_color(intensity):
        """Convert 0.0-1.0 intensity to fire color"""
        # High intensity = Yellow/White
        # Med intensity = Orange
        # Low intensity = Red
        # Very low = Dim Red/Off
        
        if intensity > 0.9:
            return (1.0, 1.0, 0.5) # White-Yellow
        elif intensity > 0.7:
            return (1.0, 0.5, 0.0) # Orange
        elif intensity > 0.4:
            return (1.0, 0.0, 0.0) # Red
        elif intensity > 0.1:
            return (0.3, 0.0, 0.0) # Dim Red
        else:
            return (0.0, 0.0, 0.0)
            
    while not stop.is_set():
        prev_auto = tree.auto_show
        tree.auto_show = False
        
        try:
            # Generate heat map
            
            # Bottom level: Hot! High intensity
            for b in range(8):
                flicker = random.uniform(0.6, 1.0)
                tree[0, b].color = get_fire_color(flicker)
            
            # Middle level: Medium heat
            for b in range(8):
                # Often correlates with bottom, but with lag or randomness
                flicker = random.uniform(0.3, 0.8)
                tree[1, b].color = get_fire_color(flicker)
                
            # Top level: Sparks and smoke
            for b in range(8):
                if random.random() < 0.3:
                    flicker = random.uniform(0.1, 0.5)
                else:
                    flicker = 0.0
                tree[2, b].color = get_fire_color(flicker)
            
            # Star: Occasional glowing ember
            if random.random() < 0.2:
                tree.star.color = (0.5, 0.1, 0.0) # Warm glow
            else:
                r, g, b = tree.star.color
                tree.star.color = (max(0, r-0.05), max(0, g-0.05), max(0, b-0.05))
                
            tree.show()
            
        finally:
            tree.auto_show = prev_auto
            
        sleep(delay)
