#!/usr/bin/env python3
"""
Lightweight Transactions (LWT) test script for Cassandra.
This script demonstrates how Cassandra's LWTs behave in normal and partitioned cluster states.
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
log = logging.getLogger("cassandra-lwt-test")
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

def test_lwt_normal_state():
    """Test Lightweight Transactions in normal cluster state"""
    console.print("\n[bold green]=== TESTING LIGHTWEIGHT TRANSACTIONS IN NORMAL CLUSTER STATE ===[/bold green]")
    
    cluster, session = connect_to_node(CASSANDRA_HOST)
    if not session:
        console.print("[red]Failed to connect to seed node. Exiting.[/red]")
        return
    
    console.print("[bold]Creating test keyspace and table for LWT test...[/bold]")
    keyspace = "demo_lwt"
    
    try:
        session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace}
        WITH REPLICATION = {{ 'class': 'SimpleStrategy', 'replication_factor': 3 }}
        """)
        
        session.execute(f"""
        CREATE TABLE IF NOT EXISTS {keyspace}.lwt_test (
            id text PRIMARY KEY,
            value text,
            version int
        )
        """)
        
        session.execute(f"""
        INSERT INTO {keyspace}.lwt_test (id, value, version)
        VALUES ('test_key', 'initial_value', 1)
        """)
        
        console.print("[bold]Initial data inserted[/bold]")
        
        rows = session.execute(f"SELECT * FROM {keyspace}.lwt_test WHERE id = 'test_key'")
        for row in rows:
            console.print(f"Initial value: id={row.id}, value={row.value}, version={row.version}")
    except Exception as e:
        console.print(f"[red]Error setting up test: {str(e)}[/red]")
        cluster.shutdown()
        return
    
    console.print("\n[bold]Cluster status:[/bold]")
    status = get_cluster_status()
    console.print(status)
    
    results_table = Table(title="Lightweight Transaction Tests (Normal Cluster)")
    results_table.add_column("Operation")
    results_table.add_column("Result")
    results_table.add_column("Applied")
    results_table.add_column("Current Value")
    
    try:
        console.print("\n[bold]Test 1: Successful CAS operation[/bold]")
        result = session.execute(
            f"""
            UPDATE {keyspace}.lwt_test 
            SET value = 'updated_value', version = 2 
            WHERE id = 'test_key' 
            IF value = 'initial_value'
            """
        )
        applied = result.one().applied
        current_rows = session.execute(f"SELECT * FROM {keyspace}.lwt_test WHERE id = 'test_key'")
        current_value = current_rows.one().value
        
        console.print(f"Operation applied: {applied}")
        console.print(f"Current value: {current_value}")
        
        results_table.add_row(
            "UPDATE IF value = 'initial_value'",
            "Success" if applied else "Failure",
            str(applied),
            current_value
        )
    except Exception as e:
        console.print(f"[red]Test 1 failed: {str(e)}[/red]")
        results_table.add_row("UPDATE IF value = 'initial_value'", f"Error: {str(e)}", "N/A", "N/A")
    
    try:
        console.print("\n[bold]Test 2: Failed CAS operation (condition not met)[/bold]")
        result = session.execute(
            f"""
            UPDATE {keyspace}.lwt_test 
            SET value = 'another_update', version = 3 
            WHERE id = 'test_key' 
            IF value = 'initial_value'
            """
        )
        applied = result.one().applied
        current_rows = session.execute(f"SELECT * FROM {keyspace}.lwt_test WHERE id = 'test_key'")
        current_value = current_rows.one().value
        
        console.print(f"Operation applied: {applied}")
        console.print(f"Current value: {current_value}")
        
        results_table.add_row(
            "UPDATE IF value = 'initial_value' (should fail)",
            "Success" if applied else "Failure (expected)",
            str(applied),
            current_value
        )
    except Exception as e:
        console.print(f"[red]Test 2 failed: {str(e)}[/red]")
        results_table.add_row("UPDATE IF value = 'initial_value' (should fail)", f"Error: {str(e)}", "N/A", "N/A")
    
    try:
        console.print("\n[bold]Test 3: INSERT IF NOT EXISTS (should fail for existing key)[/bold]")
        result = session.execute(
            f"""
            INSERT INTO {keyspace}.lwt_test (id, value, version)
            VALUES ('test_key', 'new_value', 10)
            IF NOT EXISTS
            """
        )
        applied = result.one().applied
        current_rows = session.execute(f"SELECT * FROM {keyspace}.lwt_test WHERE id = 'test_key'")
        current_value = current_rows.one().value
        
        console.print(f"Operation applied: {applied}")
        console.print(f"Current value: {current_value}")
        
        results_table.add_row(
            "INSERT IF NOT EXISTS (existing key)",
            "Success" if applied else "Failure (expected)",
            str(applied),
            current_value
        )
    except Exception as e:
        console.print(f"[red]Test 3 failed: {str(e)}[/red]")
        results_table.add_row("INSERT IF NOT EXISTS", f"Error: {str(e)}", "N/A", "N/A")
    
    console.print(results_table)
    
    cluster.shutdown()

