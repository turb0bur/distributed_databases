# Task - Cassandra Cluster Replication

This project demonstrates a 3-node Cassandra cluster deployment using Docker Compose. It implements various operations to explore Cassandra's distributed capabilities, consistency levels, and network partition behavior.

## Requirements

- Configure a 3-node Cassandra cluster
- Verify the correct configuration using nodetool
- Create keyspaces with different replication factors (1, 2, 3)
- Create tables in each keyspace
- Test reading and writing to different nodes
- View data distribution across nodes
- Find which nodes store specific records
- Test consistency levels when nodes disconnect
- Simulate network partitions
- Create and resolve conflicts in a partitioned network
- Test lightweight transactions (LWT)

## Setup and Running

### Prerequisites
- Docker and Docker Compose
- Knowledge of Cassandra database concepts
- Familiarity with CQL (Cassandra Query Language)

### Environment Variables
The application uses environment variables for configuration. These are defined in the `.env` file. A sample `.env.example` file is provided as a template.

| Variable | Description | Default Value |
|----------|-------------|---------------|
| CASSANDRA_HOST | Hostname of the seed node | ddb-task7-cassandra-seed |
| CASSANDRA_PORT | Port for Cassandra connections | 9042 |
| CASSANDRA_USER | Username for authentication | cassandra |
| CASSANDRA_PASSWORD | Password for authentication | cassandra |
| CASSANDRA_NODE1 | Hostname of node 1 | ddb-task7-cassandra-node1 |
| CASSANDRA_NODE2 | Hostname of node 2 | ddb-task7-cassandra-node2 |
| CASSANDRA_SEED_CONTAINER | Container name for seed node | ddb-task7-cassandra-seed |
| CASSANDRA_NODE1_CONTAINER | Container name for node 1 | ddb-task7-cassandra-node1 |
| CASSANDRA_NODE2_CONTAINER | Container name for node 2 | ddb-task7-cassandra-node2 |

### Running the Application

1. Copy the example environment file and modify if needed:
   ```bash
   cp .env.example .env
   ```

2. Start the cluster with Docker Compose:
   ```bash
   docker-compose up -d
   ```

   This will start:
   - 3 Cassandra nodes (seed node and 2 additional nodes)
   - A Python application container for running tests and demonstrations

3. Run specific tests:
   ```bash
   # Test consistency levels
   docker compose run --rm -it app python /app/test_consistency.py
   
   # Test network partition scenarios
   docker compose run --rm -it app python /app/test_network_partition.py
   
   # Test lightweight transactions
   docker compose run --rm -it app python /app/test_lwt.py
   ```

### Connecting to Cassandra with cqlsh

```bash
# Connect to the seed node
docker exec -it ddb-task7-cassandra-seed cqlsh -u cassandra -p cassandra

# Connect to node 1
docker exec -it ddb-task7-cassandra-node1 cqlsh -u cassandra -p cassandra

# Connect to node 2
docker exec -it ddb-task7-cassandra-node2 cqlsh -u cassandra -p cassandra
```

### Using the Management Script

The included `manage_cluster.sh` script provides convenient commands for managing the cluster:

```bash
# Show cluster status
./manage_cluster.sh status

# Connect to the cluster with cqlsh
./manage_cluster.sh cqlsh

# Disconnect a node (simulating failure)
./manage_cluster.sh disconnect 2

# Reconnect a node
./manage_cluster.sh reconnect 2

# Run a specific Python script
./manage_cluster.sh run test_consistency.py

# Show token ring information
./manage_cluster.sh ring

# Run repair on the seed node
./manage_cluster.sh repair
```

### Project Structure
```
├── docker-compose.yml      # Defines the 3-node Cassandra cluster and application container
├── Dockerfile              # Builds Python environment with required dependencies
├── .env                    # Contains environment variables for containers and application
├── .env.example            # Template for environment variables configuration
├── cassandra-config/       # Contains custom Cassandra configuration files
│   ├── cassandra-seed.yaml # Configuration for the seed node with authentication settings
│   ├── cassandra-node1.yaml # Configuration for the first worker node
│   ├── cassandra-node2.yaml # Configuration for the second worker node
│   └── cassandra.yaml      # Base configuration template for all nodes
├── app/                    # Python application code
│   ├── main.py             # Implements core operations (keyspaces, tables, data insertion)
│   ├── db_connection.py    # Connection handling, retry logic, and shared database utilities
│   ├── test_consistency.py # Tests different consistency levels with node disconnection
│   ├── test_lwt.py         # Tests lightweight transactions in normal and partitioned states
│   ├── test_network_partition.py # Simulates network partitions and conflict resolution
│   └── requirements.txt    # Python dependencies (cassandra-driver, rich)
├── manage_cluster.sh       # Script for managing cluster operations and node status
├── CQL_CHEATSHEET.md       # Reference for common CQL commands used in the project
└── README.md               # Project documentation and instructions
```

## Implementation Details

### Data Model

The project creates the following tables in each keyspace:

1. **Users**:
   ```sql
   CREATE TABLE users (
     user_id uuid PRIMARY KEY,
     username text,
     email text,
     created_at timestamp
   )
   ```

