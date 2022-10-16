from sqlalchemy import Column, Integer, String
from db.db_config import Base

class Hashtag(Base):
    __tablename__ = 'hashtags'
    
    CATEGORY: str = 'category'
    HASHTAG: str = 'hashtag'
    FRAMEWORK: str = 'framework'

    id = Column(Integer, primary_key=True)
    key = Column(String(32), nullable=False) # Application defined
    value = Column(String(64), nullable=False)

    # TODO add delete cascade
    
    def to_dict(self):
        return {'id': self.id, 'key': self.key, 'value': self.value}
        
    # TODO validate key
    # key: 'category', 'hashtag', 'framework'