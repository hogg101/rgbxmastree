from __future__ import annotations

from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def police_lights(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Rotating red and blue police lights.
    """
    # Speed handling
    s = max(0.001, float(speed))
    # Needs to be fairly fast to look like a siren
    delay = max(0.01, 0.1 / s)
    
    offset = 0
    
    while not stop.is_set():
        prev_auto = tree.auto_show
        tree.auto_show = False
        
        try:
            tree.color = (0, 0, 0)
            
            # Red Side: Branches 0, 1 (relative to offset)
            # Blue Side: Branches 4, 5 (relative to offset)
            
            red_branches = [(offset) % 8, (offset + 1) % 8]
            blue_branches = [(offset + 4) % 8, (offset + 5) % 8]
            
            # Set Red
            for b in red_branches:
                for l in range(3):
                    tree[l, b].color = (1.0, 0.0, 0.0)
            
            # Set Blue
            for b in blue_branches:
                for l in range(3):
                    tree[l, b].color = (0.0, 0.0, 1.0)
            
            # Star alternates
            if offset % 8 < 4:
                tree.star.color = (1.0, 0.0, 0.0)
            else:
                tree.star.color = (0.0, 0.0, 1.0)
                
            tree.show()
            
        finally:
            tree.auto_show = prev_auto
            
        # Rotate
        offset = (offset + 1) % 8
        sleep(delay)
