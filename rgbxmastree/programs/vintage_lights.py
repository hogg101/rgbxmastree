from __future__ import annotations

from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def vintage_lights(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Classic large bulb string lights look.
    """
    # Speed handling
    s = max(0.001, float(speed))
    delay = max(0.1, 0.5 / s) # Slower updates like old blinking lights
    
    # Classic C9 bulb colors
    palette = [
        (1.0, 0.0, 0.0), # Red
        (0.0, 1.0, 0.0), # Green
        (0.0, 0.0, 1.0), # Blue
        (1.0, 0.5, 0.0), # Orange/Gold
        (1.0, 0.0, 1.0), # Pink/Magenta
    ]
    
    offset = 0
    
    while not stop.is_set():
        prev_auto = tree.auto_show
        tree.auto_show = False
        
        try:
            # Iterate through all pixels in a linear fashion
            # (Level 0, 0-7), (Level 1, 0-7), (Level 2, 0-7)
            
            count = 0
            for level in range(3):
                for branch in range(8):
                    color_idx = (count + offset) % len(palette)
                    tree[level, branch].color = palette[color_idx]
                    count += 1
            
            # Star matches the next in sequence
            tree.star.color = palette[(count + offset) % len(palette)]
            
            tree.show()
            
        finally:
            tree.auto_show = prev_auto
            
        offset += 1
        sleep(delay)
