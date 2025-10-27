from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from .models import Base

def get_database_url():
    """Get database URL from environment variables"""
    return os.getenv('DATABASE_URL', 'sqlite:///./integrado.db')

def create_database_engine():
    """Create database engine"""
    database_url = get_database_url()
    
    if database_url.startswith('sqlite'):
        # SQLite specific configuration
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
    else:
        # PostgreSQL, MySQL, etc.
        engine = create_engine(database_url, echo=False)
    
    return engine

def create_tables():
    """Create all database tables"""
    engine = create_database_engine()
    Base.metadata.create_all(bind=engine)
    return engine

def get_session():
    """Get database session"""
    engine = create_database_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

# Global engine instance
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)






