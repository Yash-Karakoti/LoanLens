"""Start the same website locally or in a container."""

from __future__ import annotations

import argparse
import os

import uvicorn


def main() -> None:
    """Use loopback locally; containers explicitly set WEB_HOST and PORT."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("WEB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    options = parser.parse_args()
    uvicorn.run("web.server:app", host=options.host, port=options.port, access_log=False)


if __name__ == "__main__":
    main()
