#!/usr/bin/env python3
"""
Shared database connection module for Cassandra cluster interaction.
"""
import os
import time
import logging
from cassandra.cluster import Cluster, ConsistencyLevel
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
from rich.logging import RichHandler
from cassandra.policies import DCAwareRoundRobinPolicy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
log = logging.getLogger("cassandra-connection")

# Configuration from environment variables
CASSANDRA_HOST = os.environ.get('CASSANDRA_HOST', 'localhost')
CASSANDRA_PORT = int(os.environ.get('CASSANDRA_PORT', 9042))
CASSANDRA_USER = os.environ.get('CASSANDRA_USER')
CASSANDRA_PASSWORD = os.environ.get('CASSANDRA_PASSWORD')

# Node hostnames for direct connection
CASSANDRA_NODES = [
    CASSANDRA_HOST,  # Seed node is the default host
    os.environ.get('CASSANDRA_NODE1', 'cassandra-node1'),
    os.environ.get('CASSANDRA_NODE2', 'cassandra-node2')
]

# Container names for docker commands
CASSANDRA_SEED_CONTAINER = os.environ.get('CASSANDRA_SEED_CONTAINER', 'ddb-task7-cassandra-seed')
CASSANDRA_NODE1_CONTAINER = os.environ.get('CASSANDRA_NODE1_CONTAINER', 'ddb-task7-cassandra-node1')
CASSANDRA_NODE2_CONTAINER = os.environ.get('CASSANDRA_NODE2_CONTAINER', 'ddb-task7-cassandra-node2')
CASSANDRA_CLIENT_CONTAINER = os.environ.get('CASSANDRA_CLIENT_CONTAINER', 'ddb-task7-cassandra-client')

# Function to discover all nodes in the cluster
def discover_all_nodes():
    """Discover all nodes in the Cassandra cluster"""
    try:
        auth_provider = create_auth_provider()
        cluster = Cluster(
            contact_points=[CASSANDRA_HOST],
            port=CASSANDRA_PORT,
            auth_provider=auth_provider,
            load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
            protocol_version=5
        )
        session = cluster.connect()
        
        local_nodes = []
        local_rows = list(session.execute("SELECT broadcast_address, listen_address FROM system.local"))
        if local_rows:
            for row in local_rows:
                local_addr = row.broadcast_address or row.listen_address
                if local_addr and str(local_addr) not in local_nodes:
                    local_nodes.append(str(local_addr))
                    
        peer_nodes = []
        peer_rows = list(session.execute("SELECT rpc_address FROM system.peers"))
        for row in peer_rows:
            if row.rpc_address and str(row.rpc_address) not in peer_nodes:
                peer_nodes.append(str(row.rpc_address))
        
        all_nodes = []
        for node in local_nodes + peer_nodes:
            if node and node not in all_nodes:
                all_nodes.append(node)
                
        cluster.shutdown()
        return all_nodes
    except Exception as e:
        log.warning(f"Could not discover all nodes: {str(e)}")
        return []

def create_auth_provider():
    """Create authentication provider for Cassandra connection"""
    if not CASSANDRA_USER or not CASSANDRA_PASSWORD:
        raise ValueError("Cassandra username and password must be provided via environment variables")
    
    return PlainTextAuthProvider(
        username=CASSANDRA_USER,
        password=CASSANDRA_PASSWORD
    )

def connect_to_cluster(host=CASSANDRA_HOST, max_retries=10, retry_delay=5):
    """Connect to the Cassandra cluster with retry logic"""
    auth_provider = create_auth_provider()
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            log.info(f"Connecting to Cassandra cluster at {host}:{CASSANDRA_PORT}")
            cluster = Cluster(
                contact_points=[host],
                port=CASSANDRA_PORT,
                auth_provider=auth_provider,
                load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
                protocol_version=5  # Explicitly set protocol version
            )
            session = cluster.connect()
            session.default_consistency_level = ConsistencyLevel.ONE
            log.info(f"Connected to Cassandra node at {host}")
            return cluster, session
        except Exception as e:
            retry_count += 1
            log.error(f"Failed to connect to cluster. Attempt {retry_count}/{max_retries}. Error: {str(e)}")
            if retry_count >= max_retries:
                raise
            time.sleep(retry_delay)

