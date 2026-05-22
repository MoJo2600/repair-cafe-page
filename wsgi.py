#!/usr/bin/env python
"""
Main entry point for the RepairCafe Flask application.
Use this file to run the application directly.
"""
from app.run import app

# Export app at module level for Flask CLI and WSGI servers
application = app

if __name__ == "__main__":
    import sys
    
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
