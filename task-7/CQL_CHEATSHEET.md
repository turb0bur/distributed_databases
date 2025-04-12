# CQL Cheat Sheet for Cassandra Cluster

This cheat sheet provides common CQL commands for working with the Cassandra cluster in this project.

## Basic Operations

### Connecting to Cassandra
```bash
docker exec -it cassandra-seed cqlsh
```

### List Keyspaces
```sql
DESCRIBE KEYSPACES;
```

### Use a Keyspace
```sql
USE keyspace_rf3;
```

### List Tables in Current Keyspace
```sql
DESCRIBE TABLES;
```

### Describe Table Structure
```sql
DESCRIBE TABLE users;
```

## Keyspaces

### Create Keyspace with Simple Strategy (Single Datacenter)
```sql
CREATE KEYSPACE my_keyspace
WITH REPLICATION = { 
  'class': 'SimpleStrategy', 
  'replication_factor': 3 
};
```

### Create Keyspace with Network Topology Strategy (Multiple Datacenters)
```sql
CREATE KEYSPACE my_dc_keyspace
WITH REPLICATION = { 
  'class': 'NetworkTopologyStrategy', 
  'dc1': 3, 
  'dc2': 2 
};
```

### Alter Keyspace Replication
```sql
ALTER KEYSPACE my_keyspace
WITH REPLICATION = { 
  'class': 'SimpleStrategy', 
  'replication_factor': 2 
};
```

### Drop Keyspace
```sql
DROP KEYSPACE my_keyspace;
```

## Tables

### Create Table
```sql
CREATE TABLE users (
  user_id uuid PRIMARY KEY,
  username text,
  email text,
  created_at timestamp
);
```

### Create Table with Composite Key
```sql
CREATE TABLE user_posts (
  username text,
  post_id timeuuid,
  title text,
  content text,
  PRIMARY KEY (username, post_id)
);
```

### Alter Table (Add Column)
```sql
ALTER TABLE users ADD age int;
```

### Drop Table
```sql
DROP TABLE users;
```

## Data Manipulation

### Insert Data
```sql
INSERT INTO users (user_id, username, email, created_at)
VALUES (uuid(), 'johndoe', 'john@example.com', toTimestamp(now()));
```

### Update Data
```sql
UPDATE users
SET email = 'newemail@example.com'
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;
```

### Delete Data
```sql
DELETE FROM users
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;
```

### Delete Column Value
```sql
DELETE email FROM users
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;
```

### Truncate Table (Delete All Rows)
```sql
TRUNCATE users;
```

## Querying

### Select All
```sql
SELECT * FROM users;
```

### Select Specific Columns
```sql
SELECT username, email FROM users;
```

### Select with Where Clause
```sql
SELECT * FROM users WHERE username = 'johndoe';
```

### Select with IN Clause
```sql
SELECT * FROM users WHERE username IN ('johndoe', 'janedoe');
```

### Select with Limit
```sql
SELECT * FROM users LIMIT 10;
```

### Count Rows
```sql
SELECT COUNT(*) FROM users;
```

## Setting Consistency Levels

### Set Consistency for Session
```sql
CONSISTENCY QUORUM;
```

### Available Consistency Levels
- ANY: Lowest consistency level (writes only)
- ONE: At least one replica must respond
- TWO: At least two replicas must respond
- THREE: At least three replicas must respond
- QUORUM: A majority of replicas must respond
- ALL: All replicas must respond
- LOCAL_QUORUM: A majority of replicas in the local datacenter
- EACH_QUORUM: A majority of replicas in each datacenter
- LOCAL_ONE: At least one replica in the local datacenter

## Lightweight Transactions (LWT)

### Insert with Conditional Check
```sql
INSERT INTO users (user_id, username, email)
VALUES (uuid(), 'johndoe', 'john@example.com')
IF NOT EXISTS;
```

### Update with Conditional Check
```sql
UPDATE users
SET email = 'new@example.com'
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000
IF email = 'old@example.com';
```

### Delete with Conditional Check
```sql
DELETE FROM users
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000
IF username = 'johndoe';
```

## Time To Live (TTL)

### Insert with TTL
```sql
INSERT INTO users (user_id, username, email)
VALUES (uuid(), 'temp_user', 'temp@example.com')
USING TTL 3600;  -- Expire in 3600 seconds (1 hour)
```

### Update with TTL
```sql
UPDATE users
USING TTL 86400  -- Expire in 86400 seconds (24 hours)
SET email = 'expire@example.com'
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;
```

### Get TTL
```sql
SELECT TTL(email) FROM users
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;
```

## Timestamps and Timeuuid

### Insert with Custom Timestamp
```sql
INSERT INTO users (user_id, username, email)
VALUES (uuid(), 'user1', 'user1@example.com')
USING TIMESTAMP 1610000000000;
```

### Generate TimeUUID
```sql
INSERT INTO user_posts (username, post_id, title)
VALUES ('johndoe', now(), 'My First Post');
```

## Indexes

### Create Index
```sql
CREATE INDEX ON users (email);
```

### Create Custom Index with Name
```sql
CREATE INDEX user_email_idx ON users (email);
```

### Drop Index
```sql
DROP INDEX user_email_idx;
```

## Batch Operations

### Batch Multiple Operations
```sql
BEGIN BATCH
  INSERT INTO users (user_id, username) VALUES (uuid(), 'user1');
  INSERT INTO user_profiles (user_id, bio) VALUES (uuid(), 'New user');
APPLY BATCH;
```

### Batch with Timestamp
```sql
BEGIN BATCH
  USING TIMESTAMP 1610000000000
  INSERT INTO users (user_id, username) VALUES (uuid(), 'user1');
  UPDATE user_count SET count = count + 1 WHERE id = 'total';
APPLY BATCH;
```

## Collection Types

### List Operations
```sql
-- Create table with list
CREATE TABLE user_emails (
  user_id uuid PRIMARY KEY,
  emails list<text>
);

-- Insert list
INSERT INTO user_emails (user_id, emails)
VALUES (uuid(), ['email1@example.com', 'email2@example.com']);

-- Add to list
UPDATE user_emails
SET emails = emails + ['email3@example.com']
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;

-- Remove from list
UPDATE user_emails
SET emails = emails - ['email1@example.com']
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;
```

### Map Operations
```sql
-- Create table with map
CREATE TABLE user_attributes (
  user_id uuid PRIMARY KEY,
  attributes map<text, text>
);

-- Insert map
INSERT INTO user_attributes (user_id, attributes)
VALUES (uuid(), {'height': '180cm', 'weight': '75kg'});

-- Add to map
UPDATE user_attributes
SET attributes['eye_color'] = 'blue'
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;

-- Remove from map
UPDATE user_attributes
SET attributes['height'] = null
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;
```

### Set Operations
```sql
-- Create table with set
CREATE TABLE user_roles (
  user_id uuid PRIMARY KEY,
  roles set<text>
);

-- Insert set
INSERT INTO user_roles (user_id, roles)
VALUES (uuid(), {'admin', 'editor'});

-- Add to set
UPDATE user_roles
SET roles = roles + {'viewer'}
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;

-- Remove from set
UPDATE user_roles
SET roles = roles - {'editor'}
WHERE user_id = 123e4567-e89b-12d3-a456-426614174000;
``` 