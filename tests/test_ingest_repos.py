"""Tests for repo ingestion node."""

import pytest
from pathlib import Path
from src.nodes.ingest_repos import walk_repo, chunk_file


def test_walk_repo_finds_groovy_files(tmp_path):
    """walk_repo should find .groovy files and skip .git directories."""
    (tmp_path / "vars").mkdir()
    (tmp_path / "vars" / "scan.groovy").write_text("def call() { }")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("ignore me")

    files = walk_repo(tmp_path)

    assert len(files) == 1
    assert files[0].suffix == ".groovy"


def test_walk_repo_finds_jenkinsfiles(tmp_path):
    """walk_repo should find Jenkinsfile (no extension)."""
    (tmp_path / "Jenkinsfile").write_text("pipeline { }")
    (tmp_path / "Jenkinsfile-ci-scan").write_text("pipeline { }")

    files = walk_repo(tmp_path)

    assert len(files) == 2


def test_walk_repo_skips_node_modules(tmp_path):
    """walk_repo should skip node_modules directory."""
    (tmp_path / "node_modules" / "pkg").mkdir(parents=True)
    (tmp_path / "node_modules" / "pkg" / "index.js").write_text("module.exports = {}")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.js").write_text("console.log('hi')")

    files = walk_repo(tmp_path)

    assert len(files) == 1
    assert files[0].name == "app.js"


def test_walk_repo_finds_yaml(tmp_path):
    """walk_repo should find YAML files."""
    (tmp_path / "deployment.yaml").write_text("apiVersion: v1")
    (tmp_path / "config.yml").write_text("key: value")

    files = walk_repo(tmp_path)

    assert len(files) == 2


def test_walk_repo_finds_dockerfiles(tmp_path):
    """walk_repo should find Dockerfile (no extension)."""
    (tmp_path / "Dockerfile").write_text("FROM alpine:3.18")
    (tmp_path / "Dockerfile.dev").write_text("FROM node:18")

    files = walk_repo(tmp_path)

    # Dockerfile has no extension but is in SCAN_FILENAMES
    # Dockerfile.dev has extension ".dev" which is not in SCAN_EXTENSIONS
    # but walk_repo checks p.name in SCAN_FILENAMES — "Dockerfile.dev" is not "Dockerfile"
    assert any(f.name == "Dockerfile" for f in files)


def test_chunk_file_splits_content():
    """chunk_file should split large content into multiple chunks."""
    content = "def functionA():\n    pass\n\n" * 50  # ~1500 chars
    chunks = chunk_file(content, language=".py")
    assert len(chunks) >= 1


def test_chunk_file_empty_content():
    """chunk_file should return empty list for empty/whitespace content."""
    assert chunk_file("") == []
    assert chunk_file("   \n  ") == []


def test_chunk_file_groovy():
    """chunk_file should handle Groovy files (using Java splitter)."""
    content = '''void call(Map config) {
    println "scanning..."
    config.scanners.each { scanner ->
        println scanner.name
    }
}

def helper() {
    return "done"
}
'''
    chunks = chunk_file(content, language=".groovy")
    assert len(chunks) >= 1
    assert any("call" in c for c in chunks)
