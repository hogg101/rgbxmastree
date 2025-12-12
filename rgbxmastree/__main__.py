from __future__ import annotations

import argparse
import os

from rgbxmastree.web.app import create_app


def main() -> int:
    parser = argparse.ArgumentParser(prog="rgbxmastree")
    parser.add_argument("--host", default=os.environ.get("RGBXMASTREE_HOST", "0.0.0.0"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("RGBXMASTREE_PORT", "8080")),
    )
    parser.add_argument(
        "--config",
        default=os.environ.get("RGBXMASTREE_CONFIG", "/var/lib/rgbxmastree/config.json"),
        help="Path to config JSON",
    )
    args = parser.parse_args()

    app = create_app(config_path=args.config)
    # Use waitress for production-ish runs, fallback to Flask dev server.
    try:
        from waitress import serve

        serve(app, host=args.host, port=args.port)
    except Exception:
        app.run(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


