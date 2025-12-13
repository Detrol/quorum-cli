"""CLI entry point for Quorum."""

import argparse
import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path

# Suppress verbose logging from dependencies
logging.getLogger("httpx").setLevel(logging.WARNING)


def _setup_logging() -> None:
    """Configure logging to file for error tracking."""
    from logging.handlers import RotatingFileHandler

    # Use ~/.quorum/logs/ for both dev and pip install
    log_dir = Path.home() / ".quorum" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
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


def _ensure_config() -> bool:
    """Ensure ~/.quorum/.env exists. Returns True if config is ready."""
    config_dir = Path.home() / ".quorum"
    env_file = config_dir / ".env"

    # If .env exists (either in ~/.quorum/ or current dir), we're good
    if env_file.exists() or Path(".env").exists():
        return True

    # Create config directory
    config_dir.mkdir(parents=True, exist_ok=True)

    # Copy .env.example from package
    package_example = Path(__file__).parent / ".env.example"
    dest_example = config_dir / ".env.example"

    if package_example.exists() and not dest_example.exists():
        shutil.copy(package_example, dest_example)

    # Show setup message
    print()
    print("\033[33m╭─────────────────────────────────────────────────────╮\033[0m")
    print("\033[33m│\033[0m  \033[1mWelcome to Quorum!\033[0m                                \033[33m│\033[0m")
    print("\033[33m├─────────────────────────────────────────────────────┤\033[0m")
    print("\033[33m│\033[0m                                                     \033[33m│\033[0m")
    print("\033[33m│\033[0m  Configuration needed. Please set up your API keys:\033[33m│\033[0m")
    print("\033[33m│\033[0m                                                     \033[33m│\033[0m")
    print(f"\033[33m│\033[0m    \033[36mcp {dest_example} {env_file}\033[0m")
    print(f"\033[33m│\033[0m    \033[36mnano {env_file}\033[0m")
    print("\033[33m│\033[0m                                                     \033[33m│\033[0m")
    print("\033[33m│\033[0m  Add at least one API key, then run \033[32mquorum\033[0m again.  \033[33m│\033[0m")
    print("\033[33m│\033[0m                                                     \033[33m│\033[0m")
    print("\033[33m╰─────────────────────────────────────────────────────╯\033[0m")
    print()
    return False


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
        # Check config before launching UI
        if not _ensure_config():
            sys.exit(0)
        _launch_ui()


def _get_frontend_dir() -> Path | None:
    """Find frontend directory - works in both dev and pip install."""
    # 1. Bundled frontend (pip install)
    bundled = Path(__file__).parent / "_frontend"
    if (bundled / "index.js").exists():
        return bundled

    # 2. Dev: prefer built dist if available
    dev = Path(__file__).parent.parent.parent / "frontend"
    if dev.exists():
        if (dev / "dist" / "index.js").exists():
            return dev / "dist"
        return dev

    return None


def _launch_ui() -> None:
    """Launch the Ink-based UI."""
    import subprocess
    import threading
    import time

    # Check Node.js is installed
    if not shutil.which("node"):
        print("Error: Node.js is required. Install from https://nodejs.org")
        sys.exit(1)

    frontend_dir = _get_frontend_dir()
    if not frontend_dir:
        print("Frontend not found. Install with: pip install quorum-cli")
        sys.exit(1)

    # Determine how to run the frontend
    index_js = frontend_dir / "index.js"
    if index_js.exists():
        # Bundled or dev with built dist - run directly
        if index_js.is_symlink():
            print("Error: index.js is a symlink (security risk)")
            sys.exit(1)
        cmd = ["node", str(index_js)]
    else:
        # Dev mode without build - needs tsx
        if not (frontend_dir / "node_modules").exists():
            print("Run: cd frontend && npm install && npm run build")
            sys.exit(1)
        tsx_path = frontend_dir / "node_modules" / ".bin" / "tsx"
        if tsx_path.is_symlink():
            try:
                target = tsx_path.resolve()
                target.relative_to(frontend_dir / "node_modules")
            except ValueError:
                print("Error: tsx binary links outside node_modules (security risk)")
                sys.exit(1)
        cmd = [str(tsx_path), "src/index.tsx"]
        os.chdir(frontend_dir)

    # Tell Node where Python is (so frontend can spawn backend)
    os.environ["QUORUM_PYTHON"] = sys.executable

    # Signal file for spinner coordination
    signal_file = Path(f"/tmp/quorum-ready-{os.getpid()}")
    os.environ["QUORUM_SIGNAL_FILE"] = str(signal_file)

    # Animated spinner in background thread
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    stop_spinner = threading.Event()

    def spin():
        i = 0
        while not stop_spinner.is_set():
            frame = spinner_frames[i % len(spinner_frames)]
            print(f"\r\033[32m{frame} Starting Quorum...\033[0m", end="", flush=True)
            time.sleep(0.08)
            i += 1
        print("\r\033[K", end="", flush=True)

    spinner_thread = threading.Thread(target=spin, daemon=True)
    spinner_thread.start()

    # Run Node (subprocess so we can keep spinner alive)
    proc = subprocess.Popen(cmd)

    # Wait for signal file (frontend ready) or process exit
    while proc.poll() is None:
        if signal_file.exists():
            stop_spinner.set()
            signal_file.unlink(missing_ok=True)
            break
        time.sleep(0.05)

    # Stop spinner if process exited early
    stop_spinner.set()

    # Wait for Node to finish
    sys.exit(proc.wait())


if __name__ == "__main__":
    main()
