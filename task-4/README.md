# Task - Neo4j Online Store Implementation

This project implements a model of an online store using Neo4j graph database, demonstrating relationships between customers, orders, and items, including viewing and purchasing behaviors.

## Requirements
- Learn how to perform basic queries to Neo4j
- Model relationships between customers, orders, and items
- Implement viewing and purchasing behaviors
- Create complex queries to analyze customer behavior and product relationships

## Setup and Running

### Prerequisites
- Docker and Docker Compose installed on your system
- Git to clone the repository
- (Optional) Neo4j Browser installed on your system (for database management)

### Environment Variables
The application uses environment variables for configuration. These are defined in the `.env` file. A sample `.env.example` file is provided as a template.

| Variable | Description | Default Value |
|----------|-------------|---------------|
| NEO4J_AUTH | Neo4j username and password | neo4j/example123 |
| NEO4J_PORT | Port to expose Neo4j on host | 7474 |
| NEO4J_BOLT_PORT | Bolt protocol port | 7687 |
| NEO4J_HOST | Neo4j host name | neo4j |
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
   - Start a Neo4j server
   - Run the Python application that executes all required operations
   - Output the results to the console

### Connecting to Neo4j
To connect to the Neo4j database:

1. Open your web browser and navigate to `http://localhost:7474`
2. Use the following credentials:
   - Username: neo4j
   - Password: example123 (or the value you set in NEO4J_AUTH)
3. Enter the connection URL: `bolt://localhost:7687`

Note: The password must be at least 8 characters long. If you need to use a shorter password, you can set the environment variable `NEO4J_dbms_security_auth__minimum__password__length` to override this requirement.

### Project Structure
```
.
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile           # Docker configuration for the Python application
├── .env                 # Environment variables for the application
├── .env.example         # Example environment variables file
└── app/                 # Directory containing the Python application
    ├── main.py         # Main Python script implementing all Neo4j operations
    └── requirements.txt # Python dependencies
```

## Data Model

### Nodes
1. Customer
   ```cypher
   (c:Customer {id: string, name: string})
   ```

2. Item
   ```cypher
   (i:Item {id: string, name: string, price: float})
   ```

3. Order
   ```cypher
   (o:Order {id: string, date: datetime})
   ```

### Relationships
1. Customer -> Order: BOUGHT
   ```cypher
   (c:Customer)-[:BOUGHT]->(o:Order)
   ```

2. Order -> Item: CONTAINS
   ```cypher
   (o:Order)-[:CONTAINS]->(i:Item)
   ```

3. Customer -> Item: VIEWED
   ```cypher
   (c:Customer)-[:VIEWED]->(i:Item)
   ```

## Required Queries

1. Find Items in a specific Order
   ```cypher
   MATCH (o:Order {id: $order_id})-[:CONTAINS]->(i:Item)
   RETURN i
   ```

2. Calculate Order Cost
   ```cypher
   MATCH (o:Order {id: $order_id})-[:CONTAINS]->(i:Item)
   RETURN sum(i.price) as total_cost
   ```

3. Find Customer Orders
   ```cypher
   MATCH (c:Customer {id: $customer_id})-[:BOUGHT]->(o:Order)
   RETURN o
   ```

4. Find Customer Purchased Items
   ```cypher
   MATCH (c:Customer {id: $customer_id})-[:BOUGHT]->(o:Order)-[:CONTAINS]->(i:Item)
   RETURN DISTINCT i
   ```

5. Count Customer Purchased Items
   ```cypher
   MATCH (c:Customer {id: $customer_id})-[:BOUGHT]->(o:Order)-[:CONTAINS]->(i:Item)
   RETURN count(i) as item_count
   ```

6. Calculate Customer Total Purchase Amount
   ```cypher
   MATCH (c:Customer {id: $customer_id})-[:BOUGHT]->(o:Order)-[:CONTAINS]->(i:Item)
   RETURN sum(i.price) as total_amount
   ```

7. Count Item Purchase Frequency
   ```cypher
   MATCH (o:Order)-[:CONTAINS]->(i:Item)
   RETURN i.name as item_name, count(*) as purchase_count
   ORDER BY purchase_count DESC
   ```

8. Find Customer Viewed Items
   ```cypher
   MATCH (c:Customer {id: $customer_id})-[:VIEWED]->(i:Item)
   RETURN i
   ```

9. Find Related Purchased Items
   ```cypher
   MATCH (i1:Item {id: $item_id})<-[:CONTAINS]-(o:Order)-[:CONTAINS]->(i2:Item)
   WHERE i2.id <> $item_id
   RETURN i2.name as related_item, count(*) as frequency
   ORDER BY frequency DESC
   ```

10. Find Item Customers
    ```cypher
    MATCH (i:Item {id: $item_id})<-[:CONTAINS]-(o:Order)<-[:BOUGHT]-(c:Customer)
    RETURN DISTINCT c
    ```

11. Find Customer Unpurchased Viewed Items
    ```cypher
    MATCH (c:Customer {id: $customer_id})-[:VIEWED]->(i:Item)
    WHERE NOT EXISTS((c)-[:BOUGHT]->(:Order)-[:CONTAINS]->(i))
    RETURN i
    ```

## Implementation Requirements
- Neo4j must be used for all operations
- All Cypher queries and their results must be documented
- The provided data model should be followed
- Python application should demonstrate all required queries

## Report
The submission should include:
- All Cypher queries executed
- The results of each query's execution
- Explanations where necessary
- Python code implementing the queries

## Links
- [Neo4j Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/) 