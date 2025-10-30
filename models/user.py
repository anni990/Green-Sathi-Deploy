from datetime import datetime
from .database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    preferred_language = db.Column(db.Enum('english', 'hindi', 'bhojpuri', 'bundelkhandi', 'marathi', 'haryanvi', 'bengali', 'tamil', 'telugu', 'kannada', 'gujarati', 'urdu', 'malayalam', 'punjabi'), default='hindi')
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    last_login = db.Column(db.TIMESTAMP, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    user_role = db.Column(db.Enum('farmer', 'dealer'), nullable=False, default='farmer')
    
    # Relationships with foreign keys
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True)
    plant_images = db.relationship('PlantImage', backref='user', lazy=True)
    soil_reports = db.relationship('SoilReport', backref='user', lazy=True)
    crops_for_sale = db.relationship('CropForSale', backref='farmer', lazy=True, foreign_keys='CropForSale.farmer_id')
    bids = db.relationship('Bid', backref='dealer', lazy=True, foreign_keys='Bid.dealer_id')
    
    __table_args__ = (
        db.Index('idx_user_role', 'user_role'),
        db.Index('idx_created_at', 'created_at'),
    ) 