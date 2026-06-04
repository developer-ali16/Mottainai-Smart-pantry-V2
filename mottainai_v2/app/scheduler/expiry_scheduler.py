"""
Background scheduler for expiry reminders.

Uses APScheduler (BackgroundScheduler) to run periodic jobs
inside the FastAPI process.

Production note:
  For multiple replicas, move to Celery + Redis Beat to prevent
  duplicate notifications. This implementation is correct for
  single-instance deployments and development.
"""
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.repositories import notification_repository, pantry_repository
from app.services.email_service import send_expiry_reminder_email

logger = get_logger("scheduler")

_scheduler: BackgroundScheduler | None = None


# ---------------------------------------------------------------------------
# Job functions
# ---------------------------------------------------------------------------

def check_expiring_items() -> None:
    """
    Main scheduler job.
    Runs daily and:
      1. Finds all items expiring within EXPIRY_CHECK_DAYS_AHEAD days.
      2. Creates an in-app notification for each (skips duplicates).
      3. Sends a single digest email per user (if email is configured).
    """
    days_ahead = settings.expiry_check_days_ahead
    db = SessionLocal()

    try:
        today = date.today()
        logger.info("Running expiry check: today=%s, looking %d days ahead", today, days_ahead)

        # Collect items expiring today through days_ahead
        # Group by user for digest email
        user_items: dict[int, list] = {}

        for offset in range(0, days_ahead + 1):
            target_date = today + timedelta(days=offset)
            items = pantry_repository.get_expiring_items(db, target_date)

            for item in items:
                days_left = (item.expiry_date - today).days
                notif_type = f"expiry_reminder_{days_left}d"

                # Skip if a notification of this type was already sent today
                if notification_repository.notification_already_sent(
                    db, item.user_id, item.id, notif_type
                ):
                    continue

                # Create in-app notification
                if days_left == 0:
                    title = f"⚠️ '{item.item_name.title()}' expires today!"
                    message = (
                        f"Your {item.item_name} expires today. "
                        f"Use it now to avoid waste."
                    )
                else:
                    title = f"🔔 '{item.item_name.title()}' expires in {days_left} day(s)"
                    message = (
                        f"Your {item.item_name} will expire on {item.expiry_date} "
                        f"({days_left} day(s) from now). Use it soon!"
                    )

                notification_repository.create_notification(
                    db,
                    user_id=item.user_id,
                    pantry_item_id=item.id,
                    title=title,
                    message=message,
                    notification_type=notif_type,
                )
                logger.info(
                    "Notification created: user_id=%d item=%s days_left=%d",
                    item.user_id,
                    item.item_name,
                    days_left,
                )

                # Collect for email digest
                if item.user_id not in user_items:
                    user_items[item.user_id] = []
                user_items[item.user_id].append({
                    "name": item.item_name,
                    "expiry_date": item.expiry_date,
                    "days_left": days_left,
                    "user": item.user,
                })

        # Send one digest email per user
        if settings.email_configured and user_items:
            from app.models.user import User
            for user_id, item_list in user_items.items():
                user = item_list[0]["user"]
                clean_items = [
                    {"name": i["name"], "expiry_date": i["expiry_date"], "days_left": i["days_left"]}
                    for i in item_list
                ]
                send_expiry_reminder_email(user.email, user.full_name, clean_items)

        logger.info("Expiry check complete. Notified %d user(s).", len(user_items))

    except Exception as exc:
        logger.exception("Expiry check failed: %s", exc)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Scheduler lifecycle
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    """Start the background scheduler. Called at application startup."""
    global _scheduler

    _scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce": True,          # merge missed runs into one
            "max_instances": 1,        # never run job concurrently
            "misfire_grace_time": 3600,  # tolerate up to 1hr late start
        }
    )

    # Run daily at 08:00 (server local time)
    _scheduler.add_job(
        check_expiring_items,
        trigger=CronTrigger(hour=8, minute=0),
        id="expiry_check",
        name="Daily expiry reminder check",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        "Scheduler started. Next run: %s",
        _scheduler.get_job("expiry_check").next_run_time,
    )


def stop_scheduler() -> None:
    """Stop the scheduler gracefully. Called at application shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


def run_expiry_check_now() -> None:
    """
    Trigger the expiry check immediately.
    Useful for testing and development — call via a management endpoint.
    """
    logger.info("Manual expiry check triggered.")
    check_expiring_items()