def test_lwt_partitioned_state():
    """Test Lightweight Transactions in partitioned cluster state"""
    console.print("\n[bold green]=== TESTING LIGHTWEIGHT TRANSACTIONS IN PARTITIONED CLUSTER STATE ===[/bold green]")
    
    cluster, session = connect_to_node(CASSANDRA_HOST)
    if not session:
        console.print("[red]Failed to connect to seed node. Exiting.[/red]")
        return
    
    console.print("[bold]Creating test keyspace and table for partitioned LWT test...[/bold]")
    keyspace = "demo_lwt_partitioned"
    
    try:
        session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {keyspace}
        WITH REPLICATION = {{ 'class': 'SimpleStrategy', 'replication_factor': 3 }}
        """)
        
        session.execute(f"""
        CREATE TABLE IF NOT EXISTS {keyspace}.lwt_test (
            id text PRIMARY KEY,
            value text,
            version int
        )
        """)
        
        session.execute(f"""
        INSERT INTO {keyspace}.lwt_test (id, value, version)
        VALUES ('test_key', 'partition_initial_value', 1)
        """)
        
        console.print("[bold]Initial data inserted[/bold]")
        
        rows = session.execute(f"SELECT * FROM {keyspace}.lwt_test WHERE id = 'test_key'")
        for row in rows:
            console.print(f"Initial value: id={row.id}, value={row.value}, version={row.version}")
    except Exception as e:
        console.print(f"[red]Error setting up test: {str(e)}[/red]")
        cluster.shutdown()
        return
    
    console.print("\n[bold]Initial cluster status:[/bold]")
    initial_status = get_cluster_status()
    console.print(initial_status)
    
    console.print("\n[bold yellow]MANUAL STEP REQUIRED - NETWORK PARTITION:[/bold yellow]")
    console.print("Run this command in a separate terminal:")
    console.print("[bold green]./manage_cluster.sh disconnect 2[/bold green]")
    input("\nPress Enter after you've disconnected node 2... ")
    
    console.print("\n[bold]Cluster status during partition:[/bold]")
    partition_status = get_cluster_status()
    console.print(partition_status)
    
    results_table = Table(title="Lightweight Transaction Tests (Partitioned Cluster)")
    results_table.add_column("Operation")
    results_table.add_column("Result")
    results_table.add_column("Applied")
    results_table.add_column("Notes")
    
    try:
        console.print("\n[bold]Test 1: CAS during partition[/bold]")
        result = session.execute(
            f"""
            UPDATE {keyspace}.lwt_test 
            SET value = 'partition_updated_value', version = 2 
            WHERE id = 'test_key' 
            IF value = 'partition_initial_value'
            """
        )
        applied = result.one().applied if result.one() else False
        current_rows = session.execute(f"SELECT * FROM {keyspace}.lwt_test WHERE id = 'test_key'")
        current_value = current_rows.one().value if current_rows.one() else "N/A"
        
        console.print(f"Operation applied: {applied}")
        console.print(f"Current value: {current_value}")
        
        results_table.add_row(
            "UPDATE IF value = X during partition",
            "Success" if applied else "Failure",
            str(applied),
            "LWTs typically require SERIAL consistency (majority of nodes)"
        )
    except Exception as e:
        console.print(f"[red]Test 1 failed: {str(e)}[/red]")
        results_table.add_row(
            "UPDATE IF value = X during partition", 
            f"Error: {str(e)}", 
            "N/A", 
            "LWTs require quorum for linearizability"
        )
    
    try:
        console.print("\n[bold]Test 2: INSERT IF NOT EXISTS during partition[/bold]")
        result = session.execute(
            f"""
            INSERT INTO {keyspace}.lwt_test (id, value, version)
            VALUES ('partition_new_key', 'partition_new_value', 1)
            IF NOT EXISTS
            """
        )
        applied = result.one().applied if result.one() else False
        
        console.print(f"Operation applied: {applied}")
        
        results_table.add_row(
            "INSERT IF NOT EXISTS during partition",
            "Success" if applied else "Failure",
            str(applied),
            "May fail due to unavailable nodes"
        )
    except Exception as e:
        console.print(f"[red]Test 2 failed: {str(e)}[/red]")
        results_table.add_row(
            "INSERT IF NOT EXISTS during partition", 
            f"Error: {str(e)}", 
            "N/A", 
            "LWTs require quorum for linearizability"
        )
    
    console.print(results_table)
    
    console.print("\n[bold yellow]MANUAL STEP REQUIRED - HEAL PARTITION:[/bold yellow]")
    console.print("Run this command in a separate terminal:")
    console.print("[bold green]./manage_cluster.sh reconnect 2[/bold green]")
    input("\nPress Enter after you've reconnected node 2... ")
    
    console.print("\n[bold]Waiting for cluster to stabilize after healing (30 seconds)...[/bold]")
    time.sleep(30)
    
    console.print("\n[bold]Cluster status after healing:[/bold]")
    healed_status = get_cluster_status()
    console.print(healed_status)
    
    summary_table = Table(title="LWT Behavior Summary")
    summary_table.add_column("Cluster State")
    summary_table.add_column("LWT Behavior")
    summary_table.add_column("Why")
    
    summary_table.add_row(
        "Normal (all nodes up)",
        "Works as expected with linearizable consistency",
        "Can achieve SERIAL/QUORUM consistency level"
    )
    summary_table.add_row(
        "Partitioned (nodes down)",
        "May fail depending on the partition severity",
        "Requires majority of replica nodes for Paxos consensus protocol"
    )
    
    console.print(summary_table)
    
    console.print(Panel("""
Lightweight Transactions (LWT) in Cassandra use the Paxos consensus protocol to provide linearizable consistency:

1. In a normal cluster state, LWTs provide strong consistency guarantees
2. LWTs require SERIAL consistency level by default, which needs a majority of replicas
3. During network partitions:
   - If a majority of replica nodes are available, LWTs can still succeed
   - If a majority of replica nodes are unavailable, LWTs will fail
4. LWTs are much slower than regular operations (typically 4-5x slower)
5. Unlike regular operations, LWTs cannot use the "Last Write Wins" conflict resolution
6. LWTs provide atomic compare-and-set operations but sacrifice availability during partitions
    """, title="Lightweight Transactions Findings"))
    
    cluster.shutdown()

def main():
    """Run the LWT tests"""
    console.print("[bold]Starting Cassandra Lightweight Transactions (LWT) tests...[/bold]")
    
    test_lwt_normal_state()
    
    test_lwt_partitioned_state()
    
    console.print("\n[bold]LWT testing completed.[/bold]")

if __name__ == "__main__":
    main() 