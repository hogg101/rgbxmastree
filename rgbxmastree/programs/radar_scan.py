from __future__ import annotations

import colorsys
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def radar_scan(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    A rotating radar scanner beam.
    """
    # Speed handling
    s = max(0.001, float(speed))
    delay = max(0.01, 0.1 / s)
    
    current_branch = 0
    
    while not stop.is_set():
        prev_auto = tree.auto_show
        tree.auto_show = False
        
        try:
            # Fade everything by 30% each frame to create trails
            for pixel in tree:
                r, g, b = pixel.color
                pixel.color = (r * 0.7, g * 0.7, b * 0.7)
            
            # Draw the beam at current_branch
            # Beam color: Cyan/Green radar style
            beam_color = (0.0, 1.0, 0.5)
            
            for level in range(3):
                tree[level, current_branch].color = beam_color
            
            # Pulse star when beam hits 'North' (branch 0)
            if current_branch == 0:
                tree.star.color = (1.0, 0.0, 0.0) # Blip!
            
            tree.show()
            
        finally:
            tree.auto_show = prev_auto
        
        # Rotate
        current_branch = (current_branch + 1) % 8
        sleep(delay)
