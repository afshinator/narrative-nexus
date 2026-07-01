"""Schedule run_daily_pipeline via APScheduler. One function, separated from
the scraper scheduler for clean shutdown/isolation in app/main.py lifespan."""

from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler


def start_pipeline_scheduler(
    db_path: str,
    *,
    provider_overrides: dict[str, str] | None = None,
) -> BackgroundScheduler:
    """Start a BackgroundScheduler that fires run_daily_pipeline daily.

    Fires immediately on start (next_run_time=now) so the first run happens
    at app startup regardless of when the app was launched. Subsequent runs
    fire at 24h intervals.

    Args:
      db_path: Path to the SQLite database.
      provider_overrides: Optional dict of agent_slot → provider_id from
                          runtime config (Pipeline Flow dropdowns).

    Returns the scheduler so the caller can shut it down in lifespan cleanup.
    """
    scheduler = BackgroundScheduler(daemon=True)

    def _job():
        """Thin wrapper: run the pipeline and swallow/log errors so one bad
        run doesn't stop the scheduler from retrying on the next tick."""
        try:
            from pipeline.runner import run_daily_pipeline  # lazy import — server doesn't need pipeline deps
            result = run_daily_pipeline(
                db_path,
                provider_overrides=provider_overrides,
            )
            print(f"[pipeline] daily run complete: {result}")
        except Exception as exc:
            print(f"[pipeline] daily run failed: {exc}")

    scheduler.add_job(
        _job,
        "interval",
        days=1,
        id="daily-pipeline",
        next_run_time=datetime.now(timezone.utc),
    )
    scheduler.start()
    return scheduler