2. **Products**:
   ```sql
   CREATE TABLE products (
     product_id uuid PRIMARY KEY,
     name text,
     price decimal,
     category text,
     description text
   )
   ```

3. **Orders**:
   ```sql
   CREATE TABLE orders (
     order_id uuid PRIMARY KEY,
     user_id uuid,
     order_date timestamp,
     total_price decimal,
     status text
   )
   ```

4. **Test Data**:
   ```sql
   CREATE TABLE test_data (
     id text PRIMARY KEY,
     value text,
     timestamp timestamp
   )
   ```

### Task Implementation Map

| Requirement | Implementation Files | Description |
|-------------|----------------------|-------------|
| 1. Configure a 3-node cluster | `docker-compose.yml`, `.env` | Configures a 3-node Cassandra cluster using Docker Compose with proper seed configuration |
| 2. Verify the correct configuration | `db_connection.py` | Implements checks to verify cluster status using system tables and nodetool |
| 3. Create Keyspaces with different replication factors | `db_connection.py:create_keyspaces()` | Creates three keyspaces with RF=1, RF=2, and RF=3 |
| 4. Create tables in each keyspace | `db_connection.py:create_tables()` | Creates users, products, and test_data tables in each keyspace |
| 5. Write and read from different nodes | `main.py` | Demonstrates connecting to different nodes and performing read/write operations |
| 6. Insert data and check distribution | `main.py:insert_sample_data()` | Inserts sample data into all tables and demonstrates distribution using nodetool |
| 7. Show data location for records | `main.py:get_endpoints_for_key()` | Uses nodetool to find which nodes store specific records |
| 8. Test node disconnection and consistency levels | `test_consistency.py` | Tests which consistency levels work when a node is down |
| 9. Simulate network partition | `test_network_partition.py` | Simulates network partition to see how Cassandra operates when nodes can't communicate |
| 10. Create conflicts with consistency level ONE | `test_network_partition.py` | Creates conflicts by writing different values to partitioned nodes |
| 11. Resolve conflicts after network healing | `test_network_partition.py` | Demonstrates Last Write Wins conflict resolution after reconnecting nodes |
| 12. Test lightweight transactions | `test_lwt.py` | Tests Cassandra's lightweight transactions in normal and partitioned cluster states |

### Key Features

1. **Database Connection Module** (`db_connection.py`):
   - Provides shared connection functions for all scripts
   - Handles authentication and retry logic
   - Implements keyspace and table creation utilities

2. **Test Consistency Levels** (`test_consistency.py`):
   - Tests which operations succeed or fail with different consistency levels when a node is down
   - Shows which combinations provide strong consistency
   - Automatically disconnects and reconnects nodes

3. **Network Partition Testing** (`test_network_partition.py`):
   - Connects to each node independently
   - Writes conflicting data to different nodes
   - Demonstrates Cassandra's timestamp-based conflict resolution

4. **Lightweight Transactions** (`test_lwt.py`):
   - Tests conditional updates using Cassandra's IF clauses
   - Compares behavior in normal and partitioned cluster states
   - Shows how LWTs provide linearizable consistency

## Task Walkthrough

### 1. Configure a 3-node Cluster

The docker-compose.yml file is configured to create a 3-node Cassandra cluster:
- One seed node
- Two additional nodes that connect to the seed node

Each node uses the Cassandra 5.0 image and is configured with:
- Same cluster name
- Simple snitch for rack and datacenter awareness
- Authentication using username/password
- Volume mounts for data persistence

### 2. Verify Cluster Configuration

Use the following command to verify the cluster is correctly configured:

```bash
./manage_cluster.sh status
```

Or directly:

```bash
docker exec -it ddb-task7-cassandra-seed nodetool status
```

This should show all three nodes UP and NORMAL.

### 3. Create Keyspaces with Different Replication Factors

Connect to the cluster using cqlsh:

```bash
./manage_cluster.sh cqlsh
```

Create three keyspaces with different replication factors:

```sql
CREATE KEYSPACE keyspace_rf1 
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE KEYSPACE keyspace_rf2 
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 2};

CREATE KEYSPACE keyspace_rf3 
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 3};
```

### 4. Create Tables in Each Keyspace

Create tables in each keyspace:

```sql
USE keyspace_rf1;
CREATE TABLE users (
   user_id UUID PRIMARY KEY,
   username TEXT,
   email TEXT,
   created_at TIMESTAMP
);

USE keyspace_rf2;
CREATE TABLE users (
   user_id UUID PRIMARY KEY,
   username TEXT,
   email TEXT,
   created_at TIMESTAMP
);

USE keyspace_rf3;
CREATE TABLE users (
   user_id UUID PRIMARY KEY,
   username TEXT,
   email TEXT,
   created_at TIMESTAMP
);
```

### 5. Write and Read from Different Nodes

Connect to each node and perform read/write operations:

```bash
# Connect to node 1 (seed)
docker exec -it ddb-task7-cassandra-seed cqlsh -u cassandra -p cassandra

# Connect to node 2
docker exec -it ddb-task7-cassandra-node1 cqlsh -u cassandra -p cassandra

# Connect to node 3
docker exec -it ddb-task7-cassandra-node2 cqlsh -u cassandra -p cassandra
```

