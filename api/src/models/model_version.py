from sqlalchemy import Column, Integer, String, BIGINT
from db.db_config import Base

class ModelVersion(Base):
    __tablename__ = 'model_versions'

    # TODO NOT WORKING! === ForeignKey('registered_models.name', onupdate='CASCADE')
    name = Column(String(256), primary_key=True, nullable=False)
    version = Column(Integer, primary_key=True, nullable=False)
    creation_time = Column(BIGINT)
    last_updated_time = Column(BIGINT) 
    description = Column(String(5000)) 
    user_id = Column(String(256)) 
    current_stage = Column(String(20))
    source  = Column(String(500))
    run_id  = Column(String(32), nullable=False)
    status  = Column(String(20))
    status_message = Column(String(500))
    run_link = Column(String(500))