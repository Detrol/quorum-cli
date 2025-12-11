"""CLI entry point for Quorum."""

import argparse
import asyncio
import logging
import os
import sys
import warnings
from pathlib import Path

# Suppress AutoGen's verbose logging
logging.getLogger("autogen_core").setLevel(logging.CRITICAL)
logging.getLogger("autogen_agentchat").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.WARNING)


def _setup_logging() -> None:
    """Configure logging to file for error tracking."""
    from logging.handlers import RotatingFileHandler

    # Use logs/ directory in project root
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "quorum.log"

    # Rotating file handler: 1MB max, keep 3 backups
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,  # 1 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Add handler to quorum logger
    quorum_logger = logging.getLogger("quorum")
    quorum_logger.setLevel(logging.WARNING)
    quorum_logger.addHandler(file_handler)

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="autogen_ext")


def main() -> None:
    """Start Quorum - UI, REPL, or IPC mode."""
    _setup_logging()

    parser = argparse.ArgumentParser(
        description="Quorum: Multi-agent consensus system"
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Run the modern Ink-based terminal UI"
    )
    parser.add_argument(
        "--ipc",
        action="store_true",
        help="Run in IPC mode (JSON-RPC over stdin/stdout)"
    )
    args = parser.parse_args()

    if args.ipc:
        from .ipc import run_ipc
        asyncio.run(run_ipc())
    else:
        _launch_ui()


def _launch_ui() -> None:
    """Launch the Ink-based UI."""
    import threading
    import time

    frontend_dir = Path(__file__).parent.parent.parent / "frontend"

    if not frontend_dir.exists():
        print("Frontend not found. Run: cd frontend && npm install")
        sys.exit(1)

    if not (frontend_dir / "node_modules").exists():
        print("Frontend dependencies not installed. Run: cd frontend && npm install")
        sys.exit(1)

    # Use compiled JS if available (much faster), otherwise fall back to tsx
    dist_index = frontend_dir / "dist" / "index.js"
    if dist_index.exists():
        # Security: Validate dist/index.js is not a symlink (prevent path traversal)
        if dist_index.is_symlink():
            print("Error: dist/index.js is a symlink (security risk)")
            sys.exit(1)
        cmd = ["node", str(dist_index)]
    else:
        tsx_path = frontend_dir / "node_modules" / ".bin" / "tsx"
        # Security: tsx is normally a symlink - validate it points inside node_modules
        if tsx_path.is_symlink():
            try:
                target = tsx_path.resolve()
                target.relative_to(frontend_dir / "node_modules")
            except ValueError:
                print("Error: tsx binary links outside node_modules (security risk)")
                sys.exit(1)
        cmd = [str(tsx_path), "src/index.tsx"]

    os.chdir(frontend_dir)

    # Simple spinner - runs until we exec into node
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    stop_spinner = threading.Event()

    def spin():
        i = 0
        while not stop_spinner.is_set():
            frame = spinner_frames[i % len(spinner_frames)]
            print(f"\r\033[32m{frame} Starting Quorum...\033[0m", end="", flush=True)
            time.sleep(0.08)
            i += 1

    spinner_thread = threading.Thread(target=spin, daemon=True)
    spinner_thread.start()

    # Replace current process with node (faster, no subprocess overhead)
    # Clear spinner first
    time.sleep(0.2)  # Brief spinner display
    stop_spinner.set()
    print("\r\033[K", end="", flush=True)

    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    main()
