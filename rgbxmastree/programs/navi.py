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
    Generate a bold, vibrant RGB color that is sufficiently different from the previous color.
    
    Colors are guaranteed to be bold by ensuring at least one component is near maximum
    and the color has high saturation (not too gray/muted).
    
    Args:
        previous_color: The previous fairy color, or None for the first color
        min_separation: Minimum color distance required (default 0.5)
    
    Returns:
        A new bold RGB tuple with values in 0.0-1.0 range
    """
    max_attempts = 50
    
    for _ in range(max_attempts):
        # Generate bold, vibrant color
        # Ensure at least one component is very high (0.9-1.0) for boldness
        # And ensure minimum saturation (not too gray)
        r = random.random()
        g = random.random()
        b = random.random()
        
        # Boost the highest component to near maximum for boldness
        max_component = max(r, g, b)
        if max_component < 0.7:
            # If nothing is bright enough, boost the highest one
            if r == max_component:
                r = random.uniform(0.85, 1.0)
            elif g == max_component:
                g = random.uniform(0.85, 1.0)
            else:
                b = random.uniform(0.85, 1.0)
        else:
            # Boost the max component even more
            if r == max_component:
                r = random.uniform(0.9, 1.0)
            elif g == max_component:
                g = random.uniform(0.9, 1.0)
            else:
                b = random.uniform(0.9, 1.0)
        
        # Ensure minimum saturation - at least one component should be significantly lower
        min_component = min(r, g, b)
        if (max(r, g, b) - min_component) < 0.3:
            # Too gray, boost contrast
            if r == max_component:
                b = random.uniform(0.0, 0.4)
                g = random.uniform(0.0, 0.5)
            elif g == max_component:
                r = random.uniform(0.0, 0.4)
                b = random.uniform(0.0, 0.5)
            else:
                r = random.uniform(0.0, 0.4)
                g = random.uniform(0.0, 0.5)
        
        new_color = (_clamp01(r), _clamp01(g), _clamp01(b))
        
        # If no previous color, return immediately
        if previous_color is None:
            return new_color
        
        # Check if color is sufficiently different
        distance = _color_distance(new_color, previous_color)
        if distance >= min_separation:
            return new_color
    
    # If we couldn't find a sufficiently different color, generate a bold one anyway
    r = random.random()
    g = random.random()
    b = random.random()
    max_idx = 0 if r >= g and r >= b else (1 if g >= b else 2)
    if max_idx == 0:
        r = random.uniform(0.9, 1.0)
        g = random.uniform(0.0, 0.5)
        b = random.uniform(0.0, 0.5)
    elif max_idx == 1:
        r = random.uniform(0.0, 0.5)
        g = random.uniform(0.9, 1.0)
        b = random.uniform(0.0, 0.5)
    else:
        r = random.uniform(0.0, 0.5)
        g = random.uniform(0.0, 0.5)
        b = random.uniform(0.9, 1.0)
    return (_clamp01(r), _clamp01(g), _clamp01(b))


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
    # Lower fade rate = slower, more visible fade
    # Scale with speed but keep it gentle for visible trail
    base_fade_rate = 0.08  # 8% per frame - visible fade
    fade_rate = _clamp01(base_fade_rate * (1.0 + (s / 30.0)))  # Scale with speed, but more gently
    
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
                # First, fade all body pixels towards warm white
                # (current pixel will be overwritten with fairy color below)
                for px in body_pixels:
                    current_color = pixel_colors.get(px, warm_white)
                    # Interpolate towards warm white
                    faded_r = _lerp(current_color[0], warm_white[0], fade_rate)
                    faded_g = _lerp(current_color[1], warm_white[1], fade_rate)
                    faded_b = _lerp(current_color[2], warm_white[2], fade_rate)
                    faded_color = (_clamp01(faded_r), _clamp01(faded_g), _clamp01(faded_b))
                    
                    # Update pixel color
                    px.color = faded_color
                    pixel_colors[px] = faded_color
                
                # Then set current pixel to fairy color (overwrites the fade for this pixel)
                # This creates the trail effect
                if pixel is not star:  # Only update pixel_colors for body pixels
                    pixel.color = fairy_color
                    pixel_colors[pixel] = fairy_color
                else:
                    # Star keeps its fairy color and doesn't fade
                    pixel.color = fairy_color
                
            finally:
                tree.auto_show = prev_auto
                tree.show()
            
            sleep(delay)
        
        # Longer pause before next fairy starts - allows trail to fade and star color to be visible
        # Break into small chunks and check stop event to allow immediate exit
        pause_duration = max(5.0, delay * 50)  # At least 5 seconds, or 50x the normal delay
        chunk_size = 0.1  # Check stop event every 100ms
        chunks = int(pause_duration / chunk_size)
        for _ in range(chunks):
            if stop.is_set():
                return
            sleep(chunk_size)
