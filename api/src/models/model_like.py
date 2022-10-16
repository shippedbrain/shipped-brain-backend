from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from db.db_config import Base
from models.registered_model import RegisteredModel
from models.user import User

class ModelLike(Base):
    __tablename__ = 'model_likes'

    model_name = Column(String(256), ForeignKey(RegisteredModel.name), primary_key = True)
    user_id = Column(Integer, ForeignKey(User.id), primary_key = True)
    created_at = Column(DateTime, nullable=False)

    def to_dict(self):
        return {
            'model_name': self.model_name,
            'user_id': self.user_id,
            'created_at': self.created_at
        }