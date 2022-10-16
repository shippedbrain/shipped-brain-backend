from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from db.db_config import Base
from datetime import datetime
from models.user import User
from models.model_version import ModelVersion

class ModelUpload(Base):
    __tablename__ = 'model_uploads'

    FINISHED: str = 'finished'
    FAILED: str = 'failed'
    RUNNING: str = 'running'
    QUEUED: str = 'queued'
    CANCELED: str = 'canceled'
    _all_status = [FINISHED, FAILED, RUNNING, QUEUED, CANCELED]

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    model_name = Column(String(256), ForeignKey(ModelVersion.name, ondelete='CASCADE'), nullable=True)
    model_version = Column(Integer, ForeignKey(ModelVersion.name, ondelete='CASCADE'), nullable=True)
    status = Column(String(12), default=RUNNING, nullable=False)
    started_at = Column(DateTime, default=datetime.now(), nullable=False)
    finished_at = Column(DateTime, nullable=True)

    @staticmethod
    def is_valid_status(status: str) -> bool:
        '''Validate status'''

        return any([status == s for s in ModelUpload._all_status])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'status': self.status,
            'started_at': self.started_at,
            'finished_at': self.finished_at
        }

