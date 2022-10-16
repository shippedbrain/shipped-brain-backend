from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from db.db_config import Base
from datetime import datetime
from models.user import User
from uuid import uuid4
from hashlib import md5

class PasswordReset(Base):
    __tablename__ = 'password_resets'

    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey(User.id), nullable = False)
    user_email = Column(String(255), nullable = False)
    reset_token = Column(String(255), nullable = False)
    created_at = Column(DateTime(), default = datetime.now())

    def generate_token(self) -> str:
        '''
            Generates a secure token based on uuid and md5 of current datetime
        '''
        self.reset_token = str(uuid4()) + md5(f'{datetime.now()}'.encode('utf-8')).hexdigest()

        return self.reset_token

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'reset_token': self.reset_token,
            'created_at': self.created_at
        }