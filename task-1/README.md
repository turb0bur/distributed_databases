# Task 1 - Implementation of Counter using PostgreSQL

This project implements a simple counter functionality, commonly used in social networks, video platforms, photo and video sharing services, etc. The counter increments by one when the corresponding action is performed.

## Requirements
- No loss of intermediate values due to simultaneous access (race condition).
- Data is not lost when the server is suddenly rebooted.

The second point can be implemented by writing each update to the hard disk or by replicating the value to the memory of another server.

## Goal
Implement the update of the counter value in the PostgreSQL database in several ways and estimate the time of each option.

### Table Structure
The `user_counter` table has the following structure:
- `user_id` - _key_ with user ID
- `counter` - _Integer_ - counter value
- `version` - _Integer_ - auxiliary field, used in one of the implementation options

## Implementation Methods

### Lost-update (implementation that loses records)
Run 10 threads or individual clients simultaneously
```python
for i in range(10_000):
    counter = cursor.execute("SELECT counter FROM user_counter WHERE user_id = 1").fetchone()
    counter = counter + 1
    cursor.execute("UPDATE user_counter SET counter = %s WHERE user_id = %s", (counter, 1))
    conn.commit()
```
Measure the execution time.

### In-place update
Run 10 threads or individual clients simultaneously
```python
for i in range(10_000):
    cursor.execute("UPDATE user_counter SET counter = counter + 1 WHERE user_id = %s", (1,))
    conn.commit()
```
Measure the execution time.

### Row-level locking
Row-level locking with SELECT ... FOR UPDATE:
- [Row-Level Locks](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS)
- [Enforcing Consistency with Explicit Blocking Locks](https://www.postgresql.org/docs/current/applevel-consistency.html#NON-SERIALIZABLE-CONSISTENCY)

Run 10 threads or individual clients simultaneously
```python
for i in range(10_000):
    counter = cursor.execute("SELECT counter FROM user_counter WHERE user_id = 1 FOR UPDATE").fetchone()
    counter = counter + 1
    cursor.execute("UPDATE user_counter SET counter = %s WHERE user_id = %s", (counter, 1))
    conn.commit()
```
Create a separate connection and cursor for each thread for SELECT ... FOR UPDATE to have an effect.
Measure the execution time.

### Optimistic concurrency control
Run 10 threads or individual clients simultaneously
```python
while True:
    cursor.execute("SELECT counter, version FROM user_counter WHERE user_id = 1")
    result = cursor.fetchone()
    if result:
        counter, version = result
        counter += 1
        new_version = version + 1
        cursor.execute(
            "UPDATE user_counter SET counter = %s, version = %s WHERE user_id = %s AND version = %s",
            (counter, new_version, 1, version)
        )
        if cursor.rowcount > 0:
            conn.commit()
            break
```
Measure the execution time.

## Implementation Requirements
- Any programming language implementation
- Do not use ORM frameworks (Hibernate, SQLAlchemy, …)
- Do not forget about the need for a separate transaction for each record

## Report
As a result of the work, the script code and test results for various scenarios should be provided.
In all options, except the first, the final counter value should be 100K

## Links
- Database Interaction for Python: [Psycopg 2.9.10](https://www.psycopg.org/docs/usage.html)


## Installation
1. Clone the repository:
```bash
git clone https://github.com/turb0bur/distributed_databases
cd distributed_databases/task-1
```

2. Create and configure the .env file:  
Copy the example environment file and fill in the necessary values:
```bash
cp .env.example .env
```

3. Start the PostgreSQL database using Docker Compose:
```bash
docker-compose up -d
```

4. Install the required Python packages:
```bash
pip install -r requirements.txt
```

5. Run the `init.sql` script to create the necessary table and record

## Results
To run the scripts with detailed logging, use the following commands in the terminal:
1. `python 1_lost_update.py > 1_lost_update.log 2>&1`
2. `python 2_in_place_update.py > 2_in_place_update.log 2>&1`
3. `python 3_row_level_locking.py > 3_row_level_locking.log 2>&1`
4. `python 4_optimistic_concurrency_control.py > 4_optimistic_concurrency_control.log 2>&1`

| Method                            | Execution Time (seconds) | Final Counter Value |
|-----------------------------------|:------------------------:|:-------------------:|
| 1. Lost-update                    |        379.50 sec        |        10427        |
| 2. In-place update                |        372.08 sec        |       100000        |
| 3. Row-level locking              |        393.16 sec        |       100000        |
| 4. Optimistic concurrency control |        534.72 sec        |       100000        |
