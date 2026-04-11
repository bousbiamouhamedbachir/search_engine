from datetime import datetime
from app import db

class File(db.Model):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.String(255), nullable=False)
    url = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    indexed_at = db.Column(db.DateTime)
    indexed = db.Column(db.Integer, default=0)

class Word(db.Model):
    __tablename__ = 'word'
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(255), unique=True, nullable=False)

class Redundace(db.Model):
    __tablename__ = 'redundace'
    word = db.Column(db.Integer, db.ForeignKey('word.id'), primary_key=True)
    file = db.Column(db.Integer, db.ForeignKey('file.id'), primary_key=True)
    wheight = db.Column(db.Float, nullable=False)
    
    word_obj = db.relationship('Word', backref='redundances')
    file_obj = db.relationship('File', backref='redundances')

class Search(db.Model):
    __tablename__ = 'search'
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text, nullable=False)
    at = db.Column(db.DateTime, default=datetime.utcnow)

class Result(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.Integer, primary_key=True)
    search = db.Column(db.Integer, db.ForeignKey('search.id'), nullable=False)
    file = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    clicked = db.Column(db.Integer, default=0)

    search_obj = db.relationship('Search', backref='results')
    file_obj = db.relationship('File', backref='results')
