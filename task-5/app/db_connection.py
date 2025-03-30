import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from dotenv import load_dotenv

load_dotenv()

# Database configuration
CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'localhost')
CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', '9042'))
CASSANDRA_USERNAME = os.getenv('CASSANDRA_USERNAME')
CASSANDRA_PASSWORD = os.getenv('CASSANDRA_PASSWORD')
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'online_store')

# Setup connection
auth_provider = PlainTextAuthProvider(
    username=CASSANDRA_USERNAME,
    password=CASSANDRA_PASSWORD
)
cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT, auth_provider=auth_provider)
session = cluster.connect()

def setup_database():
    """Create keyspace and tables"""
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
    """)
    
    session.set_keyspace(CASSANDRA_KEYSPACE)
    
    session.execute("""
        CREATE TABLE IF NOT EXISTS items (
            category text,
            id uuid,
            name text,
            price decimal,
            manufacturer text,
            properties map<text, text>,
            PRIMARY KEY ((category), price, id)
        )
    """)
    
    session.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            customer_name text,
            order_id uuid,
            order_date timestamp,
            products list<uuid>,
            total_value decimal,
            PRIMARY KEY ((customer_name), order_date, order_id)
        )
    """)
    
    session.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS items_by_name AS
        SELECT * FROM items
        WHERE category IS NOT NULL AND name IS NOT NULL AND price IS NOT NULL AND id IS NOT NULL
        PRIMARY KEY ((category, name), price, id)
    """)
    
    session.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS items_by_manufacturer AS
        SELECT * FROM items
        WHERE category IS NOT NULL AND manufacturer IS NOT NULL AND price IS NOT NULL AND id IS NOT NULL
        PRIMARY KEY ((category, manufacturer), price, id)
    """)

def cleanup_database(truncate_tables=False):
    """Cleanup the database for testing
    
    Args:
        truncate_tables: If True, truncate tables, otherwise drop materialized views and tables
    """
    session.set_keyspace(CASSANDRA_KEYSPACE)
    
    if truncate_tables:
        # Truncate tables to keep structure but remove data
        session.execute("TRUNCATE items")
        session.execute("TRUNCATE orders")
    else:
        # Drop materialized views first (required before dropping the base table)
        session.execute("DROP MATERIALIZED VIEW IF EXISTS items_by_name")
        session.execute("DROP MATERIALIZED VIEW IF EXISTS items_by_manufacturer")
        
        # Drop tables
        session.execute("DROP TABLE IF EXISTS items")
        session.execute("DROP TABLE IF EXISTS orders")

def describe_table(table_name: str):
    """Show table structure"""
    result = session.execute(f"DESCRIBE {table_name}")
    print(f"\nTable structure for {table_name}:")
    for row in result:
        print(row) 