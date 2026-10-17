"""Prepare ignored local monitoring credentials; standard library only."""

import secrets
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    entries = dict(
        line.split("=", 1)
        for line in (root / ".env").read_text().splitlines()
        if line and not line.startswith("#") and "=" in line
    )
    token = entries.get("RELEVO_API_TOKEN", "")
    if len(token) < 32:
        raise SystemExit("Run python scripts/configure.py first")
    folder = root / ".cache" / "observability"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "api_token").write_text(token, encoding="utf-8")
    password = folder / "grafana_password"
    if not password.exists():
        password.write_text(secrets.token_urlsafe(32), encoding="utf-8")
    print("Prepared ignored local monitoring credentials.")


if __name__ == "__main__":
    main()
