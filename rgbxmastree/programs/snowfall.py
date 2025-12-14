from __future__ import annotations

import random
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def snowfall(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Simulates snow falling from the top of the tree, with a twinkling star.
    """
    # Speed handling
    s = max(0.001, float(speed))
    # Snow falls somewhat slowly
    delay = max(0.05, 0.3 / s)
    
    while not stop.is_set():
        prev_auto = tree.auto_show
        tree.auto_show = False
        
        try:
            # Update Star (Random twinkle)
            if random.random() < 0.1:
                tree.star.color = (1.0, 1.0, 1.0)
            elif random.random() < 0.05:
                tree.star.color = (0.5, 0.5, 1.0) # Blue-ish tint
            else:
                # Fade star slightly instead of hard off
                r, g, b = tree.star.color
                tree.star.color = (max(0, r - 0.1), max(0, g - 0.1), max(0, b - 0.1))

            # Update Snow Layers
            # We iterate branches 0-7
            for b in range(8):
                # Move snow down: Level 1 -> Level 0
                # We add a slight fade or randomness to movement?
                # No, just shift down for clear effect.
                
                # Level 0 (Bottom) - takes from Level 1
                l1_color = tree[1, b].color
                # Dim it slightly as it hits bottom/ground
                tree[0, b].color = (l1_color[0] * 0.7, l1_color[1] * 0.7, l1_color[2] * 0.7)
                
                # Level 1 (Middle) - takes from Level 2
                l2_color = tree[2, b].color
                tree[1, b].color = l2_color
                
                # Level 2 (Top) - Spawns new snow
                # 15% chance of new flake
                if random.random() < 0.15:
                    # White with slight variance
                    intensity = random.uniform(0.8, 1.0)
                    tree[2, b].color = (intensity, intensity, intensity)
                else:
                    tree[2, b].color = (0, 0, 0)
                    
            tree.show()
            
        finally:
            tree.auto_show = prev_auto
            
        sleep(delay)
