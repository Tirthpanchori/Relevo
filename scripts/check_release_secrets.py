"""Scan tracked release files and reachable Git blobs; report paths/IDs, never matches."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    re.compile(rb"\bAKIA[A-Z0-9]{16}\b"),
]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    private = []
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and value and ("TOKEN" in key or "PASSWORD" in key):
                private.append(value.encode())

    def sensitive(data):
        return any(v in data for v in private) or any(p.search(data) for p in PATTERNS)

    failed = []
    paths = git("ls-files", "-z").decode().split("\0")
    for name in filter(None, paths):
        file = ROOT / name
        if (
            name == ".env"
            or any(p in {".tools", ".cache", "node_modules"} for p in file.parts)
            or file.is_file()
            and sensitive(file.read_bytes())
        ):
            failed.append(name)
    objects = git("rev-list", "--objects", "--all").decode().splitlines()
    checked = 0
    for entry in objects:
        oid = entry.split(" ", 1)[0]
        if git("cat-file", "-t", oid).strip() == b"blob":
            checked += 1
            if sensitive(git("cat-file", "blob", oid)):
                failed.append("history blob " + oid)
    if failed:
        raise SystemExit("Potential secrets: " + ", ".join(failed))
    print(
        f"Secret patterns/current credentials absent: {len(list(filter(None, paths)))} files, "
        f"{checked} reachable history blobs. This is a bounded pattern check, not a certification."
    )


if __name__ == "__main__":
    main()
