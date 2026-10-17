"""Create private local development settings once; never print or overwrite secrets."""

import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
destination = ROOT / ".env"
if destination.exists():
    print("Existing .env preserved.")
else:
    password = secrets.token_urlsafe(32)
    token = secrets.token_urlsafe(32)
    values = (
        f"POSTGRES_PASSWORD={password}\n"
        f"RELEVO_API_TOKEN={token}\n"
        f"RELEVO_DATABASE_URL=postgresql+psycopg://relevo:{password}@127.0.0.1:55432/relevo\n"
        f"RELEVO_TEST_DATABASE_URL=postgresql+psycopg://relevo:{password}"
        "@127.0.0.1:55433/relevo_test\n"
    )
    # Exclusive creation also protects against concurrent configuration commands.
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(values)
    print(
        "Created private .env with generated local credentials. Keep it out of version control."
    )
