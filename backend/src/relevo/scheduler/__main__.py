"""python -m relevo.scheduler [--once]; no API startup hooks or local timer state."""

import argparse
import logging
import signal
from threading import Event

from sqlalchemy.exc import SQLAlchemyError

from relevo.config import Settings
from relevo.db.connection import build_engine
from relevo.engine.recovery import recover_expired
from relevo.observability import Telemetry, configure_logging, instrument_engine, log_event

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Recover expired Relevo attempts")
    parser.add_argument("--once", action="store_true", help="Scan one bounded batch, then exit")
    args = parser.parse_args()
    settings = Settings()
    configure_logging()
    telemetry = Telemetry(
        "scheduler", endpoint=str(settings.otlp_endpoint) if settings.otlp_endpoint else None
    )
    if settings.metrics_port:
        telemetry.serve(settings.metrics_port, settings.api_token.get_secret_value())
    stop = Event()
    previous = {}
    for signum in (signal.SIGINT, signal.SIGTERM):
        previous[signum] = signal.signal(signum, lambda *_: stop.set())
    engine = build_engine(settings)
    instrument_engine(engine, telemetry)
    try:
        while not stop.is_set():
            try:
                recovered = recover_expired(engine, settings)
            except SQLAlchemyError:
                # DB exceptions can contain credentials or bound data. Never print them.
                logger.warning("Recovery scan could not be confirmed; next scan will retry")
                if args.once:
                    raise SystemExit(1) from None
            else:
                for attempt in recovered:
                    log_event(
                        "Recovered expiry:",
                        job_id=attempt.job_id,
                        attempt_id=attempt.attempt_id,
                        fencing_token=attempt.fencing_token,
                        state=attempt.state,
                    )
            if args.once:
                break
            stop.wait(settings.recovery_scan_seconds)
    finally:
        engine.dispose()
        telemetry.close()
        for signum, handler in previous.items():
            signal.signal(signum, handler)


if __name__ == "__main__":
    main()
