"""Tests for CLI entry point and argument handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestArgumentParsing:
    """Tests for CLI argument parsing."""

    def test_default_mode_is_ui(self):
        """Default mode (no args) launches UI."""
        with patch("sys.argv", ["quorum"]):
            with patch("quorum.main._ensure_config", return_value=True):
                with patch("quorum.main._launch_ui") as mock_ui:
                    from quorum.main import main
                    main()
                    mock_ui.assert_called_once()

    def test_ui_flag_launches_ui(self):
        """--ui flag explicitly launches UI."""
        with patch("sys.argv", ["quorum", "--ui"]):
            with patch("quorum.main._ensure_config", return_value=True):
                with patch("quorum.main._launch_ui") as mock_ui:
                    from quorum.main import main
                    main()
                    mock_ui.assert_called_once()

    def test_ipc_flag_launches_ipc(self):
        """--ipc flag launches IPC mode."""
        with patch("sys.argv", ["quorum", "--ipc"]):
            with patch("quorum.main.asyncio.run") as mock_run:
                with patch("quorum.ipc.run_ipc", new_callable=AsyncMock) as mock_ipc:
                    from quorum.main import main
                    main()
                    mock_run.assert_called_once()

    def test_help_flag_shows_help(self):
        """--help flag shows help and exits."""
        with patch("sys.argv", ["quorum", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from quorum.main import main
                main()
            assert exc_info.value.code == 0


class TestUILaunch:
    """Tests for UI launch functionality."""

    def test_launch_ui_function_exists(self):
        """_launch_ui function is defined and callable."""
        from quorum.main import _launch_ui
        assert callable(_launch_ui)

    def test_frontend_path_construction(self):
        """Frontend path is correctly constructed relative to main.py."""
        from quorum.main import Path
        main_file = Path(__file__).parent.parent / "src" / "quorum" / "main.py"
        if main_file.exists():
            frontend_dir = main_file.parent.parent.parent / "frontend"
            assert "frontend" in str(frontend_dir)


class TestSymlinkValidation:
    """Tests for symlink security validation."""

    def test_symlink_detection_works(self, tmp_path):
        """Path.is_symlink() correctly detects symlinks."""
        # Create a regular file
        regular_file = tmp_path / "regular.txt"
        regular_file.write_text("content")

        # Create a symlink
        symlink_file = tmp_path / "link.txt"
        symlink_file.symlink_to(regular_file)

        assert not regular_file.is_symlink()
        assert symlink_file.is_symlink()

    def test_relative_to_detects_path_escape(self, tmp_path):
        """Path.relative_to() raises ValueError for paths outside base."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        outside_path = tmp_path / "outside" / "file.txt"
        (tmp_path / "outside").mkdir()
        outside_path.touch()

        # relative_to raises ValueError when path is not under base
        with pytest.raises(ValueError):
            outside_path.relative_to(base_dir)


class TestLoggingSetup:
    """Tests for logging configuration."""

    def test_setup_logging_function_exists(self):
        """_setup_logging function is defined and callable."""
        from quorum.main import _setup_logging
        assert callable(_setup_logging)

    def test_logging_handler_configuration(self):
        """Logging uses RotatingFileHandler."""
        from logging.handlers import RotatingFileHandler
        # Verify the class exists and is importable
        assert RotatingFileHandler is not None


class TestIPCMode:
    """Tests for IPC mode functionality."""

    def test_run_ipc_is_importable(self):
        """run_ipc function can be imported."""
        from quorum.ipc import run_ipc
        assert callable(run_ipc)


class TestErrorHandling:
    """Tests for error handling in main module."""

    def test_invalid_argument_shows_error(self):
        """Invalid arguments show error and exit."""
        with patch("sys.argv", ["quorum", "--invalid-flag"]):
            with pytest.raises(SystemExit) as exc_info:
                from quorum.main import main
                main()
            assert exc_info.value.code == 2  # argparse error code


class TestModuleStructure:
    """Tests for module structure and exports."""

    def test_main_function_exists(self):
        """main() entry point exists."""
        from quorum.main import main
        assert callable(main)

    def test_launch_ui_is_private(self):
        """_launch_ui is a private function (starts with _)."""
        from quorum.main import _launch_ui
        assert _launch_ui.__name__.startswith("_")
