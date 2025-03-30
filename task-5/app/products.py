import uuid
from typing import Dict, List

from db_connection import session

def insert_product(category: str, name: str, price: float, manufacturer: str, properties: Dict[str, str]):
    """Insert a new product"""
    product_id = uuid.uuid4()
    session.execute("""
        INSERT INTO items (category, id, name, price, manufacturer, properties)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (category, product_id, name, price, manufacturer, properties))
    return product_id

def get_product_by_id(category: str, product_id: uuid.UUID):
    """Get a product by its ID
    
    Handles the Cassandra primary key structure by first querying by category 
    then filtering for the specific ID.
    
    Args:
        category: The product category
        product_id: The product UUID
        
    Returns:
        The product row or None if not found
    """
    result = session.execute("""
        SELECT * FROM items
        WHERE category = %s
    """, (category,))
    
    for row in result:
        if row.id == product_id:
            return row
    
    return None

def get_products_by_category(category: str):
    """Get all products in a category sorted by price"""
    result = session.execute("""
        SELECT * FROM items
        WHERE category = %s
        ORDER BY price
    """, (category,))
    return list(result)

def get_products_by_name(category: str, name: str):
    """Get products by name in a category"""
    result = session.execute("""
        SELECT * FROM items_by_name
        WHERE category = %s AND name = %s
        ORDER BY price
    """, (category, name))
    return list(result)

def get_products_by_price_range(category: str, min_price: float, max_price: float):
    """Get products by price range in a category"""
    result = session.execute("""
        SELECT * FROM items
        WHERE category = %s AND price >= %s AND price <= %s
        ORDER BY price
    """, (category, min_price, max_price))
    return list(result)

def get_products_by_manufacturer(category: str, manufacturer: str):
    """Get products by manufacturer in a category"""
    result = session.execute("""
        SELECT * FROM items_by_manufacturer
        WHERE category = %s AND manufacturer = %s
        ORDER BY price
    """, (category, manufacturer))
    return list(result)

def get_products_by_property_exists(category: str, property_name: str):
    """Get products in a category that have a specific property"""
    result = session.execute("""
        SELECT * FROM items
        WHERE category = %s
    """, (category,))
    
    # Filter in Python for properties that contain the key
    return [row for row in result if row.properties and property_name in row.properties]

def get_products_by_property_value(category: str, property_name: str, property_value: str):
    """Get products in a category with a specific property value"""
    result = session.execute("""
        SELECT * FROM items
        WHERE category = %s
    """, (category,))
    
    # Filter in Python for properties matching the key and value
    return [row for row in result if row.properties and 
            property_name in row.properties and 
            row.properties[property_name] == property_value]

def add_product_property(category: str, product_id: uuid.UUID, property_name: str, property_value: str):
    """Add a new property to a product"""
    product = get_product_by_id(category, product_id)
    
    if not product:
        return False
    
    current_properties = product.properties if product.properties else {}
    current_properties[property_name] = property_value
    
    session.execute("""
        UPDATE items
        SET properties = %s
        WHERE category = %s AND price = %s AND id = %s
    """, (current_properties, category, product.price, product_id))
    return True

def remove_product_property(category: str, product_id: uuid.UUID, property_name: str):
    """Remove a property from a product"""
    product = get_product_by_id(category, product_id)
    
    if not product or not product.properties:
        return False
    
    current_properties = product.properties
    if property_name in current_properties:
        del current_properties[property_name]
        
        session.execute("""
            UPDATE items
            SET properties = %s
            WHERE category = %s AND price = %s AND id = %s
        """, (current_properties, category, product.price, product_id))
        return True
    return False

def update_product_properties(category: str, product_id: uuid.UUID, properties: Dict[str, str]):
    """Update product properties"""
    product = get_product_by_id(category, product_id)
    
    if not product:
        return False
        
    session.execute("""
        UPDATE items
        SET properties = %s
        WHERE category = %s AND price = %s AND id = %s
    """, (properties, category, product.price, product_id))
    return True

def product_exists(category: str, name: str):
    """Check if a product exists in the database"""
    result = session.execute("""
        SELECT COUNT(*) as count FROM items
        WHERE category = %s
    """, (category,))
    
    if result.one().count == 0:
        return False
    
    result = session.execute("""
        SELECT * FROM items
        WHERE category = %s
    """, (category,))
    
    for row in result:
        if row.name == name:
            return True
    
    return False 