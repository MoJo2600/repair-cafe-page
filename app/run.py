"""
Main application entry point for RepairCafe Flask application.
This file initializes the app and starts the scheduler.
"""
import os
import time

# Import the application factory
from app import create_app
from app.extensions import scheduler
from app.tasks.scheduler import setup_scheduler, start_scheduler as start_scheduler_func
from app.services.pdf_service import PDFService

# Create the Flask application
app = create_app()

# Initialize services
pdf_service = PDFService()


def init_app_resources():
    """Initialize app resources that should not load during CLI commands."""
    # Initialize PDFSigner (triggers file check and prints message)
    pdf_service.signer
    app.logger.info("Application resources initialized")


def start_scheduler_with_app():
    """Start the background scheduler with app context."""
    # Import the mail export function
    from app.web.routes import send_mail_export
    
    setup_scheduler(scheduler, app, send_mail_export)
    start_scheduler_func(scheduler)


# Start scheduler when deployed with WSGI server (but not during Flask CLI commands)
if os.environ.get('START_SCHEDULER') == '1' and not os.environ.get('FLASK_RUN_FROM_CLI'):
    init_app_resources()
    start_scheduler_with_app()


if __name__ == "__main__":
    import sys
    try:
        # Initialize resources and start the scheduler when running the app directly
        init_app_resources()
        start_scheduler_with_app()
        
        # Get port from command line or use default from config
        port = int(sys.argv[1]) if len(sys.argv) > 1 else app.config.get('PORT', 5000)
        
        print(f"Starting RepairCafe application on port {port}")
        print(f"Environment: {'Development' if app.config.get('DEBUG') else 'Production'}")
        print(f"Registered blueprints: {list(app.blueprints.keys())}")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=app.config.get('DEBUG', False),
            threaded=True
        )
    except KeyboardInterrupt:
        time.sleep(5)
        exit()
