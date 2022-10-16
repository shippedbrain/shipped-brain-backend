from sqlalchemy import Column, String, BIGINT
from db.db_config import Base


class RegisteredModel(Base):
    __tablename__ = 'registered_models'

    name = Column(String(256), primary_key=True, nullable=False)
    creation_time = Column(BIGINT)
    last_updated_time = Column(BIGINT)
    description = Column(String(5000))

    def to_dict(self):
        return {
            "name": self.name,
            "creation_id": self.creation_time,
            "last_updated_time": self.last_updated_time,
            "description": self.description
        }
