"""Development server launcher with Windows subprocess support.

On Windows, uvicorn's --reload flag spawns a worker process that uses
SelectorEventLoop, which does not support asyncio.create_subprocess_exec().
The Claude Agent SDK needs subprocess support to spawn the Claude Code CLI.

This script sets WindowsProactorEventLoopPolicy at the PROCESS level before
uvicorn creates its event loop, ensuring subprocess support works even with
--reload. It also passes the policy through PYTHONSTARTUP so the reloaded
worker process inherits it.

Usage:
    python run.py              # with --reload (default for dev)
    python run.py --no-reload  # without --reload
"""

import os
import sys

# Set ProactorEventLoop policy BEFORE any event loop is created.
# This must happen before uvicorn is imported.
if sys.platform == "win32":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # Ensure the worker subprocess also uses ProactorEventLoop by
    # injecting the policy into the child's Python startup.
    _startup_script = os.path.join(os.path.dirname(__file__), "_proactor_startup.py")
    if os.path.exists(_startup_script):
        os.environ.setdefault("PYTHONSTARTUP", _startup_script)

import uvicorn  # noqa: E402

if __name__ == "__main__":
    reload_mode = "--no-reload" not in sys.argv
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=reload_mode,
    )
