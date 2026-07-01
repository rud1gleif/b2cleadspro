"""Standalone queue dispatcher — run as a separate process to consume Redis queues.

Usage:
    python -m app.workers.queue_dispatcher

This process continuously polls Redis queues and dispatches jobs to the
appropriate worker functions. It is optional — if Redis is unavailable,
jobs run directly via FastAPI BackgroundTasks in the API process.
"""
import time
import signal
import sys
from loguru import logger
from app.config import settings
from app.services.queue_service import dequeue_job, queue_length
from app.workers.scrape_worker import run_scrape_job
from app.workers.verify_worker import run_verify_batch

RUNNING = True


def _handle_signal(signum, frame):
    global RUNNING
    logger.info("Queue dispatcher shutting down...")
    RUNNING = False


def main():
    global RUNNING
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("Queue dispatcher started.")
    logger.info(f"  Scrape queue : {settings.redis_queue_scrape}")
    logger.info(f"  Verify queue : {settings.redis_queue_verify}")

    while RUNNING:
        # Scrape queue
        scrape_ql = queue_length(settings.redis_queue_scrape)
        if scrape_ql > 0:
            payload = dequeue_job(settings.redis_queue_scrape, timeout=1)
            if payload:
                job_id = payload.get("job_id")
                if job_id:
                    logger.info(f"Dispatching scrape job #{job_id} (queue depth: {scrape_ql})")
                    try:
                        run_scrape_job(job_id)
                    except Exception as e:
                        logger.error(f"Scrape job #{job_id} error: {e}")

        # Verify queue
        verify_ql = queue_length(settings.redis_queue_verify)
        if verify_ql > 0:
            payload = dequeue_job(settings.redis_queue_verify, timeout=1)
            if payload:
                job_id = payload.get("job_id")
                limit = payload.get("limit", 500)
                logger.info(f"Dispatching verify batch job_id={job_id} limit={limit}")
                try:
                    run_verify_batch(job_id=job_id, limit=limit)
                except Exception as e:
                    logger.error(f"Verify batch error: {e}")

        time.sleep(0.5)

    logger.info("Queue dispatcher stopped.")


if __name__ == "__main__":
    main()
