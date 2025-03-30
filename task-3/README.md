# Task - MongoDB Online Store Implementation

This project implements a model of an online store that sells various products with different sets of properties. It demonstrates basic MongoDB operations including querying, updating, and modeling relationships between documents.

## Requirements
- Learn how to perform basic queries to MongoDB
- Model different types of products with varying properties
- Implement orders with referenced items and embedded customer information
- Create a capped collection for store reviews

## Setup and Running

### Prerequisites
- Docker and Docker Compose installed on your system
- Git to clone the repository
- (Optional) DataGrip installed on your system (for database management)

### Environment Variables
The application uses environment variables for configuration. These are defined in the `.env` file. A sample `.env.example` file is provided as a template.

| Variable | Description | Default Value |
|----------|-------------|---------------|
| MONGO_USERNAME | MongoDB username | root |
| MONGO_PASSWORD | MongoDB password | example |
| MONGO_PORT | Port to expose MongoDB on host | 27017 |
| MONGO_DATABASE | MongoDB database name | online_store |
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
   - Start a MongoDB server
   - Run the Python application that executes all required operations
   - Output the results to the console

### Connecting to MongoDB with DataGrip
To connect to the MongoDB database using DataGrip:

1. Open DataGrip
2. Click on the "+" button to add a new data source
3. Select "MongoDB" from the list of data sources
4. Configure the connection:
   - Host: localhost
   - Port: 27017 (or the value from MONGO_PORT in your .env file)
   - Database: online_store (or the value from MONGO_DATABASE in your .env file)
   - Authentication:
     - Username: root (or the value from MONGO_USERNAME in your .env file)
     - Password: example (or the value from MONGO_PASSWORD in your .env file)
     - Authentication Database: admin
5. Click "Test Connection" to verify the connection
6. Click "OK" to save the connection

After connecting, you can:
- Browse databases and collections
- View and edit documents
- Execute MongoDB queries
- View database statistics
- Export and import data

### Project Structure
- `docker-compose.yml` - Docker Compose configuration
- `Dockerfile` - Docker configuration for the Python application
- `.env` - Environment variables for the application
- `.env.example` - Example environment variables file
- `app/` - Directory containing the Python application
  - `main.py` - Main Python script implementing all MongoDB operations
  - `requirements.txt` - Python dependencies

## Goals:

1. Create a MongoDB database with various products having different sets of properties
   - Example product structure:
   ```json
   {
     "category": "Phone",
     "model": "iPhone 14 Pro",
     "producer": "Apple",
     "price": 999,
     "storage": "256GB",
     "color": "Space Black",
     "in_stock": true
   }
   ```

2. Write queries to retrieve and analyze product data:
   - Display all products in JSON format
   - Count products in a specific category
   - Count the number of different product categories
   - Display a list of unique product manufacturers

3. Write queries that select products based on different criteria:
   - Category AND price range using `$and` construct
   - Products matching one condition OR another using `$or` construct
   - Manufacturers from a specific list using `$in` construct

4. Update products:
   - Change existing values for certain products
   - Add new properties to products matching specific criteria
   - Find products with specific properties
   - Increase the price of found products by a certain amount

5. Implement an order system with referenced items and embedded customer information:
   - Example order structure:
   ```json
   {
     "order_number": 201513,
     "date": ISODate("2025-02-01"),
     "total_sum": 1398,
     "customer": {
       "name": "Andrii",
       "surname": "Rodionov",
       "phones": [9876543, 1234567],
       "address": "PTI, Peremohy 37, Kyiv, UA"
     },
     "payment": {
       "card_owner": "Andrii Rodionov",
       "cardId": 12345678
     },
     "items_id": ["552bc0f7bbcdf26a32e99954", "552bc285bbcdf26a32e99957"]
   }
   ```

6. Perform various operations on orders:
   - Create multiple orders with different product sets (ensure some products appear in multiple orders)
   - Display all orders
   - Find orders with a total value greater than a specific amount
   - Find orders made by a specific customer (by surname)
   - Find all orders containing specific product(s)
   - Add a product to orders containing a specific product and update the total value
   - Count products in a specific order
   - Display only customer information and payment details for high-value orders
   - Remove a product from orders made during a specific date range
   - Rename all orders to match the customer's name
   - Perform a join-like operation to display orders with product details instead of ObjectIds

7. Create a capped collection for store reviews:
   - Limit the collection to the 5 most recent reviews
   - Verify that old reviews are overwritten when the limit is reached

## Implementation Requirements
- MongoDB must be used for all operations
- All commands and their results must be documented
- The provided examples should be followed for document structure

## Report
The submission should include:
- All MongoDB commands executed
- The results of each command's execution
- Explanations where necessary

## Links
- [MongoDB Read Operations](http://docs.mongodb.org/manual/core/read-operations-introduction/)
- [MongoDB One-to-Many Relationship Modeling](https://docs.mongodb.com/manual/tutorial/model-referenced-one-to-many-relationships-between-documents/)

## Results

| Operation | Command | Result |
|-----------|---------|--------|
| Create Products | `db.products.insertMany([...])` | 10 products created (3 phones, 2 TVs, 2 smart watches, 2 laptops) |
| Query All Products | `db.products.find()` | All products displayed in JSON format |
| Count Products by Category | `db.products.countDocuments({category: "Phone"})` | 3 phones found |
| Count Categories | `db.products.distinct("category")` | 4 categories found (Phone, TV, Smart Watch, Laptop) |
| Count Manufacturers | `db.products.distinct("producer")` | 5 manufacturers found (Apple, Samsung, Google, LG, Dell) |
| ... | ... | ... | 