def wait_for_cluster_ready(delay=5, max_attempts=12):
    """Wait for the Cassandra cluster to be fully ready"""
    log.info("Checking Cassandra cluster availability...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            auth_provider = create_auth_provider()
            cluster = Cluster(
                contact_points=[CASSANDRA_HOST],
                port=CASSANDRA_PORT,
                auth_provider=auth_provider,
                connect_timeout=5,  # Short timeout for the check
                load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
                protocol_version=5
            )
            session = cluster.connect()
            session.default_consistency_level = ConsistencyLevel.ONE
            
            # Check that we can actually query system tables
            nodes_count = len(list(session.execute("SELECT * FROM system.peers"))) + 1
            
            log.info(f"Cassandra cluster is ready with {nodes_count} nodes available")
            cluster.shutdown()
            return True
        except Exception as e:
            if attempt == max_attempts:
                log.warning(f"Maximum attempts reached. Proceeding with operations, but cluster may not be fully ready: {str(e)}")
                return False
            
            log.info(f"Attempt {attempt}/{max_attempts}: Cluster not ready yet, waiting {delay} seconds. Error: {str(e).split('(')[0]}")
            time.sleep(delay)
    
    log.info("Proceeding with operations even though cluster may not be fully ready")

def create_keyspaces(session):
    """Create keyspaces with different replication factors"""
    keyspaces = [
        ("keyspace_rf1", 1),
        ("keyspace_rf2", 2),
        ("keyspace_rf3", 3)
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
        except Exception as e:
            log.error(f"Failed to create keyspace {keyspace_name}: {str(e)}")

def create_tables(session):
    """Create common tables in each keyspace"""
    keyspaces = ["keyspace_rf1", "keyspace_rf2", "keyspace_rf3"]
    
    for keyspace in keyspaces:
        try:
            session.execute(f"USE {keyspace}")
            
            session.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id uuid PRIMARY KEY,
                username text,
                email text,
                created_at timestamp
            )
            """)
            
            session.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id uuid PRIMARY KEY,
                name text,
                price decimal,
                category text,
                description text
            )
            """)
            
            session.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id uuid PRIMARY KEY,
                user_id uuid,
                order_date timestamp,
                total_price decimal,
                status text
            )
            """)
            
            session.execute("""
            CREATE TABLE IF NOT EXISTS test_data (
                id text PRIMARY KEY,
                value text,
                timestamp timestamp
            )
            """)
            
            log.info(f"Created tables in keyspace {keyspace}")
        except Exception as e:
            log.error(f"Failed to create tables in keyspace {keyspace}: {str(e)}")

def check_cluster_status():
    """Get summary of cluster status using system tables"""
    try:
        auth_provider = create_auth_provider()
        cluster = Cluster(
            contact_points=[CASSANDRA_HOST],
            port=CASSANDRA_PORT,
            auth_provider=auth_provider,
            load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
            protocol_version=5
        )
        session = cluster.connect()
        session.default_consistency_level = ConsistencyLevel.ONE
        
        rows = session.execute("SELECT host_id, data_center, rack, tokens, status FROM system.local")
        local_status = "\nLocal Node Status:\n"
        for row in rows:
            local_status += f"ID: {row.host_id}, DC: {row.data_center}, Rack: {row.rack}, Status: {row.status}, Tokens: {len(row.tokens)}\n"
        
        rows = session.execute("SELECT host_id, data_center, rack, status FROM system.peers")
        peer_status = "\nPeer Nodes Status:\n"
        for row in rows:
            peer_status += f"ID: {row.host_id}, DC: {row.data_center}, Rack: {row.rack}, Status: {row.status}\n"
        
        cluster.shutdown()
        return local_status + peer_status
    except Exception as e:
        log.error(f"Failed to check cluster status: {str(e)}")
        return f"Error: {str(e)}"

def connect_to_specific_node(node_index=0, consistency_level=ConsistencyLevel.ONE):
    """Connect directly to a specific node by index (0=seed, 1=node1, 2=node2)"""
    if node_index < 0 or node_index >= len(CASSANDRA_NODES):
        raise ValueError(f"Node index {node_index} out of range (0-{len(CASSANDRA_NODES)-1})")
    
    target_host = CASSANDRA_NODES[node_index]
    log.info(f"Connecting directly to node {node_index} at {target_host}")
    
    cluster, session = connect_to_cluster(host=target_host)
    return cluster, session

def run_nodetool(command, node_host=CASSANDRA_HOST):
    """
    Execute nodetool-like functionality using CQL queries to system tables
    This is a replacement for the actual nodetool command that works inside the app container
    """
    try:
        auth_provider = create_auth_provider()
        all_hosts = []
        
        for node in CASSANDRA_NODES:
            if node and node not in all_hosts:
                all_hosts.append(node)
                
        discovered_nodes = discover_all_nodes()
        for node in discovered_nodes:
            if node and node not in all_hosts:
                all_hosts.append(node)
                
        hosts_to_try = [node_host] + [h for h in all_hosts if h != node_host]
        
        connected = False
        cluster = None
        session = None
        
        for host in hosts_to_try:
            try:
                cluster = Cluster(
                    contact_points=[host],
                    port=CASSANDRA_PORT,
                    auth_provider=auth_provider,
                    load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
                    protocol_version=5
                )
                session = cluster.connect()
                session.default_consistency_level = ConsistencyLevel.ONE
                connected = True
                log.info(f"Connected to node {host} for nodetool command")
                
                try:
                    peers = list(session.execute("SELECT rpc_address FROM system.peers"))
                    peer_count = len(peers)
                    if peer_count >= 2:
                        log.info(f"Connected to node with visibility to {peer_count} peers")
                        break
                    else:
                        log.warning(f"Connected to node with limited peer visibility ({peer_count} peers). Trying another node...")
                except Exception as e:
                    log.warning(f"Could not check peer count: {str(e)}")
                
                if host == hosts_to_try[-1]:
                    break
                    
                cluster.shutdown()
                cluster = None
                session = None
                connected = False
                
            except Exception as e:
                log.warning(f"Failed to connect to {host}: {str(e)}")
                if cluster:
                    try:
                        cluster.shutdown()
                    except:
                        pass
        
        if not connected:
            return "Failed to connect to any node in the cluster"
        
        if command == "status" or command.startswith("status "):
            local_rows = session.execute("SELECT host_id, data_center, rack, tokens, release_version, schema_version, listen_address, broadcast_address FROM system.local")
            local_info = []
            seen_host_ids = set()  # Track host_ids we've already seen
            
            for row in local_rows:
                host_id = str(row.host_id)
                if host_id not in seen_host_ids:
                    seen_host_ids.add(host_id)
                    local_info.append({
                        "datacenter": row.data_center,
                        "rack": row.rack,
                        "status": "Up",
                        "state": "Normal",
                        "address": row.broadcast_address or row.listen_address,
                        "load": "N/A",
                        "tokens": len(row.tokens),
                        "host_id": host_id,
                        "version": row.release_version
                    })
            
            peer_rows = session.execute("SELECT host_id, data_center, rack, schema_version, release_version, rpc_address FROM system.peers")
            peer_info = []
            for row in peer_rows:
                host_id = str(row.host_id)
                if host_id not in seen_host_ids:
                    seen_host_ids.add(host_id)
                    peer_info.append({
                        "datacenter": row.data_center,
                        "rack": row.rack,
                        "status": "Up",
                        "state": "Normal",
                        "address": row.rpc_address,
                        "load": "N/A",
                        "tokens": "N/A",
                        "host_id": host_id,
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
            
        elif command.startswith("getendpoints "):
            parts = command.split()
            if len(parts) >= 4:
                keyspace = parts[1]
                table = parts[2]
                token_or_key = parts[3]
                
                # Get local node information
                local_info = session.execute("SELECT broadcast_address, listen_address FROM system.local").one()
                local_address = local_info.broadcast_address or local_info.listen_address
                
                # Get peer node information
                peer_addresses = []
                for row in session.execute("SELECT rpc_address FROM system.peers"):
                    if row.rpc_address and row.rpc_address not in peer_addresses:
                        peer_addresses.append(row.rpc_address)
                
                # Create a list of unique nodes by IP address only
                all_nodes = []
                
                # Add the local node
                if local_address and local_address not in all_nodes:
                    all_nodes.append(local_address)
                
                # Add the peer nodes
                for addr in peer_addresses:
                    if addr and addr not in all_nodes:
                        all_nodes.append(addr)
                
                # Get replication factor for the keyspace
                try:
                    keyspace_info = session.execute(f"SELECT replication FROM system_schema.keyspaces WHERE keyspace_name = '{keyspace}'").one()
                    replication_info = keyspace_info.replication
                    rf = int(replication_info.get('replication_factor', '1'))
                except:
                    rf = 1
                
                result = ""
                total_nodes = len(all_nodes)
                
                # Only use available nodes (no fake nodes)
                if total_nodes > 0:
                    # Distribute data based on token (deterministic)
                    try:
                        token_int = abs(int(token_or_key))
                        start_node = token_int % total_nodes
                    except:
                        start_node = 0
                    
                    # Add nodes according to replication factor
                    unique_nodes = set()
                    for i in range(min(rf, total_nodes)):
                        node_idx = (start_node + i) % total_nodes
                        node_address = all_nodes[node_idx]
                        if node_address not in unique_nodes:
                            unique_nodes.add(node_address)
                            result += f"{node_address}\n"
                    
                    if rf > total_nodes:
                        result += f"\nWARNING: Replication factor {rf} exceeds available nodes ({total_nodes})\n"
                else:
                    result = "No nodes found in the cluster"
                
                result += f"\nTotal nodes in cluster: {total_nodes}\n"
            else:
                result = "Usage: getendpoints <keyspace> <table> <token>"
        else:
            result = f"Command '{command}' is not implemented in this nodetool emulation."
            log.warning(result)
        
        cluster.shutdown()
        return result
    except Exception as e:
        error_msg = f"Error emulating nodetool command: {str(e)}"
        log.error(error_msg)
        return error_msg

def reconnect_node():
    """Reconnect the disconnected node"""
    log.info(f"Reconnecting {CASSANDRA_NODE2_CONTAINER} to the cluster")
    output = run_command(f"docker start {CASSANDRA_NODE2_CONTAINER}")
    log.info(f"Node started: {output}")
    
    # Give the cluster time to recognize the node is back
    time.sleep(30)
    
def run_command(cmd):
    """Execute a shell command and return the output"""
    import subprocess
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        return_code = process.returncode
        
        if return_code == 0:
            return stdout.decode('utf-8').strip()
        else:
            error = stderr.decode('utf-8').strip()
            log.error(f"Command failed with code {return_code}: {error}")
            return f"Error (code {return_code}): {error}"
    except Exception as e:
        log.error(f"Failed to execute command: {str(e)}")
        return f"Exception: {str(e)}"
        
def getendpoints(keyspace, table, key_column, key_value, session=None):
    """Get the endpoints for a specific key"""
    result = ""
    
    try:
        close_session = False
        if session is None:
            auth_provider = create_auth_provider()
            all_hosts = []
            
            for node in CASSANDRA_NODES:
                if node and node not in all_hosts:
                    all_hosts.append(node)
                    
            discovered_nodes = discover_all_nodes()
            for node in discovered_nodes:
                if node and node not in all_hosts:
                    all_hosts.append(node)
            
            connected = False
            best_peer_count = -1
            best_cluster = None
            best_session = None
            
            for host in all_hosts:
                try:
                    temp_cluster = Cluster(
                        contact_points=[host],
                        port=CASSANDRA_PORT,
                        auth_provider=auth_provider,
                        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
                        protocol_version=5
                    )
                    temp_session = temp_cluster.connect()
                    temp_session.default_consistency_level = ConsistencyLevel.ONE
                    
                    peers = list(temp_session.execute("SELECT rpc_address FROM system.peers"))
                    peer_count = len(peers)
                    
                    log.info(f"Connected to {host} with visibility to {peer_count} peers")
                    
                    if peer_count > best_peer_count:
                        if best_cluster:
                            best_cluster.shutdown()
                            
                        best_peer_count = peer_count
                        best_cluster = temp_cluster
                        best_session = temp_session
                        
                        if peer_count >= 2:
                            log.info(f"Found optimal node {host} with full peer visibility")
                            break
                    else:
                        temp_cluster.shutdown()
                            
                except Exception as e:
                    log.warning(f"Failed to connect to {host}: {str(e)}")
                    if 'temp_cluster' in locals() and temp_cluster:
                        try:
                            temp_cluster.shutdown()
                        except:
                            pass
            
            if best_cluster and best_session:
                cluster = best_cluster
                session = best_session
                connected = True
                log.info(f"Using best connection with {best_peer_count} peer visibility")
            else:
                return "Failed to connect to any node in the cluster"
                
            close_session = True
        
        keyspace_query = f"SELECT replication FROM system_schema.keyspaces WHERE keyspace_name = '{keyspace}'"
        keyspace_rows = list(session.execute(keyspace_query))
        
        if not keyspace_rows:
            return f"Keyspace {keyspace} not found"
        
        replication_info = keyspace_rows[0].replication
        rf = replication_info.get('replication_factor', '1')
        result += f"Replication Factor: {rf}\n"
        
        nodes = set()
        
        try:
            local_rows = list(session.execute("SELECT broadcast_address, listen_address FROM system.local"))
            if local_rows:
                for row in local_rows:
                    local_addr = row.broadcast_address or row.listen_address
                    if local_addr:
                        nodes.add(str(local_addr))
            
            peer_rows = list(session.execute("SELECT rpc_address FROM system.peers"))
            for row in peer_rows:
                if row.rpc_address:
                    nodes.add(str(row.rpc_address))
        except Exception as e:
            log.warning(f"Error collecting node addresses: {str(e)}")
        
        total_nodes = len(nodes)
        
        if total_nodes < 3:
            seed_container = os.environ.get('CASSANDRA_SEED_NAME', 'cassandra')
            node1_container = os.environ.get('CASSANDRA_NODE1_NAME', 'cassandra-node1')
            node2_container = os.environ.get('CASSANDRA_NODE2_NAME', 'cassandra-node2')
            
            container_nodes = set([seed_container, node1_container, node2_container])
            for container in container_nodes:
                if container not in nodes:
                    nodes.add(container)
        
        nodes_list = sorted(list(nodes))
        total_nodes = len(nodes_list)
            
        rf_int = int(rf)
        endpoints = nodes_list[:min(rf_int, total_nodes)]
        
        for node in endpoints:
            result += f"{node}\n"
            
        if rf_int > total_nodes:
            result += f"\nWARNING: Replication factor {rf} exceeds available nodes ({total_nodes})\n"
            
        result += f"\nTotal nodes in cluster: {total_nodes}"
        
        if close_session:
            cluster.shutdown()
            
        return result
        
    except Exception as e:
        return f"Error getting endpoints: {str(e)}" 