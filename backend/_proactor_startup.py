"""Auto-loaded by PYTHONSTARTUP in uvicorn reload worker processes.

Sets WindowsProactorEventLoopPolicy so asyncio.create_subprocess_exec()
works in the worker's event loop. Without this, the reloaded worker
falls back to SelectorEventLoop which raises NotImplementedError.
"""

import sys

if sys.platform == "win32":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
