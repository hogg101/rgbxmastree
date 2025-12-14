from __future__ import annotations

import random
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def matrix_rain(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Matrix-style digital rain effect. Green code falling down.
    """
    # Speed handling
    s = max(0.001, float(speed))
    delay = max(0.02, 0.15 / s)
    
    # State for each column (branch): -1 means inactive, 0-2 means head position
    # Actually, let's track head position for each of the 8 branches.
    # float position allows for sub-pixel movement speed differences? 
    # Let's keep it simple: integer positions.
    # 3 is above top, 2 is top, 1 is mid, 0 is bottom, -1 is done.
    
    # Let's manage drops. A drop is active on a branch.
    # branches[b] = position (3 down to -1)
    # We initiate drops randomly.
    
    branch_drops = [-1] * 8
    
    # Colors
    head_color = (0.8, 1.0, 0.8) # Bright white-green
    tail_color = (0.0, 0.8, 0.0) # Matrix Green
    fade_color = (0.0, 0.2, 0.0) # Dim Green
    
    while not stop.is_set():
        prev_auto = tree.auto_show
        tree.auto_show = False
        
        try:
            # Randomly start new drops
            if random.random() < 0.3:
                # Pick a random branch that isn't busy (active <= 0 means near bottom/done)
                # actually we can have multiple drops per column but it's short.
                # simpler: pick a random branch, if it's inactive (-1), start it at 3 (above top)
                candidates = [b for b, pos in enumerate(branch_drops) if pos == -1]
                if candidates:
                    b = random.choice(candidates)
                    branch_drops[b] = 3
            
            # Draw
            tree.color = (0, 0, 0) # Clear
            
            for b in range(8):
                pos = branch_drops[b]
                
                if pos > -1:
                    # Draw Drop
                    
                    # Head
                    if 0 <= pos <= 2:
                        tree[pos, b].color = head_color
                    
                    # Tail 1
                    if 0 <= pos + 1 <= 2:
                        tree[pos + 1, b].color = tail_color
                        
                    # Tail 2 (fading)
                    if 0 <= pos + 2 <= 2:
                        tree[pos + 2, b].color = fade_color

                    # Move down
                    # To make it fall, we decrement. 
                    # But the loop runs fast, so we need to control fall speed.
                    # Or we just update every frame.
                    
                    # Wait, if we decrement every frame, it might be too fast compared to spawn rate?
                    # The delay controls the frame rate.
                    branch_drops[b] -= 1
                    
                    # If head went below -2 (tail is gone), reset to -1
                    if branch_drops[b] < -3:
                        branch_drops[b] = -1
            
            # Star: occasional glitch
            if random.random() < 0.05:
                tree.star.color = head_color
            else:
                tree.star.color = (0, 0, 0)
                
            tree.show()
            
        finally:
            tree.auto_show = prev_auto
            
        sleep(delay)
