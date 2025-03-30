# Task - Cassandra Online Store Implementation

This project implements a model of an online store that sells various products with different sets of properties using Apache Cassandra. It demonstrates Cassandra data modeling concepts, including primary keys, materialized views, and various query patterns.

## Requirements
- Learn Cassandra data modeling concepts and best practices
- Model different types of products with varying properties using maps and indexes
- Implement orders with product references and customer information
- Create materialized views for efficient querying
- Implement TTL and JSON support

## Setup and Running

### Prerequisites
- Docker and Docker Compose installed on your system
- Git to clone the repository
- (Optional) DataStax DevCenter or cqlsh for database management

### Environment Variables
The application uses environment variables for configuration. These are defined in the `.env` file. A sample `.env.example` file is provided as a template.

| Variable | Description | Default Value |
|----------|-------------|---------------|
| CASSANDRA_USERNAME | Cassandra username | cassandra |
| CASSANDRA_PASSWORD | Cassandra password | cassandra |
| CASSANDRA_PORT | Port to expose Cassandra on host | 9042 |
| CASSANDRA_KEYSPACE | Cassandra keyspace name | online_store |
| APP_PORT | Application port | 8000 |

### Running the Application
1. Clone the repository
2. Navigate to the project directory
3. Copy the example environment file and modify if needed:
   ```bash
   cp .env.example .env
   ```
4. Start the application with Docker Compose:
   ```bash
   docker-compose up --build
   ```
5. The application will automatically:
   - Start a Cassandra server
   - Run the Python application that executes all required operations
   - Output the results to the console

### Connecting to Cassandra with cqlsh
To connect to the Cassandra database using cqlsh:

1. Open a terminal
2. Source the environment variables and run cqlsh:
   ```bash
   source .env
   docker exec -it ddb-task5-cassandra cqlsh -u $CASSANDRA_USERNAME -p $CASSANDRA_PASSWORD
   ```
3. Once connected, select the keyspace:
   ```sql
   USE online_store;
   ```
   Or connect directly to the keyspace:
   ```bash
   source .env
   docker exec -it ddb-task5-cassandra cqlsh -u $CASSANDRA_USERNAME -p $CASSANDRA_PASSWORD -k $CASSANDRA_KEYSPACE
   ```
4. Now you can:
   - Browse tables: `DESCRIBE TABLES;`
   - Describe specific tables: `DESCRIBE items;` or `DESCRIBE orders;`
   - Execute CQL queries: `SELECT * FROM items LIMIT 5;`
   - View table structures: `DESCRIBE TABLE items;`
   - Monitor database statistics

### Project Structure
```
.
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile           # Docker configuration for the Python application
├── .env                 # Environment variables for the application
├── .env.example         # Example environment variables file
├── cassandra-config/    # Directory containing Cassandra configuration
│   └── cassandra.yaml   # Custom Cassandra configuration file
└── app/                 # Directory containing the Python application
    ├── main.py          # Main Python script implementing all Cassandra operations
    ├── db_connection.py # Database connection and schema setup
    ├── products.py      # Product management functions
    ├── orders.py        # Order management functions
    ├── seed_data.py     # Sample data generator
    └── requirements.txt # Python dependencies
```

## Implementation Details

### Data Model

1. Products Table:
   ```sql
   CREATE TABLE items (
       category text,
       id uuid,
       name text,
       price decimal,
       manufacturer text,
       properties map<text, text>,
       PRIMARY KEY ((category), price, id)
   );
   ```

2. Orders Table:
   ```sql
   CREATE TABLE orders (
       customer_name text,
       order_id uuid,
       order_date timestamp,
       products list<uuid>,
       total_value decimal,
       PRIMARY KEY ((customer_name), order_date, order_id)
   );
   ```

### Materialized Views
1. Products by Name:
   ```sql
   CREATE MATERIALIZED VIEW items_by_name AS
   SELECT * FROM items
   WHERE category IS NOT NULL AND name IS NOT NULL AND price IS NOT NULL AND id IS NOT NULL
   PRIMARY KEY ((category, name), price, id);
   ```

2. Products by Manufacturer:
   ```sql
   CREATE MATERIALIZED VIEW items_by_manufacturer AS
   SELECT * FROM items
   WHERE category IS NOT NULL AND manufacturer IS NOT NULL AND price IS NOT NULL AND id IS NOT NULL
   PRIMARY KEY ((category, manufacturer), price, id);
   ```

### Key Features
- Efficient querying by category and price
- Materialized views for common query patterns
- Map type for flexible product properties
- TTL support for temporary orders
- JSON support for order data
- No ALLOW FILTERING usage in queries
- Duplicate prevention mechanism for testing

### Data Management
- The application includes a `cleanup_database()` function that can be used to either:
  - Truncate tables (clear data while preserving structure)
  - Drop tables and materialized views completely
- Prior to creating new sample data, the application checks for existing records to prevent duplicates
- This ensures consistent test results regardless of how many times the application is run

### Implemented Features
1. **Table Structure**
   - `describe_table()` - Display table structure using DESCRIBE command

2. **Product Queries**
   - `get_products_by_category()` - Display all products in a category sorted by price
   - `get_products_by_name()` - Find products by name using materialized view
   - `get_products_by_price_range()` - Find products within a price range
   - `get_products_by_manufacturer()` - Find products by manufacturer using materialized view
   - `get_products_by_property_exists()` - Find products with a specific property
   - `get_products_by_property_value()` - Find products with a specific property value

3. **Product Management**
   - `update_product_properties()` - Update all product properties
   - `add_product_property()` - Add a new property to a product
   - `remove_product_property()` - Remove a specific property from a product

4. **Order Queries**
   - `get_customer_orders()` - Display all orders for a customer sorted by date
   - `get_customer_orders_with_product()` - Find orders with a specific product
   - `get_customer_orders_by_date_range()` - Find orders within a date range
   - `get_customer_total_spent()` - Calculate total amount spent by a customer
   - `get_customer_max_order()` - Find order with maximum value for a customer
   - `update_order()` - Modify an existing order
   - `get_order_writetime()` - Display when order was entered into database

5. **Order Management**
   - `create_order()` - Create a new order with optional TTL
   - `get_order_as_json()` - Return an order in JSON format
   - `add_order_from_json()` - Add a new order from JSON data 