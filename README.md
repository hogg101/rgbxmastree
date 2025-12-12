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

## Low-level control (optional)

If you want to write your own programs, you can import the hardware driver:

```python
from rgbxmastree.hardware.tree import RGBXmasTree
from colorzero import Color

tree = RGBXmasTree()
tree.color = Color("red")
```

Built-in programs live in `rgbxmastree/programs/`.
