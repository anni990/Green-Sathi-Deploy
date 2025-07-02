from datetime import datetime
from .database import db

class Commodity(db.Model):
    __tablename__ = 'commodities_names'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    crops = db.relationship('CropForSale', backref='commodity', lazy=True)

class District(db.Model):
    __tablename__ = 'districts_names'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    crops = db.relationship('CropForSale', backref='district', lazy=True)
    
    __table_args__ = (
        db.UniqueConstraint('name', 'state', name='unique_district_state'),
    )

class CropForSale(db.Model):
    __tablename__ = 'crops_for_sale'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    commodity_id = db.Column(db.Integer, db.ForeignKey('commodities_names.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.Enum('kg', 'quintal', 'ton'), nullable=False, default='kg')
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts_names.id'), nullable=False)
    expected_date = db.Column(db.Date, nullable=False)
    image_path = db.Column(db.String(255))
    description = db.Column(db.Text)
    status = db.Column(db.Enum('active', 'closed', 'sold'), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bids = db.relationship('Bid', backref='crop', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_status', 'status'),
        db.Index('idx_created_at', 'created_at'),
    )

class Bid(db.Model):
    __tablename__ = 'bids'
    
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops_for_sale.id'), nullable=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bid_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('pending', 'accepted', 'rejected'), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_crop_status', 'crop_id', 'status'),
        db.Index('idx_dealer', 'dealer_id'),
    ) 