from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from db.db_config import Base
from models.registered_model import RegisteredModel
from models.user import User

class ModelComment(Base):
    __tablename__ = 'model_comments'

    id = Column(Integer, primary_key=True)
    model_name = Column(String(256), ForeignKey(RegisteredModel.name, onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id, onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now())
    