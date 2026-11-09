from pathlib import Path

import pytest

from figworks import skill


def test_installs_the_complete_portable_bundle(tmp_path):
    destination = tmp_path / "agent" / "skills" / "figworks"
    assert skill.install(destination) == destination
    expected = {
        "SKILL.md",
        "assets/figure.py",
        "references/composition.md",
        "references/environment.md",
        "references/planning-and-review.md",
        "references/sources.md",
    }
    installed = {
        p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()
    }
    assert expected <= installed
    assert not any("__pycache__" in name or name.endswith(".pyc") for name in installed)
    for name in installed:
        assert (destination / name).read_bytes() == (skill.path() / name).read_bytes()


def test_updates_require_overwrite_and_keep_additional_files(tmp_path):
    destination = skill.install(tmp_path / "figworks")
    entry = destination / "SKILL.md"
    entry.write_text("local edits", encoding="utf-8")
    extra = destination / "notes.txt"
    extra.write_text("keep me", encoding="utf-8")
    with pytest.raises(FileExistsError, match="--overwrite"):
        skill.install(destination)
    assert entry.read_text() == "local edits"
    skill.install(destination, overwrite=True)
    assert entry.read_bytes() == (skill.path() / "SKILL.md").read_bytes()
    assert extra.read_text() == "keep me"


@pytest.mark.parametrize("dangling", [False, True])
def test_refuses_development_links_even_with_overwrite(tmp_path, dangling):
    source = tmp_path / "source"
    if not dangling:
        source.mkdir()
    destination = tmp_path / "figworks"
    destination.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        skill.install(destination, overwrite=True)
    assert destination.is_symlink()
    assert not (source / "SKILL.md").exists()


@pytest.mark.parametrize("relative", ["SKILL.md", "references", "references/composition.md"])
def test_refuses_nested_links_before_overwriting_any_files(tmp_path, relative):
    destination = skill.install(tmp_path / "figworks")
    entry = destination / "SKILL.md"
    entry.write_text("local edits", encoding="utf-8")
    linked = destination / relative
    outside = tmp_path / "outside"
    linked.rename(outside)
    linked.symlink_to(outside, target_is_directory=outside.is_dir())
    with pytest.raises(ValueError, match="symlink"):
        skill.install(destination, overwrite=True)
    assert entry.read_text() == "local edits"


@pytest.mark.parametrize("relative", ["assets", "references/composition.md"])
def test_rejects_file_directory_conflicts_before_changes(tmp_path, relative):
    destination = tmp_path / "figworks"
    destination.mkdir()
    entry = destination / "SKILL.md"
    entry.write_text("local edits", encoding="utf-8")
    conflict = destination / relative
    if relative == "assets":
        conflict.write_text("not a folder", encoding="utf-8")
    else:
        conflict.mkdir(parents=True)
    with pytest.raises(ValueError, match="conflict"):
        skill.install(destination, overwrite=True)
    assert entry.read_text() == "local edits"


def test_refuses_installation_inside_the_bundle():
    with pytest.raises(ValueError, match="outside"):
        skill.install(skill.path(), overwrite=True)
    with pytest.raises(ValueError, match="outside"):
        skill.install(skill.path() / "nested")


def test_cli_path_install_and_existing_destination(tmp_path, capsys):
    skill.main(["path"])
    assert Path(capsys.readouterr().out.strip()) == skill.path()
    destination = tmp_path / "figworks"
    skill.main(["install", str(destination)])
    assert str(destination) in capsys.readouterr().out
    with pytest.raises(SystemExit) as error:
        skill.main(["install", str(destination)])
    assert error.value.code == 1
    assert "--overwrite" in capsys.readouterr().err
