from sqlalchemy import Column, Integer, ForeignKey
from db.db_config import Base
from models.user import User

class UserHashtag(Base):
    __tablename__ = 'user_hashtags'
    
    hashtag_id = Column(Integer, ForeignKey('hashtags.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), primary_key=True, nullable=False) 