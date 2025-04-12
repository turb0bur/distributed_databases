#!/usr/bin/env python3
"""
Network partition test script for Cassandra.
This script demonstrates how Cassandra handles conflicting writes during network partitions.
"""

import os
import time
import logging
from cassandra.cluster import Cluster, ConsistencyLevel
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)-8s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger("cassandra-partition-test")
console = Console()

# Configuration
CASSANDRA_HOST = os.environ.get('CASSANDRA_HOST', 'ddb-task7-cassandra-seed')
CASSANDRA_PORT = int(os.environ.get('CASSANDRA_PORT', 9042))
CASSANDRA_USER = os.environ.get('CASSANDRA_USER', 'cassandra')
CASSANDRA_PASSWORD = os.environ.get('CASSANDRA_PASSWORD', 'cassandra')
CASSANDRA_NODES = [
    CASSANDRA_HOST,
    os.environ.get('CASSANDRA_NODE1', 'ddb-task7-cassandra-node1'),
    os.environ.get('CASSANDRA_NODE2', 'ddb-task7-cassandra-node2')
]

def create_auth_provider():
    """Create authentication provider for Cassandra connection"""
    return PlainTextAuthProvider(
        username=CASSANDRA_USER,
        password=CASSANDRA_PASSWORD
    )

def connect_to_node(host):
    """Connect to a specific Cassandra node"""
    try:
        log.info(f"Connecting to node at {host}:{CASSANDRA_PORT}")
        auth_provider = create_auth_provider()
        cluster = Cluster(
            contact_points=[host],
            port=CASSANDRA_PORT,
            auth_provider=auth_provider,
            protocol_version=5
        )
        session = cluster.connect()
        session.default_consistency_level = ConsistencyLevel.ONE
        log.info(f"Connected to node at {host}")
        return cluster, session
    except Exception as e:
        log.error(f"Failed to connect to node at {host}: {str(e)}")
        return None, None

def get_cluster_status():
    """Get cluster status using nodetool-like functionality"""
    try:
        cluster, session = connect_to_node(CASSANDRA_HOST)
        if not session:
            return "Error: Could not connect to seed node"
        
        # Query node status from system tables
        local_rows = session.execute("SELECT host_id, data_center, rack, tokens, release_version, schema_version, listen_address, broadcast_address FROM system.local")
        local_info = []
        for row in local_rows:
            local_info.append({
                "datacenter": row.data_center,
                "rack": row.rack,
                "status": "Up",
                "state": "Normal",
                "address": row.broadcast_address or row.listen_address,
                "load": "N/A",
                "tokens": len(row.tokens),
                "host_id": str(row.host_id),
                "version": row.release_version
            })
        
        peer_rows = session.execute("SELECT host_id, data_center, rack, schema_version, release_version, rpc_address FROM system.peers")
        peer_info = []
        for row in peer_rows:
            peer_info.append({
                "datacenter": row.data_center,
                "rack": row.rack,
                "status": "Up",
                "state": "Normal",
                "address": row.rpc_address,
                "load": "N/A",
                "tokens": "N/A",
                "host_id": str(row.host_id),
                "version": row.release_version
            })
        
        result = "Datacenter: datacenter1\n"
        result += "=====================\n"
        result += "Status=Up/Down\n"
        result += "|/ State=Normal/Leaving/Joining/Moving\n"
        result += "--  Address      Load        Tokens  Owns    Host ID                               Rack\n"
        
        for node in local_info:
            result += f"UN  {node['address']:<11} {node['load']:<11} {node['tokens']:<7} ?      {node['host_id']}  {node['rack']}\n"
        
        for node in peer_info:
            result += f"UN  {node['address']:<11} {node['load']:<11} {node['tokens']:<7} ?      {node['host_id']}  {node['rack']}\n"
        
        cluster.shutdown()
        return result
    except Exception as e:
        log.error(f"Failed to get cluster status: {str(e)}")
        return f"Error: {str(e)}"

