from __future__ import annotations

import math
import random
from threading import Event
from time import sleep

from rgbxmastree.hardware.tree import RGBXmasTree


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _warm_white_rgb() -> tuple[float, float, float]:
    """
    Return a warm white RGB color that avoids green tint.
    
    Many RGB LEDs skew green in the "white" region. This palette intentionally
    keeps green lower to ensure warm white doesn't look green.
    """
    # Start with warmer white RGB values (more red/orange, less blue)
    r = 1.0
    g = 0.80
    b = 0.35
    
    # LED correction: tame green a bit (same as candles.py).
    g *= 0.82
    g = g**1.10
    
    return (_clamp01(r), _clamp01(g), _clamp01(b))


def _color_distance(c1: tuple[float, float, float], c2: tuple[float, float, float]) -> float:
    """
    Calculate Euclidean distance between two RGB colors.
    """
    r1, g1, b1 = c1
    r2, g2, b2 = c2
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def _generate_fairy_color(previous_color: tuple[float, float, float] | None, min_separation: float = 0.5) -> tuple[float, float, float]:
    """
    Generate a random RGB color that is sufficiently different from the previous color.
    
    Args:
        previous_color: The previous fairy color, or None for the first color
        min_separation: Minimum color distance required (default 0.5)
    
    Returns:
        A new RGB tuple with values in 0.0-1.0 range
    """
    max_attempts = 50
    
    for _ in range(max_attempts):
        # Generate random RGB color
        new_color = (random.random(), random.random(), random.random())
        
        # If no previous color, return immediately
        if previous_color is None:
            return new_color
        
        # Check if color is sufficiently different
        distance = _color_distance(new_color, previous_color)
        if distance >= min_separation:
            return new_color
    
    # If we couldn't find a sufficiently different color, return a random one anyway
    return (random.random(), random.random(), random.random())


def _generate_corkscrew_path(tree: RGBXmasTree) -> list:
    """
    Generate the corkscrew path from bottom to top.
    
    Returns:
        List of pixel references in order: level 0 (branches 0-7), level 1 (branches 0-7),
        level 2 (branches 0-7), then star.
    """
    path = []
    
    # Level 0: branches 0-7 (bottom level)
    for branch in range(8):
        path.append(tree[0, branch])
    
    # Level 1: branches 0-7 (middle level)
    for branch in range(8):
        path.append(tree[1, branch])
    
    # Level 2: branches 0-7 (top level)
    for branch in range(8):
        path.append(tree[2, branch])
    
    # Star
    path.append(tree.star)
    
    return path


def navi(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Navi fairy effect: a colored fairy moves up the tree in a corkscrew pattern,
    leaving a fading trail. The tree maintains a warm white baseline.
    
    When the fairy reaches the star, it changes the star color to match the fairy.
    Each fairy uses a different color that's visually distinct from the previous one.
    
    The only tempo control is the supplied `speed` knob from the web UI/controller.
    """
    star = tree.star
    body_pixels = [px for px in tree if px is not star]
    
    # speed is expected to be in a wide range (e.g. 0.1..200).
    s = max(0.001, float(speed))
    # Update cadence: very slow at low end (seconds), extremely fast at high end (milliseconds).
    delay = max(0.001, 1.0 / s)
    
    # Generate corkscrew path
    path = _generate_corkscrew_path(tree)
    
    # Warm white baseline color
    warm_white = _warm_white_rgb()
    
    # Initialize all pixels to warm white
    prev_auto = tree.auto_show
    tree.auto_show = False
    try:
        for px in tree:
            px.color = warm_white
    finally:
        tree.auto_show = prev_auto
        tree.show()
    
    # Track pixel colors for fading trail
    pixel_colors: dict = {}
    for px in tree:
        pixel_colors[px] = warm_white
    
    # Previous fairy color for ensuring separation
    previous_fairy_color: tuple[float, float, float] | None = None
    
    # Trail fade rate (how quickly pixels fade back to warm white)
    # Use a smaller base rate for smoother fading
    # Higher speed = slightly faster fade, but keep it gentle
    base_fade_rate = 0.02  # 2% per frame
    fade_rate = _clamp01(base_fade_rate * (1.0 + (s / 50.0)))  # Scale with speed but cap it
    
    while not stop.is_set():
        # Generate new fairy color
        fairy_color = _generate_fairy_color(previous_fairy_color)
        previous_fairy_color = fairy_color
        
        # Traverse the corkscrew path
        for pixel in path:
            if stop.is_set():
                return
            
            # Batch update all pixels
            prev_auto = tree.auto_show
            tree.auto_show = False
            try:
                # Fade body pixels towards warm white (exclude star and current pixel)
                # Star keeps its fairy color, current pixel will be set to fairy color below
                for px in body_pixels:
                    # Skip the current pixel - it will be set to fairy color
                    if px is pixel:
                        continue
                    
                    current_color = pixel_colors.get(px, warm_white)
                    # Interpolate towards warm white
                    faded_r = _lerp(current_color[0], warm_white[0], fade_rate)
                    faded_g = _lerp(current_color[1], warm_white[1], fade_rate)
                    faded_b = _lerp(current_color[2], warm_white[2], fade_rate)
                    faded_color = (_clamp01(faded_r), _clamp01(faded_g), _clamp01(faded_b))
                    
                    # Update pixel color
                    px.color = faded_color
                    pixel_colors[px] = faded_color
                
                # Set current pixel to fairy color (this creates the trail)
                pixel.color = fairy_color
                pixel_colors[pixel] = fairy_color
                
                # If current pixel is the star, it keeps its fairy color (don't fade it)
                # Star color persists until next fairy reaches it
                
            finally:
                tree.auto_show = prev_auto
                tree.show()
            
            sleep(delay)
        
        # When fairy reaches star, star color is already set to fairy color
        # (it was set in the loop above)
        
        # Brief pause before next fairy starts
        sleep(delay * 2)
