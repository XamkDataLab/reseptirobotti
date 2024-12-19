import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables from .env file
load_dotenv()

def connect_to_db():
    """Establish a connection to the PostgreSQL database using environment variables."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432")  # Default port 5432
        )
        return conn
    except Exception as e:
        raise Exception(f"Error connecting to database: {e}")
