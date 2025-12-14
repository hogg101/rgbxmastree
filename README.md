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

### Updating on the Pi

For normal code updates (no dependency changes):

```bash
cd /path/to/your/rgbxmastree/checkout
git pull
chmod +x scripts/update_pi.sh
sudo ./scripts/update_pi.sh
```

This syncs your checkout into `/opt/rgbxmastree` and restarts `rgbxmastree.service` (it does **not** run `apt` or reinstall Python deps).

Re-run `sudo ./scripts/setup_pi.sh` when:

- it’s a first-time install (no `/opt/rgbxmastree` yet)
- `requirements.txt` changed and you need new Python dependencies

## Low-level control (optional)

If you want to write your own programs, you can import the hardware driver:

```python
from rgbxmastree.hardware.tree import RGBXmasTree
from colorzero import Color

tree = RGBXmasTree()
tree.color = Color("red")
```

### Pixel mapping (`level` / `branch` / `star`)

The tree body is addressed as **3 levels × 8 branches**:

- `level`: `0..2` (0 is the bottom level)
- `branch`: `0..7` (around the tree)
- `tree.star`: the star pixel

If you orient the tree so the Raspberry Pi is facing you, `branch=0` starts at the “front” and counts around.

Example:

```python
from rgbxmastree.hardware.tree import RGBXmasTree
from colorzero import Color

tree = RGBXmasTree()
tree[0, 0].color = Color("green")  # bottom/front
tree.star.color = Color("yellow")
```

### Batching updates (`show()` / `auto_show`)

By default, writes show immediately (`auto_show=True`). For faster multi-pixel updates, batch changes and call `show()` once:

```python
tree.auto_show = False
for level in range(3):
    for branch in range(8):
        tree[level, branch].color = (0.0, 0.0, 1.0)
tree.star.color = (1.0, 1.0, 1.0)
tree.show()
```

### Brightness (`body_brightness` / `star_brightness`)

Brightness is exposed as APA102 “global brightness” **ints** `0..31`:

```python
tree.body_brightness = 8
tree.star_brightness = 2
```

Built-in programs live in `rgbxmastree/programs/`.
