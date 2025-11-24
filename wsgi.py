"""
WSGI configuration file for PythonAnywhere deployment.

Note: PythonAnywhere uses its own WSGI configuration file located at:
/var/www/yourusername_pythonanywhere_com_wsgi.py

This file is provided for reference and local testing.
For actual deployment, use the configuration shown in DEPLOYMENT.md
"""

import sys
import os

# Add the project directory to the Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Optional: Activate virtual environment if running locally
# (PythonAnywhere handles this in their WSGI config)
venv_path = os.path.join(project_home, 'venv', 'bin', 'activate_this.py')
if os.path.exists(venv_path):
    exec(open(venv_path).read(), {'__file__': venv_path})

# Import the Flask app
from app import app

# PythonAnywhere requires the WSGI application to be named 'application'
application = app

if __name__ == "__main__":
    # This is for local testing only
    print("Starting Flask app for local testing...")
    print("For production, use PythonAnywhere's WSGI configuration.")
    app.run(debug=False, host='0.0.0.0', port=5000)

