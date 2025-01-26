import logging
import os
import time
from multiprocessing import Process
import psycopg2
from utils import DB_CONFIG, ensure_row_exists


def lost_update(process_id):
    """Simulate lost-update problem."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    process_start_time = time.time()
    try:
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
        for i in range(NUM_UPDATES):
            cursor.execute("SELECT counter FROM user_counter WHERE user_id = 1")
            row = cursor.fetchone()

            if row is None:
                logging.error("No row found for user_id 1")
                break

            counter = row[0]
            counter += 1
            cursor.execute("UPDATE user_counter SET counter = %s WHERE user_id = %s", (counter, 1))
            conn.commit()
            logging.info(f"Process {process_id}: Update {i + 1}: Counter = {counter}")
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
        elapsed_time = time.time() - process_start_time
        logging.info(f"Process {process_id} completed in {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    NUM_PROCESSES = int(os.getenv('NUM_PROCESSES', 10))
    NUM_UPDATES = int(os.getenv('NUM_UPDATES', 1000))

    ensure_row_exists()
    main_start_time = time.time()
    processes = []

    for i in range(NUM_PROCESSES):
        p = Process(target=lost_update, args=(i,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    total_elapsed_time = time.time() - main_start_time
    logging.info(f"Lost-update simulation completed in {total_elapsed_time:.2f} seconds.")
