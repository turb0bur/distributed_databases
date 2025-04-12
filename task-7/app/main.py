#!/usr/bin/env python3
"""
Main application for Cassandra cluster exploration.
Demonstrates the basic operations of a multi-node Cassandra cluster.
Only includes non-interactive tasks (tasks 1-7) that can run automatically.
"""
import uuid
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from cassandra.cluster import ConsistencyLevel
from cassandra.query import SimpleStatement

import db_connection as db

log = logging.getLogger("cassandra-cluster")
console = Console()

class CassandraClusterExplorer:
    def __init__(self):
        self.cluster = None
        self.session = None
        self.connect()

    def connect(self):
        """Connect to the Cassandra cluster"""
        self.cluster, self.session = db.connect_to_cluster()

    def check_cluster_status(self):
        """Check the status of the cluster using nodetool status"""
        try:
            status_output = db.run_nodetool("status")
            console.print(Panel(status_output, title="Cluster Status", expand=False))
            return status_output
        except Exception as e:
            console.print(Panel(f"[bold red]Error checking cluster status: {str(e)}[/bold red]", title="Cluster Error", expand=False))
            return f"Error: {str(e)}"

    def insert_sample_data(self):
        """Insert sample data into all tables in each keyspace"""
        keyspaces = [
            db.os.environ.get('CASSANDRA_RF1_KEYSPACE', 'keyspace_rf1'),
            db.os.environ.get('CASSANDRA_RF2_KEYSPACE', 'keyspace_rf2'),
            db.os.environ.get('CASSANDRA_RF3_KEYSPACE', 'keyspace_rf3')
        ]
        
        for keyspace in keyspaces:
            try:
                self.session.execute(f"USE {keyspace}")
                
                for i in range(1, 6):
                    user_id = uuid.uuid4()
                    self.session.execute(
                        """
                        INSERT INTO users (user_id, username, email, created_at)
                        VALUES (%s, %s, %s, toTimestamp(now()))
                        """,
                        (user_id, f"user{i}", f"user{i}@example.com")
                    )
                
                product_categories = ["Electronics", "Clothing", "Home", "Books", "Food"]
                for i in range(1, 11):
                    product_id = uuid.uuid4()
                    category = product_categories[i % len(product_categories)]
                    self.session.execute(
                        """
                        INSERT INTO products (product_id, name, price, category, description)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (product_id, f"Product {i}", 10.0 * i, category, f"Description for product {i}")
                    )
                
                for i in range(1, 6):
                    order_id = uuid.uuid4()
                    user_id = uuid.uuid4()  # In a real scenario, you'd use an existing user_id
                    self.session.execute(
                        """
                        INSERT INTO orders (order_id, user_id, order_date, total_price, status)
                        VALUES (%s, %s, toTimestamp(now()), %s, %s)
                        """,
                        (order_id, user_id, 100.0 * i, "COMPLETED" if i % 2 == 0 else "PENDING")
                    )
                
                log.info(f"Inserted sample data into keyspace {keyspace}")
            except Exception as e:
                log.error(f"Failed to insert data into keyspace {keyspace}: {str(e)}")

    def get_endpoints_for_key(self, keyspace, table, key_column, key_value):
        """Get the nodes that contain a specific record"""
        try:
            if key_column.lower().endswith('id') and isinstance(key_value, str):
                try:
                    key_value = uuid.UUID(key_value)
                except ValueError:
                    pass
            
            if isinstance(key_value, uuid.UUID):
                token_query = f"SELECT token({key_column}) FROM {keyspace}.{table} WHERE {key_column} = {key_value}"
            else:
                token_query = f"SELECT token({key_column}) FROM {keyspace}.{table} WHERE {key_column} = '{key_value}'"
            
            token_result = None
            try:
                rows = self.session.execute(token_query)
                result_row = rows.one()
                if result_row is not None:
                    token_result = result_row[0]
            except Exception as e:
                log.error(f"Error getting token: {str(e)}")
            
            if token_result is None:
                return f"No record found with {key_column} = {key_value}"
            
            rf = 1
            try:
                keyspace_info = self.session.execute(f"SELECT replication FROM system_schema.keyspaces WHERE keyspace_name = '{keyspace}'").one()
                replication_info = keyspace_info.replication
                rf = int(replication_info.get('replication_factor', '1'))
            except Exception as e:
                log.error(f"Error getting keyspace info: {str(e)}")
            
            endpoints_output = db.run_nodetool(f"getendpoints {keyspace} {table} {token_result}")
            return f"Replication Factor: {rf}\n{endpoints_output}"
        except Exception as e:
            log.error(f"Failed to get endpoints: {str(e)}")
            return f"Error: {str(e)}"

    def run_demo(self):
        """Run the basic demonstration (tasks 1-7)"""
        with console.status("[bold green]Running Cassandra cluster demo...") as status:
            status.update("[bold green]Checking cluster status...")
            
            status.stop()
            self.check_cluster_status()
            console.print("[bold]---------------------------------------------------[/bold]")
            
            status.start()
            status.update("[bold green]Creating keyspaces...")
            try:
                db.create_keyspaces(self.session)
            except Exception as e:
                console.print(f"[bold red]Error creating keyspaces: {str(e)}[/bold red]")
            console.print("[bold]---------------------------------------------------[/bold]")
            
            status.update("[bold green]Creating tables...")
            try:
                db.create_tables(self.session)
            except Exception as e:
                console.print(f"[bold red]Error creating tables: {str(e)}[/bold red]")
            console.print("[bold]---------------------------------------------------[/bold]")
            
            status.update("[bold green]Inserting sample data...")
            try:
                self.insert_sample_data()
            except Exception as e:
                console.print(f"[bold red]Error inserting sample data: {str(e)}[/bold red]")
            console.print("[bold]---------------------------------------------------[/bold]")
            
            status.update("[bold green]Checking data distribution...")
            
            status.stop()
            self.check_cluster_status()
            console.print("[bold]---------------------------------------------------[/bold]")
            
            status.start()
            status.update("[bold green]Showing data location for specific records...")
            keyspaces = [
                db.os.environ.get('CASSANDRA_RF1_KEYSPACE', 'keyspace_rf1'),
                db.os.environ.get('CASSANDRA_RF2_KEYSPACE', 'keyspace_rf2'),
                db.os.environ.get('CASSANDRA_RF3_KEYSPACE', 'keyspace_rf3')
            ]
            
            rf_table = Table(title="Replication Factor Test")
            rf_table.add_column("Keyspace")
            rf_table.add_column("Replication Factor")
            rf_table.add_column("Record ID")
            rf_table.add_column("Nodes Containing Data")
            
            total_nodes = 0
            try:
                peer_rows = list(self.session.execute("SELECT * FROM system.peers"))
                total_nodes = len(peer_rows) + 1
            except Exception as e:
                console.print(f"[bold yellow]Warning: Could not determine total node count: {str(e)}[/bold yellow]")
                total_nodes = 3
                
            for keyspace in keyspaces:
                rf = keyspace[-1]
                try:
                    self.session.execute(f"USE {keyspace}")
                    
                    try:
                        product_rows = list(self.session.execute("SELECT product_id FROM products LIMIT 1"))
                        if product_rows:
                            product_id = product_rows[0].product_id
                            endpoints_output = self.get_endpoints_for_key(keyspace, "products", "product_id", product_id)
                            
                            # Extract only the node IPs, not the warning or total count
                            clean_node_lines = []
                            for line in endpoints_output.strip().split('\n'):
                                line = line.strip()
                                if line and not line.startswith("Replication Factor:") and not line.startswith("WARNING:") and not line.startswith("Total nodes"):
                                    clean_node_lines.append(line)
                            
                            # Get the actual total node count (displayed separately)
                            actual_total = 0
                            for line in endpoints_output.strip().split('\n'):
                                if line.startswith("Total nodes in cluster:"):
                                    try:
                                        actual_total = int(line.split(":")[1].strip())
                                    except:
                                        actual_total = len(clean_node_lines)
                            
                            # Format the output
                            rf_int = int(rf)
                            rf_display = f"Replication Factor: {rf}"
                            
                            # Add explanation if RF > actual nodes
                            if rf_int > actual_total:
                                rf_display += f"\n[yellow]Note: RF={rf} exceeds available nodes ({actual_total})[/yellow]"
                            
                            # Add the node IPs as a comma-separated list
                            node_count = len(clean_node_lines)
                            node_display = f"{node_count} node(s):\n{rf_display}\n{', '.join(clean_node_lines)}"
                            
                            rf_table.add_row(
                                keyspace,
                                rf,
                                str(product_id),
                                node_display
                            )
                        else:
                            rf_table.add_row(
                                keyspace,
                                rf,
                                "N/A",
                                "No data found in table"
                            )
                    except Exception as e:
                        rf_table.add_row(
                            keyspace,
                            rf,
                            "ERROR",
                            f"Error retrieving data: {str(e).split('(')[0]}"
                        )
                except Exception as e:
                    rf_table.add_row(
                        keyspace,
                        rf,
                        "ERROR",
                        f"Could not connect to keyspace: {str(e).split('(')[0]}"
                    )
            
            status.stop()
            console.print(rf_table)
            console.print("[bold]---------------------------------------------------[/bold]")
            
            log.info("Basic demo completed (tasks 1-7)")

    def close(self):
        """Close the connection to the cluster"""
        if self.cluster:
            self.cluster.shutdown()

if __name__ == "__main__":
    db.wait_for_cluster_ready()
    try:
        explorer = CassandraClusterExplorer()
        explorer.run_demo()
    except Exception as e:
        log.error(f"Error in Cassandra Cluster Explorer: {str(e)}", exc_info=True)
    finally:
        if 'explorer' in locals():
            explorer.close() 