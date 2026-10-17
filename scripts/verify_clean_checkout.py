"""Verify a fresh local Git clone with new credentials and an isolated Compose project."""

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "relevo-clean-checkout"


def run(args, cwd=ROOT, *, log=None):
    result = subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, timeout=600, check=False
    )
    if log:
        with log.open("a", encoding="utf-8") as stream:
            stream.write(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(
            f"Verification command failed ({result.returncode}); see ignored log"
        )
    return result.stdout.strip()


def main():
    commit = run(["git", "rev-parse", "HEAD"])
    destination = ROOT / ".cache" / f"clean-checkout-{commit[:12]}"
    assert not destination.exists(), (
        "Use a new committed checkpoint for a fresh verification"
    )
    assert not run(
        [
            "docker",
            "ps",
            "-aq",
            "--filter",
            f"label=com.docker.compose.project={PROJECT}",
        ]
    )
    assert not run(
        [
            "docker",
            "volume",
            "ls",
            "-q",
            "--filter",
            f"label=com.docker.compose.project={PROJECT}",
        ]
    )
    run(["git", "clone", "--no-local", str(ROOT), str(destination)])
    assert run(["git", "rev-parse", "HEAD"], destination) == commit
    log = destination / ".cache" / "verification.log"
    log.parent.mkdir(parents=True)
    run(["python", "scripts/configure.py"], destination, log=log)
    assert (destination / ".env").read_bytes() != (ROOT / ".env").read_bytes()
    override = destination / ".cache" / "verification-compose.json"
    override.write_text(
        json.dumps(
            {
                "services": {
                    service: {"image": "relevo-backend:clean-checkout"}
                    for service in (
                        "migrate",
                        "api",
                        "worker",
                        "scheduler",
                        "fault-api",
                    )
                }
            }
        ),
        encoding="utf-8",
    )
    compose = [
        "docker",
        "compose",
        "-p",
        PROJECT,
        "-f",
        "compose.yaml",
        "-f",
        str(override),
    ]
    # Development/test services are stopped, never removed. Their database volume is preserved.
    run(
        [
            "docker",
            "compose",
            "--profile",
            "test",
            "stop",
            "worker",
            "scheduler",
            "api",
            "postgres",
            "fault-api",
            "postgres-test",
            "toxiproxy",
        ],
        log=log,
    )
    passed = False
    try:
        run(
            compose + ["up", "--build", "-d", "--wait", "--wait-timeout", "90"],
            destination,
            log=log,
        )
        for key in ("fresh-clone-first", "fresh-clone-after-restart"):
            if key.endswith("restart"):
                run(
                    compose + ["restart", "api", "worker", "scheduler"],
                    destination,
                    log=log,
                )
                run(
                    compose + ["up", "-d", "--wait", "--wait-timeout", "90"],
                    destination,
                    log=log,
                )
            run(
                compose
                + [
                    "exec",
                    "-T",
                    "-e",
                    "RELEVO_API_URL=http://api:8000",
                    "api",
                    "python",
                    "-m",
                    "relevo",
                    "demo",
                    "--key",
                    key,
                ],
                destination,
                log=log,
            )
        run(
            compose + ["--profile", "test", "run", "--build", "--rm", "tests"],
            destination,
            log=log,
        )
        passed = True
    finally:
        run(compose + ["--profile", "test", "down"], destination, log=log)
        volumes = run(
            [
                "docker",
                "volume",
                "ls",
                "-q",
                "--filter",
                f"label=com.docker.compose.project={PROJECT}",
            ]
        ).splitlines()
        assert set(volumes) <= {f"{PROJECT}_postgres_data"}, (
            "Unexpected verification volume"
        )
        for volume in volumes:
            run(["docker", "volume", "rm", volume], log=log)
        run(
            ["docker", "compose", "up", "-d", "--wait", "--wait-timeout", "90"], log=log
        )
    if passed:
        output = ROOT / "artifacts" / "verification" / "clean-checkout.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "captured_at": datetime.now(UTC).isoformat(),
                    "git_commit": commit,
                    "source": "scripts/verify_clean_checkout.py",
                    "fresh_credentials": True,
                    "compose_startup": "passed",
                    "cli_demo": "passed before and after component restart",
                    "full_container_suite": "passed",
                    "development_volume": "preserved",
                    "cleanup": "verification containers/network/new database volume removed; development services restored",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            "Clean-checkout startup, CLI, restart, and full test suite passed; development services restored."
        )


if __name__ == "__main__":
    main()
