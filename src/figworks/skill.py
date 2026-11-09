"""Install the bundled, harness-independent authoring skill.

Run ``python -m figworks.skill install DESTINATION`` to copy the complete
bundle, or ``python -m figworks.skill path`` to locate it for development.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Sequence
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path


def _bundle() -> Traversable:
    return files("figworks").joinpath("_skills", "figworks")


def path() -> Path:
    """Return the installed bundle's directory for direct use or editable links."""
    bundle = _bundle()
    if not isinstance(bundle, Path):
        raise ValueError("The skill is not on the filesystem; use 'install' to extract it")
    return bundle.resolve()


def _contents(bundle: Traversable, relative: Path = Path()) -> Iterator[tuple[Path, bytes]]:
    for child in sorted(bundle.iterdir(), key=lambda item: item.name):
        if child.name == "__pycache__" or child.name.endswith((".pyc", ".pyo")):
            continue
        name = relative / child.name
        if child.is_dir():
            yield from _contents(child, name)
        else:
            yield name, child.read_bytes()


def install(destination: str | Path, *, overwrite: bool = False) -> Path:
    """Copy the skill to an exact destination directory, without agent configuration.

    Existing destinations require ``overwrite=True``. Only bundled files are
    replaced; additional files are kept. Destination symlinks are never followed
    within the skill, so installing cannot overwrite an editable source link.
    """
    target = Path(destination).expanduser().absolute()
    bundle = _bundle()
    if isinstance(bundle, Path) and target.resolve().is_relative_to(bundle.resolve()):
        raise ValueError("Install outside the bundled skill directory")
    if target.is_symlink():
        raise ValueError(f"Destination is a symlink; keep editable links separate: {target}")
    if target.exists():
        if not target.is_dir():
            raise ValueError(f"Destination is not a directory: {target}")
        if not overwrite:
            raise FileExistsError(f"Destination exists: {target}; use --overwrite to update it")

    contents = list(_contents(bundle))
    if not any(name == Path("SKILL.md") for name, _ in contents):
        raise ValueError("The installed package is missing its bundled SKILL.md")
    # Check all conflicts before changing an existing installation.
    for name, _ in contents:
        output = target / name
        for parent in (output, *output.parents):
            if parent == target:
                break
            if parent.is_symlink():
                raise ValueError(f"Refusing to overwrite through a symlink: {parent}")
            if parent.exists() and parent.is_dir() != (parent != output):
                raise ValueError(f"File/directory conflict: {parent}")

    target.mkdir(parents=True, exist_ok=True)
    for name, data in contents:
        output = target / name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    return target


def main(argv: Sequence[str] | None = None) -> None:
    """Run the small skill installer without a harness-specific dependency."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("path", help="Print the bundled directory for direct use or development")
    copier = commands.add_parser(
        "install", help="Copy the complete skill to a destination directory"
    )
    copier.add_argument(
        "destination", type=Path, help="Exact skill folder, e.g. ~/.agents/skills/figworks"
    )
    copier.add_argument(
        "--overwrite", action="store_true", help="Replace bundled files in an existing copy"
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "path":
            print(path())
        else:
            print(
                f"Installed FigWorks skill at {install(args.destination, overwrite=args.overwrite)}"
            )
    except (OSError, ValueError) as error:
        parser.exit(1, f"figworks.skill: {error}\n")


if __name__ == "__main__":
    main()
