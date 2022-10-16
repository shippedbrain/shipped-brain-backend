from sqlalchemy import Column, Integer, String, ForeignKey
from db.db_config import Base
from models.registered_model import RegisteredModel


class ModelHashtag(Base):
    __tablename__ = 'model_hashtags'

    hashtag_id = Column(Integer, ForeignKey('hashtags.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    model_name = Column(String(256),
                        ForeignKey(RegisteredModel.name, ondelete='CASCADE'),
                        primary_key=True,
                        nullable=False)
