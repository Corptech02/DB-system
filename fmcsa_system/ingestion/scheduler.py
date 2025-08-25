"""
Scheduled data refresh for FMCSA carriers.
Runs daily updates to keep carrier data current.
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from dotenv import load_dotenv

from .fmcsa_client import FMCSAClient
from .ingestion_pipeline import IngestionPipeline, IngestionStats
from ..database import initialize_database, close_database, refresh_statistics

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class IngestionScheduler:
    """
    Manages scheduled ingestion of FMCSA data.
    Supports both full refresh and incremental updates.
    """
    
    def __init__(
        self,
        enable_scheduler: bool = None,
        refresh_hour: int = None,
        refresh_minute: int = None
    ):
        """
        Initialize scheduler.
        
        Args:
            enable_scheduler: Whether to enable scheduling
            refresh_hour: Hour to run refresh (0-23)
            refresh_minute: Minute to run refresh (0-59)
        """
        # Load configuration from environment
        self.enabled = enable_scheduler
        if self.enabled is None:
            self.enabled = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
        
        self.refresh_hour = refresh_hour
        if self.refresh_hour is None:
            self.refresh_hour = int(os.getenv("REFRESH_SCHEDULE_HOUR", "2"))
        
        self.refresh_minute = refresh_minute
        if self.refresh_minute is None:
            self.refresh_minute = int(os.getenv("REFRESH_SCHEDULE_MINUTE", "0"))
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()
        
        # Track last run information
        self.last_run_time: Optional[datetime] = None
        self.last_run_stats: Optional[IngestionStats] = None
        self.last_run_success: bool = False
        
        # Setup event listeners
        self.scheduler.add_listener(
            self._job_executed,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error,
            EVENT_JOB_ERROR
        )
    
    def start(self):
        """Start the scheduler."""
        if not self.enabled:
            logger.info("Scheduler is disabled")
            return
        
        # Schedule daily refresh
        self.scheduler.add_job(
            self.run_daily_refresh,
            CronTrigger(
                hour=self.refresh_hour,
                minute=self.refresh_minute
            ),
            id="daily_refresh",
            name="Daily FMCSA Data Refresh",
            replace_existing=True,
            max_instances=1  # Prevent overlapping runs
        )
        
        # Schedule hourly incremental updates (optional)
        if os.getenv("ENABLE_INCREMENTAL_UPDATES", "false").lower() == "true":
            self.scheduler.add_job(
                self.run_incremental_update,
                CronTrigger(minute=30),  # Run at :30 every hour
                id="hourly_incremental",
                name="Hourly Incremental Update",
                replace_existing=True,
                max_instances=1
            )
        
        # Schedule statistics refresh
        self.scheduler.add_job(
            self.refresh_statistics,
            CronTrigger(
                hour=self.refresh_hour + 2,  # 2 hours after data refresh
                minute=0
            ),
            id="stats_refresh",
            name="Statistics Refresh",
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        
        logger.info(
            f"Scheduler started. Daily refresh at {self.refresh_hour:02d}:{self.refresh_minute:02d}"
        )
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    async def run_daily_refresh(self):
        """
        Run full daily refresh of FMCSA data.
        This fetches all carrier records and updates the database.
        """
        logger.info("Starting daily FMCSA data refresh")
        start_time = datetime.now()
        
        try:
            # Initialize database
            await initialize_database()
            
            # Create ingestion pipeline
            client = FMCSAClient()
            pipeline = IngestionPipeline(
                fmcsa_client=client,
                batch_size=1000
            )
            
            # Run full ingestion
            stats = await pipeline.run_full_ingestion(
                progress_callback=self._progress_callback
            )
            
            # Update tracking
            self.last_run_time = start_time
            self.last_run_stats = stats
            self.last_run_success = True
            
            # Log results
            logger.info(
                f"Daily refresh completed successfully. "
                f"Processed {stats.total_fetched:,} records in {stats.duration_seconds/60:.1f} minutes"
            )
            
            # Send notification if configured
            await self._send_notification(
                "FMCSA Daily Refresh Complete",
                f"Successfully processed {stats.total_fetched:,} records\n"
                f"Inserted: {stats.total_inserted:,}\n"
                f"Updated: {stats.total_updated:,}\n"
                f"Errors: {stats.total_errors:,}\n"
                f"Duration: {stats.duration_seconds/60:.1f} minutes"
            )
            
        except Exception as e:
            logger.error(f"Daily refresh failed: {e}", exc_info=True)
            self.last_run_success = False
            
            # Send error notification
            await self._send_notification(
                "FMCSA Daily Refresh Failed",
                f"Error: {str(e)}\n"
                f"Time: {datetime.now()}"
            )
            
            raise
        
        finally:
            # Clean up
            await close_database()
    
    async def run_incremental_update(self):
        """
        Run incremental update for recently modified records.
        This is more efficient than full refresh for frequent updates.
        """
        logger.info("Starting incremental FMCSA update")
        
        try:
            await initialize_database()
            
            # Determine cutoff date (last 24 hours)
            since_date = datetime.now() - timedelta(days=1)
            
            # Create pipeline
            client = FMCSAClient()
            pipeline = IngestionPipeline(
                fmcsa_client=client,
                batch_size=500
            )
            
            # Run incremental update
            stats = await pipeline.run_incremental_update(
                since_date=since_date,
                progress_callback=self._progress_callback
            )
            
            logger.info(
                f"Incremental update completed. "
                f"Updated {stats.total_updated:,} records"
            )
            
        except Exception as e:
            logger.error(f"Incremental update failed: {e}")
            # Don't raise - incremental updates are less critical
        
        finally:
            await close_database()
    
    async def refresh_statistics(self):
        """Refresh materialized views and statistics."""
        logger.info("Refreshing carrier statistics")
        
        try:
            await initialize_database()
            await refresh_statistics()
            logger.info("Statistics refreshed successfully")
            
        except Exception as e:
            logger.error(f"Statistics refresh failed: {e}")
        
        finally:
            await close_database()
    
    async def run_manual_refresh(self) -> Dict[str, Any]:
        """
        Trigger manual refresh (for admin endpoints).
        
        Returns:
            Refresh results
        """
        logger.info("Manual refresh triggered")
        
        try:
            await self.run_daily_refresh()
            
            return {
                "status": "success",
                "start_time": self.last_run_time,
                "stats": self.last_run_stats.to_dict() if self.last_run_stats else None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status and last run information.
        
        Returns:
            Status dictionary
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            })
        
        return {
            "enabled": self.enabled,
            "running": self.scheduler.running,
            "jobs": jobs,
            "last_run": {
                "time": self.last_run_time.isoformat() if self.last_run_time else None,
                "success": self.last_run_success,
                "stats": self.last_run_stats.to_dict() if self.last_run_stats else None
            }
        }
    
    def _progress_callback(self, current: int, total: int):
        """Progress callback for ingestion."""
        if current % 100000 == 0:
            logger.info(f"Refresh progress: {current:,}/{total:,} ({current/total*100:.1f}%)")
    
    def _job_executed(self, event):
        """Handle successful job execution."""
        logger.info(f"Job {event.job_id} executed successfully")
    
    def _job_error(self, event):
        """Handle job execution error."""
        logger.error(f"Job {event.job_id} failed: {event.exception}")
    
    async def _send_notification(self, subject: str, message: str):
        """
        Send notification (email, Slack, etc.).
        
        Args:
            subject: Notification subject
            message: Notification message
        """
        # This would integrate with your notification service
        # For now, just log
        logger.info(f"Notification: {subject}")
        
        # Example email integration
        if os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "false").lower() == "true":
            # Would send email here
            pass
        
        # Example Slack integration
        if os.getenv("SLACK_WEBHOOK_URL"):
            # Would post to Slack here
            pass


# Global scheduler instance
scheduler = IngestionScheduler()


def start_scheduler():
    """Start the global scheduler."""
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler."""
    scheduler.stop()


async def trigger_manual_refresh() -> Dict[str, Any]:
    """Trigger manual data refresh."""
    return await scheduler.run_manual_refresh()


def get_scheduler_status() -> Dict[str, Any]:
    """Get scheduler status."""
    return scheduler.get_status()


if __name__ == "__main__":
    """Run scheduler standalone for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Start scheduler
    scheduler = IngestionScheduler()
    scheduler.start()
    
    try:
        # Keep running
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted")
        scheduler.stop()