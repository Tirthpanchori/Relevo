"""Check staged source without printing matched credentials or file contents."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True
    ).stdout


def main():
    paths = (
        git("diff", "--cached", "--name-only", "--diff-filter=ACM", "-z")
        .decode()
        .split("\0")
    )
    private = []
    environment = ROOT / ".env"
    if environment.exists():
        for line in environment.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and value and ("TOKEN" in key or "PASSWORD" in key):
                private.append(value.encode())
    patterns = [
        rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b",
        rb"\bAKIA[A-Z0-9]{16}\b",
    ]
    bad = []
    for path in filter(None, paths):
        forbidden = path == ".env" or any(
            part in {".cache", ".venv", ".tools"} for part in Path(path).parts
        )
        content = git("show", f":{path}")
        if (
            forbidden
            or any(value in content for value in private)
            or any(re.search(pattern, content) for pattern in patterns)
        ):
            bad.append(path)
    if bad:
        raise SystemExit(
            "Potential private material in staged files: " + ", ".join(bad)
        )
    print(
        f"Staged secret check passed for {len(list(filter(None, paths)))} files; ignored credentials remain local."
    )


if __name__ == "__main__":
    main()
