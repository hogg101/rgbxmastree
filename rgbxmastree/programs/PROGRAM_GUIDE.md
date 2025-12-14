# RGB Xmas Tree Program Guide

This guide explains how to write programs for the RGB Xmas Tree.

## Program Structure

All programs must follow this function signature:

```python
def your_program(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Your program description.
    
    The only tempo control is the supplied `speed` knob from the web UI/controller.
    """
    # Your program code here
```

### Parameters

- `tree: RGBXmasTree` - The tree hardware driver instance
- `stop: Event` - Threading event that signals when the program should stop
- `speed: float` - Speed control from the web UI (typically 0.1-200, default 1.0)

## Tree Structure

The tree has:
- **3 levels** (0-2, bottom to top)
- **8 branches** per level (0-7, arranged in a circle)
- **1 star** at the top

### Accessing Pixels

```python
# Access by level and branch
tree[0, 0]  # Bottom level, first branch
tree[1, 3]  # Middle level, fourth branch
tree[2, 7]  # Top level, last branch

# Access the star
tree.star

# Iterate all pixels
for pixel in tree:
    pixel.color = (1.0, 0.0, 0.0)  # Red

# Get body pixels (everything except star)
star = tree.star
body_pixels = [px for px in tree if px is not star]
```

### Setting Pixel Colors

Colors are RGB tuples with values in 0.0-1.0 range:

```python
# Set a single pixel
pixel.color = (1.0, 0.0, 0.0)  # Red
pixel.color = (0.0, 1.0, 0.0)  # Green
pixel.color = (0.0, 0.0, 1.0)  # Blue

# Set all pixels at once
tree.color = (1.0, 1.0, 1.0)  # White

# Using colorzero Color objects
from colorzero import Color
pixel.color = Color("red")
pixel.color = Color("yellow")
```

## Speed Handling

Always handle speed like this:

```python
# speed is expected to be in a wide range (e.g. 0.1..200).
s = max(0.001, float(speed))
# Update cadence: very slow at low end (seconds), extremely fast at high end (milliseconds).
delay = max(0.001, 1.0 / s)
```

Then use `delay` in your `sleep()` calls:

```python
sleep(delay)
```

## Stop Event Handling

**Critical**: Programs must check `stop.is_set()` frequently, especially during long sleeps.

```python
while not stop.is_set():
    # Your main loop
    
    for item in collection:
        if stop.is_set():
            return  # Exit immediately
        
        # Do work
        sleep(delay)
    
    # For long pauses, break into chunks
    pause_duration = 5.0
    chunk_size = 0.1  # Check every 100ms
    chunks = int(pause_duration / chunk_size)
    for _ in range(chunks):
        if stop.is_set():
            return
        sleep(chunk_size)
```

**Important**: Programs should return immediately when `stop.is_set()` is True. No cleanup is needed - the new program will immediately overwrite pixels.

## Batching Updates

For better performance when updating multiple pixels, use batched updates:

```python
prev_auto = tree.auto_show
tree.auto_show = False
try:
    # Update multiple pixels
    for pixel in pixels:
        pixel.color = some_color
    tree.star.color = star_color
finally:
    tree.auto_show = prev_auto
    tree.show()  # Display all changes at once
```

This pattern ensures:
1. Updates are batched together
2. `tree.show()` is always called even if an exception occurs
3. The original `auto_show` setting is restored

## Helper Functions

Common helper functions used across programs:

```python
def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * t

def _clamp01(x: float) -> float:
    """Clamp value to 0.0-1.0 range."""
    return max(0.0, min(1.0, x))
```

## Example: Simple Program

```python
from __future__ import annotations

from threading import Event
from time import sleep

from colorzero import Color

from rgbxmastree.hardware.tree import RGBXmasTree


def simple_example(tree: RGBXmasTree, stop: Event, speed: float = 1.0) -> None:
    """
    Simple example that cycles through colors on all pixels.
    """
    colors = [Color("red"), Color("green"), Color("blue")]
    
    # Speed handling
    s = max(0.001, float(speed))
    delay = max(0.01, 1.0 / max(s, 0.01))
    
    while not stop.is_set():
        for c in colors:
            if stop.is_set():
                return
            tree.color = c
            sleep(delay)
```

## Example: Complex Program (Candles Pattern)

See `candles.py` for a more complex example that:
- Uses batched updates
- Separates star and body pixels
- Implements smooth color transitions
- Handles speed properly
- Checks stop events frequently

## Registering Your Program

1. Create your program file in `rgbxmastree/programs/`
2. Import it in `rgbxmastree/programs/__init__.py`:

```python
from rgbxmastree.programs.your_program import your_program
```

3. Add it to the `PROGRAMS` dictionary:

```python
PROGRAMS: dict[str, ProgramSpec] = {
    # ... existing programs ...
    "your_program": ProgramSpec(
        id="your_program",
        name="Your Program Name",
        runner=your_program,
        default_speed=1.0,
    ),
}
```

## Best Practices

1. **Always check `stop.is_set()`** before long operations or sleeps
2. **Use batched updates** when updating multiple pixels
3. **Handle speed properly** using the standard pattern
4. **Keep it simple** - no cleanup needed, just return when stopped
5. **Break long sleeps into chunks** to check stop events frequently
6. **Use descriptive docstrings** explaining what your program does
7. **Follow existing patterns** - look at `candles.py` for a good example

## Common Pitfalls

1. **Forgetting to check stop events** - causes programs to not exit immediately
2. **Long sleeps without checking stop** - makes program switching slow
3. **Not batching updates** - causes flickering and poor performance
4. **Incorrect speed handling** - makes programs unresponsive to speed changes
5. **Trying to clean up on exit** - unnecessary, new program overwrites immediately

## Testing

Test your program by:
1. Running it through the web UI
2. Switching between programs to ensure clean transitions
3. Testing at different speed values
4. Verifying it stops immediately when switched
