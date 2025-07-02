from datetime import datetime
from .database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum('farmer', 'dealer', 'admin'), nullable=False, default='farmer')
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships with foreign keys
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True)
    plant_images = db.relationship('PlantImage', backref='user', lazy=True)
    soil_reports = db.relationship('SoilReport', backref='user', lazy=True)
    crops_for_sale = db.relationship('CropForSale', backref='farmer', lazy=True, foreign_keys='CropForSale.farmer_id')
    bids = db.relationship('Bid', backref='dealer', lazy=True, foreign_keys='Bid.dealer_id')
    
    __table_args__ = (
        db.Index('idx_role', 'role'),
        db.Index('idx_created_at', 'created_at'),
    ) 