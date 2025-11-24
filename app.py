import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)


@app.route('/')
def hello():
    return 'Hello, World!'


@app.route('/test-db')
def test_db():
    """Test database connection"""
    try:
        # Try to execute a simple query
        result = db.session.execute(db.text('SELECT version();'))
        version = result.fetchone()
        return f'Database connected! PostgreSQL version: {version[0] if version else "unknown"}'
    except Exception as e:
        return f'Database error: {str(e)}', 500


if __name__ == '__main__':
    app.run(debug=True)
