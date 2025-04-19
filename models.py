from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    plan = db.Column(db.String(20), default='free')
    clips_generated_this_month = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    clips = db.relationship('Clip', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_clip_limit(self):
        if self.plan == 'free':
            return 3
        elif self.plan == 'premium':
            return 20
        elif self.plan == 'pro':
            return float('inf')  # Illimité
        return 0
    
    def can_generate_clip(self, mode='short'):
        # Vérifier si l'utilisateur a atteint sa limite mensuelle
        if self.clips_generated_this_month >= self.get_clip_limit():
            return False
        
        # Vérifier si l'utilisateur peut générer des clips longs
        if mode == 'long' and self.plan == 'free':
            return False
        
        return True
    
    def increment_clip_count(self):
        self.clips_generated_this_month += 1
        db.session.commit()

class Clip(db.Model):
    __tablename__ = 'clips'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    youtube_url = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200))
    channel = db.Column(db.String(100))
    duration = db.Column(db.Integer)  # Durée en secondes
    thumbnail = db.Column(db.String(200))
    mode = db.Column(db.String(10), default='short')  # 'short' ou 'long'
    transitions = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'downloading', 'processing', 'completed', 'error'
    error = db.Column(db.Text)
    file_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'youtube_url': self.youtube_url,
            'title': self.title,
            'channel': self.channel,
            'duration': self.duration,
            'thumbnail': self.thumbnail,
            'mode': self.mode,
            'transitions': self.transitions,
            'status': self.status,
            'error': self.error,
            'file_path': self.file_path,
            'created_at': self.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT') if self.created_at else None,
            'completed_at': self.completed_at.strftime('%a, %d %b %Y %H:%M:%S GMT') if self.completed_at else None
        }
