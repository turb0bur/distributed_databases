#!/usr/bin/env python3
"""
Script to test consistency levels in Cassandra when a node is disconnected.
This demonstrates which operations succeed or fail with different replication factors.
"""

import uuid
import logging
from cassandra.cluster import ConsistencyLevel
from cassandra.query import SimpleStatement
from rich.console import Console
from rich.table import Table
from rich import print as rprint

import db_connection as db

log = logging.getLogger("cassandra-consistency")
console = Console()

def check_cluster_status():
    """Check the status of the cluster using nodetool status"""
    status_output = db.run_nodetool("status")
    rprint(status_output)
    rprint("[bold]---------------------------------------------------[/bold]")
    return status_output

def setup_test_keyspaces(session):
    """Create test keyspaces with different replication factors"""
    keyspaces = [
        ("consistency_rf1", 1),
        ("consistency_rf2", 2),
        ("consistency_rf3", 3)
    ]
    
    for keyspace_name, rf in keyspaces:
        try:
            query = f"""
            CREATE KEYSPACE IF NOT EXISTS {keyspace_name}
            WITH REPLICATION = {{ 
                'class': 'SimpleStrategy', 
                'replication_factor': {rf} 
            }}
            """
            session.execute(query)
            log.info(f"Created keyspace {keyspace_name} with replication factor {rf}")
            
            session.execute(f"""
            CREATE TABLE IF NOT EXISTS {keyspace_name}.test_data (
                id uuid PRIMARY KEY,
                value text
            )
            """)
            
            for i in range(5):
                session.execute(f"""
                INSERT INTO {keyspace_name}.test_data (id, value)
                VALUES (uuid(), %s)
                """, (f"Value {i} in {keyspace_name}",))
            
            log.info(f"Created table and inserted data in {keyspace_name}")
        except Exception as e:
            log.error(f"Failed to setup keyspace {keyspace_name}: {str(e)}")
    rprint("[bold]---------------------------------------------------[/bold]")

def disconnect_node():
    """Disconnect one of the Cassandra nodes"""
    log.info(f"Disconnecting {db.CASSANDRA_NODE2_CONTAINER} from the cluster")
    output = db.run_command(f"docker stop {db.CASSANDRA_NODE2_CONTAINER}")
    log.info(f"Node stopped: {output}")
    
    # Give the cluster time to recognize the node is down
    db.time.sleep(10)
    
    log.info("Cluster status after node disconnection:")
    check_cluster_status()
    rprint("[bold]---------------------------------------------------[/bold]")

def test_consistency_levels(session):
    """Test different consistency levels for read and write operations"""
    keyspaces = [
        ("consistency_rf1", 1),
        ("consistency_rf2", 2),
        ("consistency_rf3", 3)
    ]
    
    consistency_levels = [
        (ConsistencyLevel.ONE, "ONE"),
        (ConsistencyLevel.TWO, "TWO"),
        (ConsistencyLevel.THREE, "THREE"),
        (ConsistencyLevel.QUORUM, "QUORUM"),
        (ConsistencyLevel.ALL, "ALL")
    ]
    
    table = Table(title="Consistency Test Results (with 1 node disconnected)")
    table.add_column("Keyspace (RF)")
    table.add_column("Consistency Level")
    table.add_column("Read Works")
    table.add_column("Write Works")
    table.add_column("Strong Consistency")
    
    for keyspace, rf in keyspaces:
        for cl_value, cl_name in consistency_levels:
            read_works = "❌"
            write_works = "❌"
            
            try:
                query = SimpleStatement(
                    f"SELECT * FROM {keyspace}.test_data LIMIT 1",
                    consistency_level=cl_value
                )
                session.execute(query)
                read_works = "✅"
            except Exception as e:
                log.info(f"Read failed for {keyspace} with CL={cl_name}: {str(e)}")
            
            try:
                query = SimpleStatement(
                    f"INSERT INTO {keyspace}.test_data (id, value) VALUES (uuid(), %s)",
                    consistency_level=cl_value
                )
                session.execute(query, (f"Test value with {cl_name}",))
                write_works = "✅"
            except Exception as e:
                log.info(f"Write failed for {keyspace} with CL={cl_name}: {str(e)}")
            
            # Strong consistency requires: Read consistency + Write consistency > RF
            # For this test, we use the same level for both, so CL > RF/2
            strong_consistency = "✅" if cl_value > rf/2 else "❌"
            
            if read_works == "❌" or write_works == "❌":
                strong_consistency = "N/A"
            
            table.add_row(
                f"{keyspace} (RF={rf})",
                cl_name,
                read_works,
                write_works,
                strong_consistency
            )
    
    console.print(table)
    rprint("[bold]---------------------------------------------------[/bold]")

def reconnect_node():
    """Reconnect the disconnected node"""
    log.info(f"Reconnecting {db.CASSANDRA_NODE2_CONTAINER} to the cluster")
    output = db.run_command(f"docker start {db.CASSANDRA_NODE2_CONTAINER}")
    log.info(f"Node started: {output}")
    
    # Give the cluster time to recognize the node is back
    db.time.sleep(30)
    
    log.info("Cluster status after node reconnection:")
    check_cluster_status()
    rprint("[bold]---------------------------------------------------[/bold]")

def run_test():
    """Run the complete consistency level test"""
    cluster, session = db.connect_to_cluster()
    if not cluster:
        log.error("Failed to connect to cluster. Exiting.")
        return
    
    try:
        log.info("Initial cluster status:")
        check_cluster_status()
        
        setup_test_keyspaces(session)
        
        disconnect_node()
        
        test_consistency_levels(session)
        
        reconnect_node()
        
        log.info("Consistency level test completed")
        rprint("[bold]---------------------------------------------------[/bold]")
    except Exception as e:
        log.error(f"Error during consistency test: {str(e)}")
    finally:
        if cluster:
            cluster.shutdown()

if __name__ == "__main__":
    db.wait_for_cluster_ready()
    run_test() 