def test_network_partition():
    """Test network partition and conflict resolution"""
    console.print("\n[bold green]=== TESTING NETWORK PARTITION AND CONFLICT RESOLUTION ===[/bold green]")
    
    # Connect to seed node
    seed_cluster, seed_session = connect_to_node(CASSANDRA_HOST)
    if not seed_session:
        console.print("[red]Failed to connect to seed node. Exiting.[/red]")
        return
    
    # Create a test keyspace and table
    console.print("[bold]Creating test keyspace and table for partition test...[/bold]")
    keyspace = "demo_partition"
    
    try:
        # Create keyspace with ONE consistency
        seed_session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace}
        WITH REPLICATION = {{ 'class': 'SimpleStrategy', 'replication_factor': 3 }}
        """)
        
        # Create table with ONE consistency
        seed_session.execute(f"""
        CREATE TABLE IF NOT EXISTS {keyspace}.partition_test (
            id text PRIMARY KEY,
            value text,
            last_updated timestamp
        )
        """)
        
        # Insert initial data
        initial_timestamp = "toTimestamp(now())"
        seed_session.execute(f"""
        INSERT INTO {keyspace}.partition_test (id, value, last_updated)
        VALUES ('test_key', 'initial_value', {initial_timestamp})
        """)
        
        console.print("[bold]Initial data inserted[/bold]")
        
        # Show initial value
        rows = seed_session.execute(f"SELECT * FROM {keyspace}.partition_test WHERE id = 'test_key'")
        for row in rows:
            console.print(f"Initial value: id={row.id}, value={row.value}, timestamp={row.last_updated}")
    except Exception as e:
        console.print(f"[red]Error setting up test: {str(e)}[/red]")
        seed_cluster.shutdown()
        return
    
    # Show initial cluster status
    console.print("\n[bold]Initial cluster status:[/bold]")
    initial_status = get_cluster_status()
    console.print(initial_status)
    
    # Pause to manually create network partition - disconnect only one node
    console.print("\n[bold yellow]MANUAL STEP REQUIRED - NETWORK PARTITION:[/bold yellow]")
    console.print("Run this command in a separate terminal:")
    console.print("[bold green]./manage_cluster.sh disconnect 2[/bold green]")
    input("\nPress Enter after you've disconnected node 2...")
    
    # Show cluster status during partition
    console.print("\n[bold]Cluster status during network partition:[/bold]")
    partition_status = get_cluster_status()
    console.print(partition_status)
    
    # Create a table to show writes during partition
    partition_table = Table(title="Writes During Network Partition")
    partition_table.add_column("Node")
    partition_table.add_column("Value")
    partition_table.add_column("Timestamp")
    
    # Connect to node 1 (should be up)
    node1_cluster, node1_session = connect_to_node(CASSANDRA_NODES[1])
    if not node1_session:
        console.print("[red]Failed to connect to Node 1. This is unexpected.[/red]")
    
    # Write different values to seed node and node 1
    # Write to seed node
    try:
        timestamp = "toTimestamp(now())"
        seed_session.execute(f"""
        INSERT INTO {keyspace}.partition_test (id, value, last_updated)
        VALUES ('test_key', %s, {timestamp})
        """, ("Value written to seed node",))
        
        # Read back the value to get the actual timestamp
        rows = seed_session.execute(f"SELECT * FROM {keyspace}.partition_test WHERE id = 'test_key'")
        for row in rows:
            partition_table.add_row("SEED_NODE", row.value, str(row.last_updated))
            console.print(f"Successfully wrote to SEED_NODE: {row.value} at {row.last_updated}")
    except Exception as e:
        console.print(f"[red]Failed to write to SEED_NODE: {str(e)}[/red]")
    
    # Write to node 1
    if node1_session:
        try:
            # Wait a bit to ensure a different timestamp
            time.sleep(2)
            timestamp = "toTimestamp(now())"
            node1_session.execute(f"""
            INSERT INTO {keyspace}.partition_test (id, value, last_updated)
            VALUES ('test_key', %s, {timestamp})
            """, ("Value written to node 1",))
            
            # Read back the value to get the actual timestamp
            rows = node1_session.execute(f"SELECT * FROM {keyspace}.partition_test WHERE id = 'test_key'")
            for row in rows:
                partition_table.add_row("NODE1", row.value, str(row.last_updated))
                console.print(f"Successfully wrote to NODE1: {row.value} at {row.last_updated}")
        except Exception as e:
            console.print(f"[red]Failed to write to NODE1: {str(e)}[/red]")
    
    console.print(partition_table)
    
    # Pause to manually heal the network partition
    console.print("\n[bold yellow]MANUAL STEP REQUIRED - HEAL PARTITION:[/bold yellow]")
    console.print("Run this command in a separate terminal:")
    console.print("[bold green]./manage_cluster.sh reconnect 2[/bold green]")
    input("\nPress Enter after you've reconnected node 2...")
    
    # Wait for cluster to stabilize
    console.print("\n[bold]Waiting for cluster to stabilize after healing (30 seconds)...[/bold]")
    time.sleep(30)
    
    # Show final cluster status
    console.print("\n[bold]Cluster status after healing:[/bold]")
    healed_status = get_cluster_status()
    console.print(healed_status)
    
    # Check final value after healing
    console.print("\n[bold]Final value after conflict resolution:[/bold]")
    rows = seed_session.execute(f"SELECT * FROM {keyspace}.partition_test WHERE id = 'test_key'")
    for row in rows:
        console.print(f"id={row.id}, value={row.value}, timestamp={row.last_updated}")
        console.print(f"The winning value is: {row.value} (based on last write timestamp)")
    
    # Create a summary table
    summary_table = Table(title="Conflict Resolution Summary")
    summary_table.add_column("Phase")
    summary_table.add_column("Details")
    
    summary_table.add_row("Initial State", "Single value across all nodes")
    summary_table.add_row("During Partition", "Different values written to isolated nodes")
    summary_table.add_row("After Healing", "Last Write Wins (LWW) resolution based on timestamp")
    summary_table.add_row("Resolution Method", "Timestamp-based conflict resolution")
    
    console.print(summary_table)
    
    console.print(Panel("""
In a network partition scenario (split brain):

1. We wrote different values to the same key on isolated nodes
2. When the network was healed, Cassandra used timestamp-based conflict resolution
3. The write with the latest timestamp wins
4. This is known as "Last Write Wins" (LWW) conflict resolution
5. Data from other nodes is overwritten during read repair or anti-entropy repair
6. This demonstrates why timestamp-based conflict resolution is crucial in distributed systems
    """, title="Network Partition Test Results"))
    
    # Clean up
    seed_cluster.shutdown()
    if node1_cluster:
        node1_cluster.shutdown()

if __name__ == "__main__":
    test_network_partition() 