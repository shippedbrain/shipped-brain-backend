from datetime import datetime, timedelta
from sqlalchemy import Column
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime, Integer, String, Text
from db.db_config import Base

class ModelRequest(Base):
    __tablename__ = 'model_requests'

    CANCELLED: str = 'cancelled'
    OPEN: str = 'open'
    CLOSED: str = 'closed'
    VALID_STATUS_LIST = [ 
        CANCELLED,
        OPEN,
        CLOSED
    ]
    RECENT_REQUEST_TIME = 48 # In hours

    id = Column(Integer, primary_key=True)
    requested_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    input_data = Column(Text)
    output_data = Column(Text)
    prize = Column(Text)
    status = Column(String(255))
    fulfilled_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    fulfilled_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())

    def is_recent_request(self, created_at) -> bool:
        '''
            Checks if model request was created in the last 24 hours

            :param created_at: Date when model request was created

            :return: True if request was made in the last 24 hours, else False
        '''
        now = datetime.now()
        
        return True if now - timedelta(hours = self.RECENT_REQUEST_TIME) <= created_at <= now else False