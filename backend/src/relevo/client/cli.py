"""JSON output and environment-only secrets for python -m relevo."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from relevo.api.schemas import SubmitJob
from relevo.client import ClientError, ClientSettings, RelevoClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit and inspect durable Relevo jobs")
    parser.add_argument(
        "--api-url", help="Coordinator origin; otherwise RELEVO_API_URL is required"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    submit = commands.add_parser(
        "submit", help="Submit work; preserve the key for uncertain retries"
    )
    submit.add_argument("task", choices=("hash_payload", "timed_work", "transient_failure"))
    payload = submit.add_mutually_exclusive_group(required=True)
    payload.add_argument("--payload", help="JSON object")
    payload.add_argument("--payload-file", type=Path, help="UTF-8 JSON object file")
    submit.add_argument("--key", required=True, help="Stable idempotency key")
    submit.add_argument("--run-at", help="Timezone-aware ISO timestamp")
    for name in ("inspect", "attempts", "wait"):
        command = commands.add_parser(name)
        command.add_argument("job_id", type=UUID)
        if name == "wait":
            command.add_argument("--timeout", type=float, default=60)
    demo = commands.add_parser(
        "demo", help="Submit hashing, wait for completion, and print history"
    )
    demo.add_argument("--key", required=True)
    demo.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    try:
        settings = ClientSettings(**({"api_url": args.api_url} if args.api_url else {}))
    except ValidationError:
        parser.error("Set a valid RELEVO_API_URL and RELEVO_API_TOKEN (at least 32 characters)")

    async def run():
        async with RelevoClient(settings) as client:
            if args.command == "submit":
                try:
                    if args.payload_file:
                        with args.payload_file.open("rb") as stream:
                            raw = stream.read(1_048_577)
                    else:
                        raw = args.payload.encode("utf-8")
                    if len(raw) > 1_048_576:
                        raise ValueError("Payload file exceeds limit")
                    request = SubmitJob.model_validate(
                        {"task_type": args.task, "payload": json.loads(raw), "run_at": args.run_at}
                    )
                except (OSError, ValueError, UnicodeError, RecursionError):
                    raise ClientError(
                        "Invalid task input: use a bounded JSON object and aware run_at"
                    ) from None
                result = await client.submit(request, idempotency_key=args.key)
            elif args.command == "demo":
                request = SubmitJob(task_type="hash_payload", payload={"source": "relevo-cli-demo"})
                submitted = await client.submit(request, idempotency_key=args.key)
                result = await client.wait(submitted.id, timeout=args.timeout)
                history = await client.attempts(result.id)
                print(
                    json.dumps(
                        {
                            "job": result.model_dump(mode="json"),
                            "history": history.model_dump(mode="json"),
                        },
                        indent=2,
                    )
                )
                return 0 if result.state == "succeeded" else 2
            elif args.command == "inspect":
                result = await client.inspect(args.job_id)
            elif args.command == "attempts":
                result = await client.attempts(args.job_id)
            else:
                result = await client.wait(args.job_id, timeout=args.timeout)
            print(result.model_dump_json(indent=2))
            return 2 if args.command == "wait" and result.state == "failed" else 0

    try:
        code = asyncio.run(run())
    except (ClientError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    raise SystemExit(code)
