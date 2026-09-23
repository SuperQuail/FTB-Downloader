"""包内条目名（archive entry name）的回归测试。

背景：C# 参考项目 CurseTheBeast 的 FileEntry.WithArchiveEntryName() 有两个坑，
FTB Skies 2: Aero v1.12.1 就是被第一个坑干掉的——打包出来的
overrides//default-server.properties 让 HMCL 抛
"Zip entry is trying to write outside of the destination directory" 直接安装失败。
本文件把这两个坑钉死。
"""

from __future__ import annotations

import pytest

from ftb_downloader.models.manifest import (
    ModpackManifest,
    normalize_entry_name,
    validate_entry_name,
)


# --------------------------------------------------------------------------- 坑 1
# FTB 清单里 path="./" 的条目必须落在 overrides 根目录，不能多出一个斜杠。
def test_empty_path_does_not_produce_empty_segment() -> None:
    assert normalize_entry_name("./", "default-server.properties") == "default-server.properties"


def test_double_slash_never_appears() -> None:
    entry = normalize_entry_name("./", "default-server.properties")
    assert "//" not in f"overrides/{entry}"
    assert not f"overrides/{entry}".startswith("/")


@pytest.mark.parametrize(
    ("parts", "expected"),
    [
        (("./", "default-server.properties"), "default-server.properties"),
        ((".", "x.txt"), "x.txt"),
        (("", "x.txt"), "x.txt"),
        ((None, "x.txt"), "x.txt"),
        (("   ", "x.txt"), "x.txt"),
        (("./mods", "foo.jar"), "mods/foo.jar"),
        (("./config", "a.toml"), "config/a.toml"),
        (("/mods/", "foo.jar"), "mods/foo.jar"),
        (("mods", "foo.jar"), "mods/foo.jar"),
        (("a//b", "c"), "a/b/c"),          # 段内重复斜杠也要收掉
        ((".//mods//", "foo.jar"), "mods/foo.jar"),
        (("a\\b", "c"), "a/b/c"),        # Windows 反斜杠
        ((None,), ""),
    ],
)
def test_normalize_entry_name(parts: tuple[str | None, ...], expected: str) -> None:
    assert normalize_entry_name(*parts) == expected


# --------------------------------------------------------------------------- 坑 2
# 不能用 lstrip(".") 去前缀，否则点号开头的文件会被改名。
def test_dotfiles_keep_their_leading_dot() -> None:
    assert normalize_entry_name("./config", ".gitkeep") == "config/.gitkeep"
    assert normalize_entry_name("./mods", ".gitkeep") == "mods/.gitkeep"
    assert normalize_entry_name("./config", ".gitignore") == "config/.gitignore"
    assert normalize_entry_name("./kubejs", ".content", "items") == "kubejs/.content/items"


def test_dotfile_inside_path_is_preserved() -> None:
    assert (
        normalize_entry_name("./kubejs/assets/oracle_index/books/excessive_utilities/.content/items", "x.json")
        == "kubejs/assets/oracle_index/books/excessive_utilities/.content/items/x.json"
    )


# --------------------------------------------------------------------------- 校验
@pytest.mark.parametrize(
    "entry",
    [
        "overrides//default-server.properties",
        "/absolute/path.txt",
        "overrides/",
        "overrides/./x.txt",
        "../escape.txt",
        "a/../../b",
        "",
    ],
)
def test_validate_entry_name_rejects(entry: str) -> None:
    with pytest.raises(ValueError):
        validate_entry_name(entry)


@pytest.mark.parametrize(
    "entry",
    [
        "manifest.json",
        "overrides/default-server.properties",
        "overrides/config/.gitkeep",
        "overrides/mods/foo.jar",
        "a/b/c/d.txt",
    ],
)
def test_validate_entry_name_accepts(entry: str) -> None:
    assert validate_entry_name(entry) == entry


# --------------------------------------------------------------------------- 端到端
def test_whole_manifest_entries_are_valid() -> None:
    """拿一份含各种脏 path 的合成清单，确认产出的条目名全部合法。"""
    manifest = ModpackManifest.from_json(
        {
            "id": 1,
            "name": "test",
            "type": "release",
            "files": [
                # 就是干掉 FTB Skies 2 的那一条
                {"id": 1, "name": "default-server.properties", "path": "./", "type": "resource"},
                {"id": 2, "name": ".gitkeep", "path": "./config", "type": "resource"},
                {"id": 3, "name": ".gitkeep", "path": "./mods", "type": "resource"},
                {"id": 4, "name": "foo.jar", "path": "./mods", "type": "mod"},
                {
                    "id": 5,
                    "name": "bar.jar.disabled",
                    "path": "./mods",
                    "type": "mod",
                    "sha1": "",
                    "size": 0,
                    "curseforge": {"project": "1", "file": "2"},
                },
            ],
            "specs": {"minimum": 0, "recommended": 0},
            "targets": [],
        }
    )

    entries = [f.archive_entry for f in manifest.files]
    assert entries == [
        "default-server.properties",
        "config/.gitkeep",
        "mods/.gitkeep",
        "mods/foo.jar",
        "mods/bar.jar",  # .jar.disabled 去掉 .disabled（对照 FTBFileEntry）
    ]
    for entry in entries:
        validate_entry_name(entry)

    # 标准包 = 客户端文件里排除掉交给启动器下载的 CurseForge 模组
    assert [f.archive_entry for f in manifest.local_files] == [
        "default-server.properties",
        "config/.gitkeep",
        "mods/.gitkeep",
        "mods/foo.jar",
    ]
