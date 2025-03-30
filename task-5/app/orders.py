import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional

from db_connection import session

def create_order(customer_name: str, products: List[uuid.UUID], total_value: float, ttl: Optional[int] = None):
    """Create a new order with optional TTL"""
    order_id = uuid.uuid4()
    order_date = datetime.now()
    
    query = """
        INSERT INTO orders (customer_name, order_id, order_date, products, total_value)
        VALUES (%s, %s, %s, %s, %s)
    """
    
    if ttl:
        query += f" USING TTL {ttl}"
    
    session.execute(query, (customer_name, order_id, order_date, products, total_value))
    return order_id

def get_order_by_id(customer_name: str, order_id: uuid.UUID):
    """Get an order by its ID
    
    Handles the Cassandra primary key structure by first querying by customer_name
    and order_date range, then filtering for the specific order_id.
    
    Args:
        customer_name: The customer's name
        order_id: The order UUID
        
    Returns:
        The order row or None if not found
    """
    result = session.execute("""
        SELECT * FROM orders
        WHERE customer_name = %s AND order_date >= %s AND order_date <= %s
    """, (customer_name, datetime.min, datetime.max))
    
    for row in result:
        if row.order_id == order_id:
            return row
    
    return None

def get_customer_orders(customer_name: str):
    """Get all orders for a customer sorted by date"""
    result = session.execute("""
        SELECT * FROM orders
        WHERE customer_name = %s
        ORDER BY order_date DESC
    """, (customer_name,))
    return list(result)

def get_customer_orders_with_product(customer_name: str, product_id: uuid.UUID):
    """Get orders containing a specific product for a customer"""
    result = session.execute("""
        SELECT * FROM orders
        WHERE customer_name = %s AND products CONTAINS %s
        ORDER BY order_date DESC
    """, (customer_name, product_id))
    return list(result)

def get_customer_orders_by_date_range(customer_name: str, start_date: datetime, end_date: datetime):
    """Get orders within a date range for a customer"""
    result = session.execute("""
        SELECT * FROM orders
        WHERE customer_name = %s AND order_date >= %s AND order_date <= %s
        ORDER BY order_date DESC
    """, (customer_name, start_date, end_date))
    return list(result)

def get_customer_total_spent(customer_name: str):
    """Get total amount spent by a customer"""
    result = session.execute("""
        SELECT SUM(total_value) as total
        FROM orders
        WHERE customer_name = %s
    """, (customer_name,))
    return result[0].total if result[0].total else 0

def get_customer_max_order(customer_name: str):
    """Get the order with maximum value for a customer"""
    result = session.execute("""
        SELECT * FROM orders
        WHERE customer_name = %s
    """, (customer_name,))
    
    # Find the order with maximum value in Python
    orders = list(result)
    if not orders:
        return None
    
    return max(orders, key=lambda x: x.total_value)

def update_order(customer_name: str, order_id: uuid.UUID, products: List[uuid.UUID], total_value: float):
    """Update an existing order"""
    try:
        order = get_order_by_id(customer_name, order_id)
        
        if not order:
            print(f"Order {order_id} not found for customer {customer_name}")
            return False
        
        session.execute("""
            UPDATE orders
            SET products = %s, total_value = %s
            WHERE customer_name = %s AND order_date = %s AND order_id = %s
        """, (products, total_value, customer_name, order.order_date, order_id))
        return True
        
    except Exception as e:
        print(f"Error updating order: {str(e)}")
        return False

def get_order_writetime(customer_name: str, order_id: uuid.UUID):
    """Get the writetime of an order"""
    try:
        order = get_order_by_id(customer_name, order_id)
        
        if not order:
            print(f"Order {order_id} not found for customer {customer_name}")
            return None
        
        result = session.execute("""
            SELECT WRITETIME(total_value) as writetime
            FROM orders
            WHERE customer_name = %s AND order_date = %s AND order_id = %s
        """, (customer_name, order.order_date, order_id))
        
        if not result:
            print(f"Could not get writetime for order {order_id}")
            return None
            
        return result[0].writetime
        
    except Exception as e:
        print(f"Error getting writetime: {str(e)}")
        return None

def get_order_as_json(customer_name: str, order_id: uuid.UUID):
    """Return an order in JSON format"""
    try:
        order = get_order_by_id(customer_name, order_id)
        
        if not order:
            print(f"Order {order_id} not found for customer {customer_name}")
            return None
        
        # Convert UUID objects to strings for JSON serialization
        order_dict = {
            "customer_name": order.customer_name,
            "order_id": str(order.order_id),
            "order_date": order.order_date.isoformat(),
            "products": [str(product) for product in order.products],
            "total_value": float(order.total_value)
        }
        
        return json.dumps(order_dict)
        
    except Exception as e:
        print(f"Error getting order as JSON: {str(e)}")
        return None

def add_order_from_json(order_json: str, ttl: Optional[int] = None):
    """Add an order from JSON data"""
    try:
        order_data = json.loads(order_json)
        
        # Extract and validate required fields
        customer_name = order_data.get("customer_name")
        if not customer_name:
            return None
        
        # Convert string products to UUIDs
        products = [uuid.UUID(p) for p in order_data.get("products", [])]
        
        # Use provided order_id or generate a new one
        order_id = uuid.UUID(order_data.get("order_id")) if "order_id" in order_data else uuid.uuid4()
        
        # Use provided order_date or current time
        order_date = datetime.fromisoformat(order_data.get("order_date")) if "order_date" in order_data else datetime.now()
        
        total_value = float(order_data.get("total_value", 0))
        
        query = """
            INSERT INTO orders (customer_name, order_id, order_date, products, total_value)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        if ttl:
            query += f" USING TTL {ttl}"
        
        session.execute(query, (customer_name, order_id, order_date, products, total_value))
        return order_id
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Error adding order from JSON: {str(e)}")
        return None 