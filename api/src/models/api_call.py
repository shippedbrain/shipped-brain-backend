'''
Call performed by user to a specific model
'''
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from db.db_config import Base
from datetime import datetime
from models.user import User
from models.registered_model import RegisteredModel

class ApiCall(Base):
    __tablename__ = 'api_calls'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    model_name = Column(String(256), ForeignKey(RegisteredModel.name), nullable=False)
    call_time = Column(DateTime(), default=datetime.now())

    def to_dict(self):
        
        return {'id': self.id,
                'user_id': self.user_id,
                'model_name': self.model_name,
                'call_time': self.call_time}