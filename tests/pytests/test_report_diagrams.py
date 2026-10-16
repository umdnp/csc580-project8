"""Exercise Pandoc's actual Lua filter with local, synthetic cached images."""

import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zipfile
import zlib

import pytest


ROOT = Path(__file__).resolve().parents[2]
FILTER = ROOT / "report/filters/plantuml.lua"
SOURCE = "@startuml\nAlice -> Bob : Test\n@enduml\n"


def tiny_png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    return b"\x89PNG\r\n\x1a\n" + chunk(
        b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ) + chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff")) + chunk(b"IEND", b"")


@pytest.fixture
def document(tmp_path):
    portable = ROOT / ".cache/report-tools/pandoc.exe"
    pandoc = os.environ.get("PANDOC_BIN") or shutil.which("pandoc")
    if not pandoc and portable.is_file():
        pandoc = str(portable)
    if not pandoc:
        pytest.skip("Pandoc is required for report filter integration tests")
    cache = tmp_path / "report/diagrams/rendered"
    cache.mkdir(parents=True)
    (tmp_path / "report/toolchain.json").write_text("{}\n")
    key = hashlib.sha1(("{}\n\n" + SOURCE).encode()).hexdigest()
    image = cache / f"{key}.png"
    image.write_bytes(tiny_png())

    def run(markdown, writer="html", output=None):
        command = [pandoc, "-f", "markdown", "-t", writer, "--lua-filter", str(FILTER)]
        if output:
            command.extend(["-o", str(output)])
        environment = os.environ.copy()
        environment["PLANTUML_CACHED_ONLY"] = "1"
        # A cache hit must not invoke a renderer, even if none is installed.
        environment["PLANTUML_JAVA"] = "deliberately-missing-java"
        return subprocess.run(command, input=markdown, text=True, capture_output=True,
                              cwd=tmp_path, env=environment, check=False)

    return tmp_path, image, run


def block(source=SOURCE):
    return '```{#fig-test .plantuml caption="A test caption"}\n' + source + '\n```\n'


def test_cached_html_is_embedded_and_captioned(document):
    _, _, run = document
    result = run(block())
    assert result.returncode == 0, result.stderr
    assert "data:image/png;base64," in result.stdout
    assert '<figure id="fig-test">' in result.stdout
    assert "<figcaption" in result.stdout
    assert "A test caption" in result.stdout


def test_source_file_and_crlf_use_same_cache(document):
    folder, _, run = document
    (folder / "source.puml").write_bytes(SOURCE.replace("\n", "\r\n").encode())
    result = run('```{.plantuml source="source.puml" caption="File source"}\n```')
    assert result.returncode == 0, result.stderr
    assert "data:image/png;base64," in result.stdout


def test_source_change_fails_in_cached_only_mode(document):
    _, _, run = document
    result = run(block(SOURCE.replace("Test", "Changed")))
    assert result.returncode != 0
    assert "no cached image" in result.stderr


def test_invalid_cache_fails_instead_of_emitting_bad_image(document):
    _, image, run = document
    image.write_bytes(b"not a PNG")
    result = run(block())
    assert result.returncode != 0
    assert "invalid cached PNG" in result.stderr


def test_unmarked_code_is_not_rendered(document):
    _, _, run = document
    result = run("```sql\nSELECT 1;\n```")
    assert result.returncode == 0, result.stderr
    assert "SELECT" in result.stdout
    assert "data:image/png" not in result.stdout


def test_docx_embeds_cached_png(document):
    folder, _, run = document
    output = folder / "test.docx"
    result = run(block(), "docx", output)
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(output) as package:
        assert any(name.startswith("word/media/") and name.endswith(".png") for name in package.namelist())
        assert "A test caption" in package.read("word/document.xml").decode()


def test_latex_references_local_png(document):
    _, image, run = document
    result = run(block(), "latex")
    assert result.returncode == 0, result.stderr
    assert image.name in result.stdout
    assert "includegraphics" in result.stdout
    assert "A test caption" in result.stdout
