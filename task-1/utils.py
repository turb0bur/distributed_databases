import os
import logging
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def ensure_row_exists():
    """Ensure the row for user_id = 1 exists in the database, or insert it if it does not."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT INTO user_counter (user_id, counter, version)
                    VALUES (1, 0, 1)
                    ON CONFLICT (user_id)
                    DO UPDATE SET counter = EXCLUDED.counter, version = EXCLUDED.version
                """)
                conn.commit()
            except Exception as e:
                logging.error(f"Error ensuring row existence: {e}")
