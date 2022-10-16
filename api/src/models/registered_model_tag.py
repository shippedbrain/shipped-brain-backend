from sqlalchemy import Column, String, ForeignKey
from db.db_config import Base

class RegisteredModelTag(Base):
    __tablename__ = 'registered_model_tags'

    name = Column(String(256), ForeignKey("registered_models.name", onupdate="CASCADE"), primary_key=True, nullable=False)
    key = Column(String(250), primary_key=True, nullable=False)
    value = Column(String(5000))

    def to_dict(self):
        return {
            "name": self.name,
            "key": self.key,
            "value": self.value
        }
