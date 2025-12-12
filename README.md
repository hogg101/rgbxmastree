## rgbxmastree (fork)

This fork turns the original examples into a small always-on project for the **3D RGB Xmas Tree**:

- A **LAN web UI** (iPhone-friendly)
- A **timer** (daily window + “on for X” countdown override)
- A **systemd service** so it starts on boot

## Getting started

### Quick start (dev)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the web UI on the Pi:

```bash
python -m rgbxmastree --host 0.0.0.0 --port 8080
```

Open from your phone (same Wi‑Fi): `http://xmaspi.local:8080`

### Raspberry Pi OS setup (recommended)

Use the setup script (added in this fork) to install and configure the systemd service.

- From the repo directory on your Pi:

```bash
chmod +x scripts/setup_pi.sh
sudo ./scripts/setup_pi.sh
```

- Then open: `http://xmaspi.local:8080`

- Service status:

```bash
sudo systemctl status rgbxmastree.service --no-pager
```

## Original driver + examples

The original low-level driver lives in `tree.py` and the examples are in `examples/`.

In this fork, the driver is also available as `rgbxmastree.hardware.tree.RGBXmasTree` and the animations are in `rgbxmastree.programs`.

## Change the colour

You can set the colour of all the LEDs together using RGB values (all 0-1):

```python
from tree import RGBXmasTree

tree = RGBXmasTree()

tree.color = (1, 0, 0)
```

Alternatively you can use the `colorzero` library:

```python
from tree import RGBXmasTree
from colorzero import Color

tree = RGBXmasTree()

tree.color = Color('red')
```

You can write a loop to repeatedly cycle through red, green and blue:

```python
from tree import RGBXmasTree
from time import sleep

tree = RGBXmasTree()

colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]

for color in colors:
    tree.color = color
    sleep(1)
```

## Individual control

You can also control each LED individually, for example turn each one red, one
at a time:

```python
from tree import RGBXmasTree
from time import sleep

tree = RGBXmasTree()

for pixel in tree:
    pixel.color = (1, 0, 0)
    sleep(1)
```

To control a specific pixel, you can access it by its index number (0-24):

```python
tree[0].color = (0, 1, 0)
```

## Change the brightness

You can change the brightness from 0 to 1 - the default is 0.5. You can set this
when initialising your tree:

```python
from tree import RGBXmasTree

tree = RGBXmasTree(brightness=0.1)
```

Alternatively, you can change it after initialisation:

```python
from tree import RGBXmasTree

tree = RGBXmasTree()

tree.brightness = 0.1
```

You'll find that 1 is _extremely bright_ and even 0.1 is plenty bright enough if
the tree is on your desk :)

## Examples

## RGB cycle

Cycle through red, green and blue, changing all pixels together

- [rgb.py](examples/rgb.py)

### One-by-one

Cycle through red, green and blue, changing pixel-by-pixel

- [onebyone.py](examples/onebyone.py)

### Hue cycle

Cycle through hues forever

- [huecycle.py](examples/huecycle.py)

### Random sparkles

Randomly sparkle all the pixels

- [randomsparkles.py](examples/randomsparkles.py)
