from __future__ import annotations

from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def candy_cane(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Rotating red and white candy cane stripes.
    """
    # Speed handling
    s = max(0.001, float(speed))
    delay = max(0.05, 0.2 / s)
    
    offset = 0
    
    while not stop.is_set():
        prev_auto = tree.auto_show
        tree.auto_show = False
        
        try:
            for level in range(3):
                for branch in range(8):
                    # Create diagonal stripes by adding level to branch
                    # This makes the pattern spiral up the tree
                    idx = branch + level + offset
                    
                    if idx % 2 == 0:
                        tree[level, branch].color = (1.0, 0.0, 0.0) # Red
                    else:
                        tree[level, branch].color = (1.0, 1.0, 1.0) # White
            
            # Star spins too
            if offset % 2 == 0:
                tree.star.color = (1.0, 0.0, 0.0)
            else:
                tree.star.color = (1.0, 1.0, 1.0)
                
            tree.show()
            
        finally:
            tree.auto_show = prev_auto
            
        offset += 1
        sleep(delay)
