import uuid
from datetime import datetime

from db_connection import setup_database, cleanup_database, describe_table
from products import (
    get_product_by_id, get_products_by_category, get_products_by_name,
    get_products_by_manufacturer, get_products_by_property_value,
    add_product_property, remove_product_property, get_products_by_property_exists,
    get_products_by_price_range, product_exists, update_product_properties
)
from orders import (
    get_customer_orders, get_customer_total_spent, get_customer_max_order,
    get_order_writetime, get_order_as_json, get_customer_orders_with_product,
    get_customer_orders_by_date_range, create_order, update_order,
    add_order_from_json, get_order_by_id
)
from seed_data import seed_database

def demonstrate_queries(product_ids, order_id):
    """Run demonstration queries to show functionality"""
    print("\nDemonstrating queries...")
    
    print("\n1. Tables structure:")
    describe_table("items")
    describe_table("orders")
    
    print("\n2. Products in Electronics category:")
    for product in get_products_by_category("Electronics"):
        print(f"- {product.name}: ${product.price}")
    
    print("\n3. Products in Books category:")
    for product in get_products_by_category("Books"):
        print(f"- {product.name}: ${product.price}")
    
    print("\n4. Products in Clothing category:")
    for product in get_products_by_category("Clothing"):
        print(f"- {product.name}: ${product.price}")
    
    print("\n5. Products by manufacturer (Apple):")
    for product in get_products_by_manufacturer("Electronics", "Apple"):
        print(f"- {product.name}: ${product.price}")
    
    print("\n6. Books by author Yuval Noah Harari:")
    for product in get_products_by_property_value("Books", "author", "Yuval Noah Harari"):
        print(f"- {product.name}: ${product.price}")
    
    print("\n7. Waterproof clothing items:")
    for product in get_products_by_property_value("Clothing", "waterproof", "Yes"):
        print(f"- {product.name}: ${product.price}")
    
    print("\n8. Customer orders for John Doe:")
    for order in get_customer_orders("John Doe"):
        print(f"- Order {order.order_id}: ${order.total_value}")
    
    print("\n9. Customer total spent by John Doe:")
    print(f"Total spent by John Doe: ${get_customer_total_spent('John Doe')}")
    
    print("\n10. Customer max order for John Doe:")
    max_order = get_customer_max_order("John Doe")
    if max_order:
        print(f"Max order value: ${max_order.total_value}")
    
    print("\n11. Order writetime:")
    writetime = get_order_writetime("John Doe", order_id)
    if writetime:
        print(f"Order was created at: {datetime.fromtimestamp(writetime/1000000)}")
    
    print("\n12. Order as JSON:")
    order_json = get_order_as_json("John Doe", order_id)
    print(f"- {order_json}")
    
    phone_id = product_ids["Electronics"]["phone_id"]
    
    print("\n13. Adding property to product:")
    add_product_property("Electronics", phone_id, "warranty", "2 years")
    
    # Get the product using the helper function
    phone_after = get_product_by_id("Electronics", phone_id)
    
    if phone_after:
        print(f"- {phone_after.name} now has warranty: {phone_after.properties.get('warranty')}")
    
    print("\n14. Removing property from product:")
    remove_product_property("Electronics", phone_id, "warranty")
    
    # Get the updated product using the helper function
    phone_after = get_product_by_id("Electronics", phone_id)
    
    if phone_after:
        print(f"- {phone_after.name} warranty removed: {'warranty' not in phone_after.properties}")

def main():
    """Main function demonstrating all operations"""
    print("Setting up database...")
    # Clean up before setup to ensure no duplicates
    cleanup_database(truncate_tables=True)
    setup_database()
    
    # Seed the database with sample data
    seed_data = seed_database()
    
    # Demonstrate various queries and operations
    demonstrate_queries(seed_data["product_ids"], seed_data["order_id"])

if __name__ == "__main__":
    main() 