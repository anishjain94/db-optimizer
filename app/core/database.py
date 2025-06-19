from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .config import get_settings
from contextlib import contextmanager

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # Maximum number of connections to keep
    max_overflow=10,  # Maximum number of connections that can be created beyond pool_size
    pool_timeout=30,  # Seconds to wait before giving up on getting a connection from the pool
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True  # Enable connection health checks
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Global connection pool
_connection_pool = None

def init_db():
    """Initialize the database connection pool."""
    global _connection_pool
    try:
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _connection_pool = engine
        print("Database connection pool initialized successfully")
    except Exception as e:
        print(f"Error initializing database connection pool: {e}")
        raise

@contextmanager
def get_db_connection():
    """Get a database connection from the pool."""
    if not _connection_pool:
        raise Exception("Database connection pool not initialized")
    
    connection = None
    try:
        connection = _connection_pool.connect()
        yield connection
    finally:
        if connection:
            connection.close()

def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
