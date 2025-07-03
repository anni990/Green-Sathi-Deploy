import mysql.connector
import os
from dotenv import load_dotenv
from flask import Flask
from models.chat_model import db

load_dotenv()

def connect_to_mysql():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'db'),
        user=os.getenv('DB_USER', 'GreenSathi'),
        password=os.getenv('DB_PASSWORD', 'GreenSathi@990'),
    )

def create_database():
    conn = connect_to_mysql()
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    db_name = os.getenv('DB_NAME', 'flaskdb')
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    
    print(f"Database '{db_name}' created or already exists")
    
    cursor.close()
    conn.close()

def create_tables():
    # Create a Flask app for database initialization
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(
        os.getenv('DB_USER', 'GreenSathi'),
        os.getenv('DB_PASSWORD', 'GreenSathi@990'),
        os.getenv('DB_HOST', 'db'),
        os.getenv('DB_NAME', 'flaskdb')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with this app
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    create_database()
    create_tables() 