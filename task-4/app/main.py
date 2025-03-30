import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class Neo4jStore:
    def __init__(self):
        auth = os.getenv('NEO4J_AUTH')
        if not auth:
            raise ValueError("NEO4J_AUTH environment variable is not set")
        username, password = auth.split('/')
        
        bolt_port = os.getenv('NEO4J_BOLT_PORT', '7687')
        host = os.getenv('NEO4J_HOST', 'neo4j')
        
        uri = f'bolt://{host}:{bolt_port}'
        
        try:
            self.driver = GraphDatabase.driver(
                uri,
                auth=(username, password)
            )
            self.driver.verify_connectivity()
        except Exception as e:
            raise Exception(f"Failed to connect to Neo4j at {uri}: {str(e)}")

    def close(self):
        if hasattr(self, 'driver'):
            self.driver.close()

    def create_sample_data(self):
        with self.driver.session() as session:
            # Create customers
            session.run("""
                CREATE (c1:Customer {id: 'C1', name: 'John Doe'})
                CREATE (c2:Customer {id: 'C2', name: 'Jane Smith'})
                CREATE (c3:Customer {id: 'C3', name: 'Bob Johnson'})
            """)

            # Create items
            session.run("""
                CREATE (i1:Item {id: 'I1', name: 'Laptop', price: 999.99})
                CREATE (i2:Item {id: 'I2', name: 'Phone', price: 699.99})
                CREATE (i3:Item {id: 'I3', name: 'Headphones', price: 99.99})
                CREATE (i4:Item {id: 'I4', name: 'Tablet', price: 499.99})
            """)

            # Create orders
            session.run("""
                CREATE (o1:Order {id: 'O1', date: datetime('2024-01-01')})
                CREATE (o2:Order {id: 'O2', date: datetime('2024-01-15')})
                CREATE (o3:Order {id: 'O3', date: datetime('2024-02-01')})
            """)

            # Create relationships
            session.run("""
                MATCH (c:Customer {id: 'C1'})
                MATCH (o:Order {id: 'O1'})
                CREATE (c)-[:BOUGHT]->(o)
            """)

            session.run("""
                MATCH (c:Customer {id: 'C1'})
                MATCH (o:Order {id: 'O2'})
                CREATE (c)-[:BOUGHT]->(o)
            """)

            session.run("""
                MATCH (o:Order {id: 'O1'})
                MATCH (i:Item {id: 'I1'})
                CREATE (o)-[:CONTAINS]->(i)
            """)

            session.run("""
                MATCH (o:Order {id: 'O1'})
                MATCH (i:Item {id: 'I2'})
                CREATE (o)-[:CONTAINS]->(i)
            """)

            session.run("""
                MATCH (c:Customer {id: 'C1'})
                MATCH (i:Item {id: 'I3'})
                CREATE (c)-[:VIEWED]->(i)
            """)

    def find_items_in_order(self, order_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (o:Order {id: $order_id})-[:CONTAINS]->(i:Item)
                RETURN i
            """, order_id=order_id)
            return [dict(record["i"]) for record in result]

    def calculate_order_cost(self, order_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (o:Order {id: $order_id})-[:CONTAINS]->(i:Item)
                RETURN sum(i.price) as total_cost
            """, order_id=order_id)
            return result.single()["total_cost"]

    def find_customer_orders(self, customer_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Customer {id: $customer_id})-[:BOUGHT]->(o:Order)
                RETURN o
            """, customer_id=customer_id)
            return [dict(record["o"]) for record in result]

    def find_customer_purchased_items(self, customer_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Customer {id: $customer_id})-[:BOUGHT]->(o:Order)-[:CONTAINS]->(i:Item)
                RETURN DISTINCT i
            """, customer_id=customer_id)
            return [dict(record["i"]) for record in result]

    def count_customer_purchased_items(self, customer_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Customer {id: $customer_id})-[:BOUGHT]->(o:Order)-[:CONTAINS]->(i:Item)
                RETURN count(i) as item_count
            """, customer_id=customer_id)
            return result.single()["item_count"]

    def calculate_customer_total_purchase(self, customer_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Customer {id: $customer_id})-[:BOUGHT]->(o:Order)-[:CONTAINS]->(i:Item)
                RETURN sum(i.price) as total_amount
            """, customer_id=customer_id)
            return result.single()["total_amount"]

    def count_item_purchase_frequency(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (o:Order)-[:CONTAINS]->(i:Item)
                RETURN i.name as item_name, count(*) as purchase_count
                ORDER BY purchase_count DESC
            """)
            return [dict(record) for record in result]

    def find_customer_viewed_items(self, customer_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Customer {id: $customer_id})-[:VIEWED]->(i:Item)
                RETURN i
            """, customer_id=customer_id)
            return [dict(record["i"]) for record in result]

    def find_related_purchased_items(self, item_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i1:Item {id: $item_id})<-[:CONTAINS]-(o:Order)-[:CONTAINS]->(i2:Item)
                WHERE i2.id <> $item_id
                RETURN i2.name as related_item, count(*) as frequency
                ORDER BY frequency DESC
            """, item_id=item_id)
            return [dict(record) for record in result]

    def find_item_customers(self, item_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i:Item {id: $item_id})<-[:CONTAINS]-(o:Order)<-[:BOUGHT]-(c:Customer)
                RETURN DISTINCT c
            """, item_id=item_id)
            return [dict(record["c"]) for record in result]

    def find_customer_unpurchased_viewed_items(self, customer_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Customer {id: $customer_id})-[:VIEWED]->(i:Item)
                WHERE NOT EXISTS((c)-[:BOUGHT]->(:Order)-[:CONTAINS]->(i))
                RETURN i
            """, customer_id=customer_id)
            return [dict(record["i"]) for record in result]

def main():
    store = Neo4jStore()
    try:
        store.create_sample_data()
        
        print("\n1. Items in Order O1:")
        print(store.find_items_in_order('O1'))
        
        print("\n2. Cost of Order O1:")
        print(store.calculate_order_cost('O1'))
        
        print("\n3. Orders of Customer C1:")
        print(store.find_customer_orders('C1'))
        
        print("\n4. Items purchased by Customer C1:")
        print(store.find_customer_purchased_items('C1'))
        
        print("\n5. Number of items purchased by Customer C1:")
        print(store.count_customer_purchased_items('C1'))
        
        print("\n6. Total amount purchased by Customer C1:")
        print(store.calculate_customer_total_purchase('C1'))
        
        print("\n7. Item purchase frequency:")
        print(store.count_item_purchase_frequency())
        
        print("\n8. Items viewed by Customer C1:")
        print(store.find_customer_viewed_items('C1'))
        
        print("\n9. Items purchased together with I1:")
        print(store.find_related_purchased_items('I1'))
        
        print("\n10. Customers who bought I1:")
        print(store.find_item_customers('I1'))
        
        print("\n11. Items viewed but not purchased by Customer C1:")
        print(store.find_customer_unpurchased_viewed_items('C1'))
        
    finally:
        store.close()

if __name__ == "__main__":
    main() 