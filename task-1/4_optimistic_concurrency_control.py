import logging
import os
import time
from multiprocessing import Process
import psycopg2
from utils import DB_CONFIG, ensure_row_exists


def optimistic_concurrency_control(process_id):
    """Simulate optimistic concurrency control with version checking."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    process_start_time = time.time()

    try:
        for i in range(NUM_UPDATES):
            while True:
                try:
                    cursor.execute("SELECT counter, version FROM user_counter WHERE user_id = %s", (1,))
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
                            logging.info(f"Process {process_id}: Update {i + 1}: Counter = {counter}, Version = {new_version}")
                            break
                        else:
                            logging.warning(f"Process {process_id}: Version conflict detected. Retrying...")
                    else:
                        logging.warning(f"Process {process_id}: No row found for user_id = 1. Skipping update.")
                        break
                except Exception as e:
                    logging.error(f"Process {process_id}: Error during update: {e}")
                    conn.rollback()
    except Exception as e:
        logging.error(f"Error in process {process_id}: {e}")
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
        p = Process(target=optimistic_concurrency_control, args=(i,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    total_elapsed_time = time.time() - main_start_time
    logging.info(f"Optimistic concurrency control simulation completed in {total_elapsed_time:.2f} seconds.")
