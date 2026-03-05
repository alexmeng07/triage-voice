"""Convenience entry-point: ``python api_server.py``

Equivalent to:
    uvicorn app.api:app --reload --port 8000
"""

from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the triage-voice API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", default=True)
    args = parser.parse_args()

    uvicorn.run("app.api:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
