from __future__ import annotations

from dataclasses import dataclass
from gettext import gettext as _
import os
import shlex
import shutil
from typing import Protocol


class CageCommandError(RuntimeError):
    """Raised when Cage launch arguments cannot be built safely."""


class CageLaunchConfig(Protocol):
    executable_path: str
    window_width: int
    window_height: int
    logical_width: int
    logical_height: int
    socket_name: str
    scale: int
    refresh_rate: int
    hide_titlebar: bool
    confine_pointer: bool


@dataclass(frozen=True)
class CageCommand:
    argv: tuple[str, ...]
    display_name: str

    @property
    def command_line(self) -> str:
        return shlex.join(self.argv)


def resolve_cage_executable(executable_path: str) -> str:
    """Resolve and validate the configured Cage executable before launch.

    The key mapper starts Cage without a shell, so an empty executable would
    shift the first option (for example ``-W``) into argv[0]. Validating here
    keeps subprocess errors tied to the real configuration problem.
    """
    expanded_path = os.path.expandvars(os.path.expanduser(executable_path.strip()))
    if not expanded_path:
        raise CageCommandError(
            _(
                "Cage is enabled, but the Cage executable path is empty. "
                "Open Key Mapping Settings and choose the Cage executable."
            )
        )

    if _looks_like_filesystem_path(expanded_path):
        if not os.path.exists(expanded_path):
            raise CageCommandError(
                _("Cage executable does not exist: {0}").format(expanded_path)
            )
        if not os.access(expanded_path, os.X_OK):
            raise CageCommandError(
                _("Cage executable is not executable: {0}").format(expanded_path)
            )
        return expanded_path

    resolved_path = shutil.which(expanded_path)
    if not resolved_path:
        raise CageCommandError(
            _("Cage executable was not found in PATH: {0}").format(expanded_path)
        )
    return resolved_path


def build_cage_command(config: CageLaunchConfig) -> CageCommand:
    executable_path = resolve_cage_executable(config.executable_path)
    argv = [
        executable_path,
        "-W",
        str(config.window_width),
        "-H",
        str(config.window_height),
        "-w",
        str(config.logical_width),
        "-h",
        str(config.logical_height),
        "-S",
        config.socket_name,
        "--scale",
        str(config.scale / 100),
        "--refresh-rate",
        str(config.refresh_rate),
    ]

    if config.hide_titlebar:
        argv.append("--hide-titlebar")
    if config.confine_pointer:
        argv.append("--confine-pointer")

    argv.extend(["--", "waydroid", "show-full-ui"])
    return CageCommand(argv=tuple(argv), display_name=config.socket_name)


def _looks_like_filesystem_path(executable_path: str) -> bool:
    return os.path.sep in executable_path or (
        os.path.altsep is not None and os.path.altsep in executable_path
    )
