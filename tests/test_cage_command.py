from __future__ import annotations

from dataclasses import dataclass
import os
import shlex

import pytest

from waydroid_helper.cage_command import (
    CageCommandError,
    build_cage_command,
    resolve_cage_executable,
)


@dataclass
class FakeCageConfig:
    executable_path: str
    window_width: int = 1920
    window_height: int = 1080
    logical_width: int = 1920
    logical_height: int = 1080
    socket_name: str = "waydroid-test"
    scale: int = 125
    refresh_rate: int = 144
    hide_titlebar: bool = False
    confine_pointer: bool = False


def test_empty_cage_executable_path_is_rejected():
    with pytest.raises(CageCommandError, match="executable path is empty"):
        resolve_cage_executable("   ")


def test_cage_command_uses_validated_executable_as_argv0(tmp_path):
    executable = tmp_path / "cage"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)

    command = build_cage_command(
        FakeCageConfig(
            executable_path=str(executable),
            hide_titlebar=True,
            confine_pointer=True,
        )
    )

    assert command.argv[0] == str(executable)
    assert command.argv[1:5] == ("-W", "1920", "-H", "1080")
    assert "--hide-titlebar" in command.argv
    assert "--confine-pointer" in command.argv
    assert command.argv[-3:] == ("--", "waydroid", "show-full-ui")


def test_cage_command_line_round_trips_paths_with_spaces(tmp_path):
    executable_dir = tmp_path / "with space"
    executable_dir.mkdir()
    executable = executable_dir / "cage"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)

    command = build_cage_command(FakeCageConfig(executable_path=str(executable)))

    assert shlex.split(command.command_line) == list(command.argv)


def test_cage_executable_can_be_resolved_from_path(tmp_path, monkeypatch):
    executable = tmp_path / "cage"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    assert resolve_cage_executable("cage") == str(executable)
