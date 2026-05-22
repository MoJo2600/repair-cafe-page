"""
Background scheduler tasks.
"""
from datetime import datetime, timedelta
from apscheduler.triggers.cron import CronTrigger


def is_third_saturday(date):
    """
    Check if the given date is the third Saturday of the month.
    
    Args:
        date: datetime object to check
    
    Returns:
        bool: True if date is third Saturday, False otherwise
    """
    # Find the first day of the month
    first_day = date.replace(day=1)
    
    # Calculate the first Saturday of the month
    first_saturday = first_day + timedelta(days=(5 - first_day.weekday() + 7) % 7)
    
    # Calculate the third Saturday of the month
    third_saturday = first_saturday + timedelta(weeks=2)
    
    # Check if the provided date is the third Saturday
    return date.date() == third_saturday.date()


def create_export_mail_cron_job(app, send_mail_export_func):
    """
    Create the export mail cron job function.
    
    Args:
        app: Flask application instance
        send_mail_export_func: Function to call for sending export mail
    
    Returns:
        Function to be used as cron job
    """
    def send_export_mail_cron():
        """Cron job to send export mail on third Saturday of each month."""
        with app.app_context():
            if app.config.get('EMAIL_ENABLED'):
                today = datetime.today()
                if is_third_saturday(today):
                    print('Today is the third Saturday of the month!')
                    send_mail_export_func(cron=True)
            else:
                print('Mail sending is disabled.')
    
    return send_export_mail_cron


def setup_scheduler(scheduler, app, send_mail_export_func):
    """
    Set up scheduled jobs.
    
    Args:
        scheduler: APScheduler BackgroundScheduler instance
        app: Flask application instance
        send_mail_export_func: Function to call for sending export mail
    """
    # Create and add the export mail cron job
    export_mail_job = create_export_mail_cron_job(app, send_mail_export_func)
    
    scheduler.add_job(
        func=export_mail_job,
        trigger=CronTrigger(hour=20, minute=0, day_of_week='sat'),
        id='export_mail_cron',
        name='Send export mail on Saturdays at 20:00',
        replace_existing=True
    )
    
    print("Scheduler jobs configured")


def start_scheduler(scheduler):
    """
    Start the background scheduler if not already running.
    
    Args:
        scheduler: APScheduler BackgroundScheduler instance
    """
    if not scheduler.running:
        scheduler.start()
        print("Background scheduler started")
