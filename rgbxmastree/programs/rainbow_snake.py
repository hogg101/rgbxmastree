from __future__ import annotations

import colorsys
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def rainbow_snake(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    A rainbow snake that winds its way up the tree.
    """
    # Build the path of pixels: Spiral up 0-7 on each level, then Star
    # We pre-calculate the list of pixel objects for efficiency
    snake_path = []
    for level in range(3):
        for branch in range(8):
            snake_path.append(tree[level, branch])
    snake_path.append(tree.star)
    
    path_len = len(snake_path)
    snake_len = 8  # Length of the snake
    
    # Pre-calculate rainbow colors for the snake body
    # Head is full brightness, tail fades out? 
    # Let's just do full rainbow for now.
    snake_colors = []
    for i in range(snake_len):
        # Hue cycles through the spectrum
        hue = i / (snake_len - 1)
        # Convert HSV to RGB
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        snake_colors.append(rgb)
    
    # Speed handling
    s = max(0.001, float(speed))
    delay = max(0.01, 0.1 / s)
    
    head_pos = 0
    
    while not stop.is_set():
        prev_auto = tree.auto_show
        tree.auto_show = False
        
        try:
            # Turn off all pixels first
            tree.color = (0, 0, 0)
            
            # Draw the snake
            for i in range(snake_len):
                # Calculate position in path
                # We want the head at head_pos, tail behind it
                current_idx = head_pos - i
                
                if 0 <= current_idx < path_len:
                    pixel = snake_path[current_idx]
                    pixel.color = snake_colors[i]
            
            tree.show()
        finally:
            tree.auto_show = prev_auto
            
        # Move snake forward
        head_pos += 1
        # Loop around after the snake has fully left the tree
        if head_pos >= path_len + snake_len:
            head_pos = 0
            
        sleep(delay)
