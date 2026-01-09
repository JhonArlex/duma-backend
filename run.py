#!/usr/bin/env python
"""
Entry point for running the Flask application.
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
