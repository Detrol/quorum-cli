#!/usr/bin/env python3
"""
Minimal Python client for Quorum IPC.

Demonstrates how to connect to Quorum's JSON-RPC backend and run a discussion.

Usage:
    python examples/python_ipc_client.py
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path


class QuorumClient:
    """Simple async client for Quorum IPC."""

    def __init__(self):
        self.process = None
        self.request_id = 0
        self.pending_requests = {}
        self.reader_task = None

    async def connect(self):
        """Start the Quorum backend process."""
        # Find the project root (where pyproject.toml is)
        project_root = Path(__file__).parent.parent

        # Start the backend with --ipc flag
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "quorum", "--ipc",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root,
        )

        # Start background reader
        self.reader_task = asyncio.create_task(self._read_loop())

        # Wait for ready event
        print("Waiting for backend to be ready...")
        await self._wait_for_ready()
        print("Backend ready!")

    async def _wait_for_ready(self):
        """Wait for the ready event."""
        while True:
            line = await self.process.stdout.readline()
            if not line:
                raise RuntimeError("Backend closed unexpectedly")

            data = json.loads(line)
            if data.get("method") == "ready":
                print(f"  Protocol version: {data['params'].get('protocol_version')}")
                return

    async def _read_loop(self):
        """Background task to read responses and events."""
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break

            data = json.loads(line)

            # Check if it's a response to a pending request
            if "id" in data and data["id"] in self.pending_requests:
                future = self.pending_requests.pop(data["id"])
                if "error" in data:
                    future.set_exception(RuntimeError(data["error"]["message"]))
                else:
                    future.set_result(data.get("result"))
            else:
                # It's an event
                self._handle_event(data)

    def _handle_event(self, event):
        """Handle incoming events."""
        method = event.get("method", "unknown")
        params = event.get("params", {})

        if method == "phase_start":
            print(f"\n=== {params.get('message')} ===")

        elif method == "thinking":
            print(f"  [{params.get('model')}] thinking...")

        elif method == "independent_answer":
            print(f"\n[{params.get('source')}]")
            print(f"  {params.get('content', '')[:200]}...")

        elif method == "critique":
            print(f"\n[{params.get('source')}] Critique:")
            print(f"  Agreements: {params.get('agreements', '')[:100]}...")

        elif method == "chat_message":
            role = params.get("role", "")
            source = params.get("source")
            print(f"\n[{source}] {f'({role}) ' if role else ''}")
            print(f"  {params.get('content', '')[:200]}...")

        elif method == "final_position":
            print(f"\n[{params.get('source')}] Final Position ({params.get('confidence')}):")
            print(f"  {params.get('position', '')[:200]}...")

        elif method == "synthesis":
            print(f"\n=== SYNTHESIS ({params.get('consensus')}) ===")
            print(f"Synthesizer: {params.get('synthesizer_model')}")
            print(f"\n{params.get('synthesis', '')[:500]}...")

        elif method == "discussion_complete":
            print(f"\nDiscussion complete! ({params.get('messages_count')} messages)")

        elif method == "phase_complete":
            print(f"\n[Phase {params.get('completed_phase')} complete, press Enter to continue]")
            # In a real client, you'd wait for user input and send resume_discussion

        elif method == "discussion_error":
            print(f"\nERROR: {params.get('error')}")

    async def request(self, method, params=None):
        """Send a JSON-RPC request and wait for response."""
        self.request_id += 1
        request_id = self.request_id

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }

        # Create future for response
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[request_id] = future

        # Send request
        line = json.dumps(request) + "\n"
        self.process.stdin.write(line.encode())
        await self.process.stdin.drain()

        # Wait for response
        return await future

    async def close(self):
        """Close the connection."""
        if self.process:
            self.process.stdin.close()
            await self.process.wait()
        if self.reader_task:
            self.reader_task.cancel()


async def main():
    """Example: List models and run a simple discussion."""
    client = QuorumClient()

    try:
        # Connect to backend
        await client.connect()

        # Initialize
        result = await client.request("initialize", {"protocol_version": "1.0.0"})
        print(f"Initialized: {result['name']} v{result['version']}")
        print(f"Providers: {', '.join(result['providers'])}")

        # List available models
        result = await client.request("list_models")
        print("\nAvailable models:")
        for provider, models in result["models"].items():
            print(f"  {provider}:")
            for model in models:
                validated = "(validated)" if model["id"] in result.get("validated", []) else ""
                print(f"    - {model['id']} {validated}")

        # Get user settings
        settings = await client.request("get_user_settings")
        selected = settings.get("selected_models", [])

        if len(selected) < 2:
            print("\nNot enough models selected. Please run Quorum UI first to select models.")
            return

        print(f"\nSelected models: {selected}")

        # Run a discussion
        print("\n" + "=" * 60)
        print("Starting discussion...")
        print("=" * 60)

        # Note: This will emit events handled by _handle_event
        result = await client.request("run_discussion", {
            "question": "What is 2+2?",
            "model_ids": selected[:2],  # Use first 2 selected models
            "options": {
                "method": "standard",
                "max_turns": 2,
            }
        })

        print(f"\nDiscussion result: {result}")

    except Exception as e:
        print(f"Error: {e}")
        raise

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
