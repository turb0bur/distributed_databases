import uuid
from typing import Dict

from db_connection import session
from products import insert_product, product_exists, get_product_by_id
from orders import create_order, get_customer_orders

def seed_database():
    """Create sample products and orders for demo purposes"""
    print("\nCreating sample products...")
    
    # Dictionary to store product IDs by category
    product_ids = {}
    
    # Electronics products
    product_ids["Electronics"] = {}
    
    # Check if products exist before creating
    if not product_exists("Electronics", "iPhone 14 Pro"):
        phone_id = insert_product(
            category="Electronics",
            name="iPhone 14 Pro",
            price=999.99,
            manufacturer="Apple",
            properties={"storage": "256GB", "color": "Space Black", "screen": "6.7 inch"}
        )
    else:
        # Get existing product ID
        result = session.execute("""
            SELECT * FROM items
            WHERE category = %s
        """, ("Electronics",))
        
        for row in result:
            if row.name == "iPhone 14 Pro":
                phone_id = row.id
                print(f"Using existing iPhone 14 Pro with ID: {phone_id}")
                break
    
    if not product_exists("Electronics", "MacBook Pro"):
        laptop_id = insert_product(
            category="Electronics",
            name="MacBook Pro",
            price=1299.99,
            manufacturer="Apple",
            properties={"storage": "512GB", "color": "Silver", "screen": "14 inch"}
        )
    else:
        # Get existing product ID
        result = session.execute("""
            SELECT * FROM items
            WHERE category = %s
        """, ("Electronics",))
        
        for row in result:
            if row.name == "MacBook Pro":
                laptop_id = row.id
                print(f"Using existing MacBook Pro with ID: {laptop_id}")
                break
    
    # Add additional electronics products
    product_ids["Electronics"]["phone_id"] = phone_id
    product_ids["Electronics"]["laptop_id"] = laptop_id
    
    # Add Samsung TV
    tv_id = insert_product(
        category="Electronics",
        name="QLED 4K Smart TV",
        price=899.99,
        manufacturer="Samsung",
        properties={"size": "55 inch", "resolution": "4K", "refresh_rate": "120Hz"}
    )
    product_ids["Electronics"]["tv_id"] = tv_id
    
    # Add gaming console
    console_id = insert_product(
        category="Electronics",
        name="PlayStation 5",
        price=499.99,
        manufacturer="Sony",
        properties={"storage": "825GB", "color": "White", "disc_drive": "Yes"}
    )
    product_ids["Electronics"]["console_id"] = console_id
    
    # Add headphones
    headphones_id = insert_product(
        category="Electronics",
        name="AirPods Pro",
        price=249.99,
        manufacturer="Apple",
        properties={"type": "In-ear", "noise_cancellation": "Yes", "water_resistant": "Yes"}
    )
    product_ids["Electronics"]["headphones_id"] = headphones_id
    
    # Books category
    product_ids["Books"] = {}
    
    # Fiction book
    fiction_book_id = insert_product(
        category="Books",
        name="The Great Gatsby",
        price=12.99,
        manufacturer="Scribner",
        properties={"author": "F. Scott Fitzgerald", "format": "Paperback", "pages": "180"}
    )
    product_ids["Books"]["fiction_book_id"] = fiction_book_id
    
    # Non-fiction book
    nonfiction_book_id = insert_product(
        category="Books",
        name="Sapiens: A Brief History of Humankind",
        price=18.99,
        manufacturer="Harper",
        properties={"author": "Yuval Noah Harari", "format": "Hardcover", "pages": "464"}
    )
    product_ids["Books"]["nonfiction_book_id"] = nonfiction_book_id
    
    # Technical book
    tech_book_id = insert_product(
        category="Books",
        name="Clean Code",
        price=32.99,
        manufacturer="Prentice Hall",
        properties={"author": "Robert C. Martin", "format": "Paperback", "pages": "464", "topic": "Programming"}
    )
    product_ids["Books"]["tech_book_id"] = tech_book_id
    
    # Clothing category
    product_ids["Clothing"] = {}
    
    # T-shirt
    tshirt_id = insert_product(
        category="Clothing",
        name="Cotton T-Shirt",
        price=19.99,
        manufacturer="Nike",
        properties={"size": "L", "color": "Black", "material": "100% Cotton"}
    )
    product_ids["Clothing"]["tshirt_id"] = tshirt_id
    
    # Jeans
    jeans_id = insert_product(
        category="Clothing",
        name="Slim Fit Jeans",
        price=49.99,
        manufacturer="Levi's",
        properties={"size": "32x34", "color": "Blue", "material": "Denim", "style": "Slim"}
    )
    product_ids["Clothing"]["jeans_id"] = jeans_id
    
    # Jacket
    jacket_id = insert_product(
        category="Clothing",
        name="Puffer Jacket",
        price=89.99,
        manufacturer="Columbia",
        properties={"size": "M", "color": "Navy", "material": "Polyester", "waterproof": "Yes"}
    )
    product_ids["Clothing"]["jacket_id"] = jacket_id
    
    # Create some sample orders
    print("\nCreating sample orders...")
    
    # Check if John Doe has any orders
    existing_orders = get_customer_orders("John Doe")
    if not existing_orders:
        order_id = create_order(
            customer_name="John Doe",
            products=[phone_id, laptop_id],
            total_value=2299.98
        )
        print(f"Created new order for John Doe with ID: {order_id}")
    else:
        # Use the first existing order
        order_id = existing_orders[0].order_id
        print(f"Using existing order for John Doe with ID: {order_id}")
    
    # Add more orders with different product mixes
    # Order with clothing items
    clothing_order_id = create_order(
        customer_name="John Doe",
        products=[tshirt_id, jeans_id],
        total_value=69.98
    )
    
    # Order with books
    books_order_id = create_order(
        customer_name="John Doe",
        products=[fiction_book_id, nonfiction_book_id, tech_book_id],
        total_value=64.97
    )
    
    # Order with a mix of categories
    mixed_order_id = create_order(
        customer_name="John Doe",
        products=[console_id, headphones_id, tech_book_id],
        total_value=782.97
    )
    
    # Check if Jane Smith has any orders
    existing_orders = get_customer_orders("Jane Smith")
    if not existing_orders:
        # Create an order with TTL
        ttl_order_id = create_order(
            customer_name="Jane Smith",
            products=[phone_id],
            total_value=999.99,
            ttl=3600  # 1 hour TTL
        )
        print(f"Created new order with TTL for Jane Smith with ID: {ttl_order_id}")
    else:
        # Use the first existing order
        ttl_order_id = existing_orders[0].order_id
        print(f"Using existing order for Jane Smith with ID: {ttl_order_id}")
    
    # Create an order for another customer
    create_order(
        customer_name="Bob Johnson",
        products=[tv_id, console_id],
        total_value=1399.98
    )
    
    return {
        "product_ids": product_ids, 
        "order_id": order_id
    } 