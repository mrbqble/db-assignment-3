# PythonAnywhere Deployment Guide

This guide will help you deploy this Flask application on PythonAnywhere.

## Prerequisites

- A PythonAnywhere account (free tier available)
- Your project code in a Git repository (GitHub, GitLab, etc.)

## Step 1: Clone Your Repository

1. Open a Bash console in PythonAnywhere
2. Navigate to your home directory:
   ```bash
   cd ~
   ```
3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git db-assignment-3
   cd db-assignment-3
   ```

## Step 2: Set Up Virtual Environment

1. Create a virtual environment:

   ```bash
   python3.10 -m venv venv
   ```

   (Use the Python version available on PythonAnywhere, typically 3.10 or 3.11)

2. Activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Step 3: Configure Environment Variables

1. Create a `.env` file in your project root:

   ```bash
   nano .env
   ```

2. Add your environment variables:

   ```
   DATABASE_URL=mysql+pymysql://yourusername:yourpassword@yourusername.mysql.pythonanywhere-services.com/yourusername$dbname
   FLASK_SECRET_KEY=your-secret-key-here
   ```

   **Important Notes:**

   - Replace `yourusername` with your PythonAnywhere username
   - Replace `yourpassword` with your MySQL password
   - Replace `dbname` with your database name
   - For the secret key, generate a secure random string

3. Save and exit (Ctrl+X, then Y, then Enter)

## Step 4: Set Up MySQL Database

1. Go to the **Databases** tab in PythonAnywhere dashboard
2. Create a new MySQL database (if you haven't already)
3. Note your database credentials:

   - Hostname: `yourusername.mysql.pythonanywhere-services.com`
   - Username: Your PythonAnywhere username
   - Database name: `yourusername$dbname`
   - Password: (set when creating the database)

4. Initialize the database by running:
   ```bash
   python script.py
   ```
   This will create all tables and insert sample data.

## Step 5: Configure WSGI File

1. Go to the **Web** tab in PythonAnywhere dashboard
2. Click on your web app (or create a new one)
3. Scroll down to the **WSGI configuration file** section
4. Click on the file path (usually `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
5. Replace the entire contents with:

   ```python
   import sys
   import os

   # Add your project directory to the Python path
   project_home = '/home/yourusername/db-assignment-3'
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   # Activate virtual environment
   activate_this = '/home/yourusername/db-assignment-3/venv/bin/activate_this.py'
   if os.path.exists(activate_this):
       exec(open(activate_this).read(), {'__file__': activate_this})

   # Import the Flask app
   from app import app as application
   ```

   **Important:** Replace `yourusername` with your actual PythonAnywhere username in both paths.

6. Save the file

## Step 6: Configure Static Files and Source Code

1. In the **Web** tab, scroll to **Static files** section
2. Add a mapping:

   - **URL:** `/static/`
   - **Directory:** `/home/yourusername/db-assignment-3/static/` (if you have static files)

3. Scroll to **Source code** section
4. Set the working directory:
   - **Directory:** `/home/yourusername/db-assignment-3`

## Step 7: Reload Your Web App

1. Click the green **Reload** button at the top of the Web tab
2. Your app should now be live at `https://yourusername.pythonanywhere.com`

## Troubleshooting

### Database Connection Issues

- Verify your `DATABASE_URL` in `.env` is correct
- Check that your MySQL database is running
- Ensure your database credentials are correct

### Import Errors

- Make sure your virtual environment is activated in the WSGI file
- Verify all dependencies are installed: `pip list`
- Check that the project path in WSGI file is correct

### Application Errors

- Check the **Error log** in the Web tab for detailed error messages
- Verify your `.env` file is in the project root
- Make sure the database tables are created (run `script.py`)

### Static Files Not Loading

- Verify static files mapping in Web tab
- Check that your templates are in the `templates/` directory
- Ensure file permissions are correct

## Additional Notes

- **Free tier limitations:** Free accounts have limited resources and may have restrictions
- **HTTPS:** Your app will be served over HTTPS automatically
- **Custom domain:** Paid accounts can use custom domains
- **Database backups:** Regularly backup your database through the Databases tab

## Testing Locally

You can test the WSGI configuration locally:

```bash
python wsgi.py
```

However, for production, always use PythonAnywhere's WSGI configuration file.
