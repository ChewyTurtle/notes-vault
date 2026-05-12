"""
models.py
Defines the SQLAlchemy database models for the Notes Vault API.
Contains the Note model and its serialization logic.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Note(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.Text, nullable = False)
    title = db.Column(db.Text, nullable = True)
    created_at = db.Column(db.DateTime, default = lambda: datetime.now(timezone.utc))

    def to_dict(self):
        new_dict = {}
        try:
            new_dict['id'] = self.id
            new_dict['content'] = self.content
            new_dict['title'] = self.title
            new_dict['created_at'] = self.created_at.isoformat()
        except Exception as e:
            print(f"Error creating dict from Database data: {e}")
        
        return new_dict
    