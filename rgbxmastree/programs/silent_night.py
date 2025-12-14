from __future__ import annotations

import math
import time
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def silent_night(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Peaceful, slow-moving blue and white gradients.
    """
    # Speed handling - this one should naturally be slower
    s = max(0.001, float(speed))
    # We use time.time() for the wave, delay just controls framerate
    delay = 0.05 
    
    while not stop.is_set():
        prev_auto = tree.auto_show
        tree.auto_show = False
        
        t = time.time() * s
        
        try:
            # Gentle vertical wave
            for level in range(3):
                # Calculate brightness based on sine wave
                # Offset phase by level
                val = (math.sin(t + level) + 1) / 2 # 0.0 to 1.0
                
                # Interpolate between Deep Blue and White/Cyan
                # Deep Blue: (0, 0, 0.5)
                # Cyan/White: (0.5, 0.5, 1.0)
                
                r = 0.0 + (0.5 - 0.0) * val
                g = 0.0 + (0.5 - 0.0) * val
                b = 0.5 + (1.0 - 0.5) * val
                
                for branch in range(8):
                    # Add slight variation per branch
                    b_var = (math.sin(t + branch * 0.5) + 1) / 4
                    tree[level, branch].color = (r, g, min(1.0, b + b_var))
            
            # Star pulses slowly
            star_val = (math.sin(t * 1.5) + 1) / 2
            tree.star.color = (star_val, star_val, 1.0)
            
            tree.show()
            
        finally:
            tree.auto_show = prev_auto
            
        sleep(delay)
