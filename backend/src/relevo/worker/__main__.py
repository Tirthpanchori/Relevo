"""python -m relevo.worker [--once]; safe to import under Windows spawn."""

import argparse
import asyncio
import signal

from relevo.observability import Telemetry, configure_logging
from relevo.worker.config import WorkerSettings
from relevo.worker.coordinator import CoordinatorClient, CoordinatorRejected
from relevo.worker.runtime import Worker


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a supervised Relevo worker")
    parser.add_argument("--once", action="store_true", help="Attempt one claim, then exit")
    args = parser.parse_args()
    settings = WorkerSettings()
    configure_logging()
    telemetry = Telemetry(
        "worker", endpoint=str(settings.otlp_endpoint) if settings.otlp_endpoint else None
    )
    if settings.metrics_port:
        telemetry.serve(settings.metrics_port, settings.api_token.get_secret_value())

    async def run() -> None:
        stop = asyncio.Event()
        previous = {}
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, lambda *_: stop.set())
        try:
            async with CoordinatorClient(settings, telemetry=telemetry) as client:
                worker = Worker(client, settings, stop=stop)
                if args.once:
                    outcome = await worker.run_once()
                    print(outcome)
                    if outcome not in ("idle", "reported"):
                        raise SystemExit(1)
                else:
                    await worker.run_forever()
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)

    try:
        asyncio.run(run())
    except CoordinatorRejected as exc:
        raise SystemExit(str(exc)) from None
    finally:
        telemetry.close()


if __name__ == "__main__":
    main()
