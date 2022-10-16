from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Load env variables
load_dotenv()

# Engine setup
db_url = os.getenv('DB_URL')

print(f'[DEBUG] Using DB URL {db_url}')
print('[INFO] Creating database engine')
engine = create_engine(db_url)

Session = sessionmaker(bind = engine)
session = Session()

Base = declarative_base()