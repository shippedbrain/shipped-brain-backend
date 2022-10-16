from sqlalchemy import Column, Integer, String, DateTime, Text
from db.db_config import Base
from datetime import datetime
import bcrypt

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False)
    username = Column(String(255), unique = True)
    email = Column(String(255), unique = True)
    description = Column(Text)
    password = Column(String(255), nullable = False)
    created_at = Column(DateTime(), default = datetime.now())
    updated_at = Column(DateTime(), default = datetime.now(), onupdate = datetime.now())
    models_count = None
    model_versions_count = None
    api_calls_count = None

    def hash_pw(self, pw):
        self.password = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())

        self.password = self.password.decode('utf-8')

    def check_pw(self, pw):
        """
        pw: plain text\n
        self.password: hashed\n
        Checks if provided pw parameter equals hashed password
        """

        return bcrypt.checkpw(pw.encode('utf-8'), self.password.encode('utf-8'))