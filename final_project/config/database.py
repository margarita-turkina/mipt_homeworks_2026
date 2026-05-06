"""Database config package"""

import os
from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


load_dotenv()

# SQLite database configuration
database_url = os.getenv('DATABASE_URL', 'sqlite:///./mipt.db')

engine = create_engine(database_url, connect_args={'check_same_thread': False}, echo=False)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session():
    """Session generator for dependency injection."""
    session = Session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    else:
        session.commit()
    finally:
        session.close()