### 6. Insert Data and Check Distribution

Insert data into the tables:

```sql
USE keyspace_rf1;
INSERT INTO users (user_id, username, email, created_at) 
VALUES (uuid(), 'User1', 'user1@example.com', toTimestamp(now()));

USE keyspace_rf2;
INSERT INTO users (user_id, username, email, created_at) 
VALUES (uuid(), 'User2', 'user2@example.com', toTimestamp(now()));

USE keyspace_rf3;
INSERT INTO users (user_id, username, email, created_at) 
VALUES (uuid(), 'User3', 'user3@example.com', toTimestamp(now()));
```

Check data distribution with:

```bash
./manage_cluster.sh status
```

### 7. Show Data Location for Records

Get endpoints for specific records:

```bash
# First, get a UUID that exists in your data
docker exec -it ddb-task7-cassandra-seed cqlsh -u cassandra -p cassandra -e "SELECT * FROM keyspace_rf1.users LIMIT 1;"

# Then use the UUID to find endpoints
docker exec -it ddb-task7-cassandra-seed nodetool getendpoints keyspace_rf1 users <uuid-from-previous-step>
```

Repeat this for each keyspace.

### 8. Test Node Disconnection and Consistency Levels

Run the consistency test:

```bash
docker compose run --rm -it app python /app/test_consistency.py
```

Or manually:

1. Disconnect one node:
   ```bash
   ./manage_cluster.sh disconnect 2
   ```

2. Test different consistency levels:
   ```sql
   -- Try with ONE
   CONSISTENCY ONE;
   SELECT * FROM keyspace_rf3.users;

   -- Try with QUORUM
   CONSISTENCY QUORUM;
   SELECT * FROM keyspace_rf3.users;

   -- Try with ALL
   CONSISTENCY ALL;
   SELECT * FROM keyspace_rf3.users;
   ```

3. Observe which consistency levels work for each keyspace when a node is down.

### 9. Simulate Network Partition

Run the network partition test script:

```bash
docker compose run --rm -it app python /app/test_network_partition.py
```

This script will simulate a network partition by disconnecting nodes and analyzing the behavior.

### 10. Create Conflicts with Consistency Level ONE

With network partition in place, write different values to the same record:

```sql
-- On node 1
CONSISTENCY ONE;
UPDATE keyspace_rf3.users SET email = 'conflict1@example.com' WHERE user_id = <uuid>;

-- On node 2
CONSISTENCY ONE;
UPDATE keyspace_rf3.users SET email = 'conflict2@example.com' WHERE user_id = <uuid>;

-- On node 3
CONSISTENCY ONE;
UPDATE keyspace_rf3.users SET email = 'conflict3@example.com' WHERE user_id = <uuid>;
```

### 11. Resolve the Conflict

Reconnect the nodes:

```bash
./manage_cluster.sh reconnect 2
```

Check which value was accepted:

```sql
CONSISTENCY QUORUM;
SELECT * FROM keyspace_rf3.users WHERE user_id = <uuid>;
```

Cassandra uses **"Last Write Wins"** based on timestamp for conflict resolution.

### 12. Test Lightweight Transactions

Run the LWT test script:

```bash
docker compose run --rm -it app python /app/test_lwt.py
```

Or manually test LWT in a connected cluster:

```sql
INSERT INTO keyspace_rf3.users (user_id, username, email) 
VALUES (uuid(), 'LWT Test', 'lwt@example.com') 
IF NOT EXISTS;

UPDATE keyspace_rf3.users 
SET email = 'lwt_updated@example.com' 
WHERE user_id = <uuid> 
IF username = 'LWT Test';
```

LWT operations will only succeed when a majority of replicas can be reached.

## References

### Cassandra Cluster Setup
- [Docker Hub Cassandra Image](https://hub.docker.com/_/cassandra)
- [Build a Cassandra Cluster on Docker](https://gokhanatil.com/2018/02/build-a-cassandra-cluster-on-docker.html)
- [Create a Simple Cassandra Cluster with 3 Nodes](https://www.jamescoyle.net/how-to/2448-create-a-simple-cassandra-cluster-with-3-nodes)

### Keyspace and Table Operations
- [Cassandra Create Keyspace Tutorial](https://www.tutorialspoint.com/cassandra/cassandra_create_keyspace.htm)
- [CQL Reference: CREATE TABLE](https://docs.datastax.com/en/cql/3.1/cql/cql_reference/create_table_r.html)

### Data Operations
- [CQL Reference: INSERT](https://docs.datastax.com/en/cql/3.1/cql/cql_reference/insert_r.html)
- [CQL Reference: SELECT](https://docs.datastax.com/en/cql/3.1/cql/cql_reference/select_r.html)

### Consistency and Transactions
- [CQL Reference: Consistency](https://docs.datastax.com/en/cql/3.1/cql/cql_reference/consistency_r.html)
- [Using Lightweight Transactions](https://docs.datastax.com/en/cql-oss/3.3/cql/cql_using/useInsertLWT.html)
=======
```
