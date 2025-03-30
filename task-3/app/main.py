#!/usr/bin/env python3
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from bson.objectid import ObjectId

def print_section(title: str) -> None:
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_result(title: str, result: Any) -> None:
    """Print the result of a MongoDB operation"""
    print(f"\n--- {title} ---")
    print(json.dumps(result, indent=2, default=str))
    print()

mongo_username: str = os.environ.get("MONGO_USERNAME", "root")
mongo_password: str = os.environ.get("MONGO_PASSWORD", "example")
mongo_host: str = os.environ.get("MONGO_HOST", "localhost")
mongo_port: str = os.environ.get("MONGO_PORT", "27017")
mongo_database: str = os.environ.get("MONGO_DATABASE", "online_store")
mongo_auth_database: str = os.environ.get("MONGO_AUTH_DATABASE", "admin")

mongo_uri: str = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_database}?authSource={mongo_auth_database}"

client: MongoClient = MongoClient(mongo_uri)
db: Database = client[mongo_database]

def create_products() -> List[ObjectId]:
    """Create products with different sets of properties"""
    print_section("CREATING PRODUCTS")
    
    db.products.drop()
    
    phones: List[Dict[str, Any]] = [
        {
            "category": "Phone",
            "model": "iPhone 14 Pro",
            "producer": "Apple",
            "price": 999,
            "storage": "256GB",
            "color": "Space Black",
            "in_stock": True
        },
        {
            "category": "Phone",
            "model": "Galaxy S23",
            "producer": "Samsung",
            "price": 799,
            "storage": "128GB",
            "color": "Phantom Black",
            "in_stock": True
        },
        {
            "category": "Phone",
            "model": "Pixel 7",
            "producer": "Google",
            "price": 599,
            "storage": "128GB",
            "color": "Snow",
            "in_stock": False
        }
    ]
    
    tvs: List[Dict[str, Any]] = [
        {
            "category": "TV",
            "model": "OLED C2",
            "producer": "LG",
            "price": 1499,
            "size": "65 inch",
            "resolution": "4K",
            "smart": True
        },
        {
            "category": "TV",
            "model": "Q90T",
            "producer": "Samsung",
            "price": 1299,
            "size": "55 inch",
            "resolution": "4K",
            "smart": True
        }
    ]
    
    smart_watches: List[Dict[str, Any]] = [
        {
            "category": "Smart Watch",
            "model": "Apple Watch Series 8",
            "producer": "Apple",
            "price": 399,
            "size": "45mm",
            "color": "Silver",
            "water_resistant": True
        },
        {
            "category": "Smart Watch",
            "model": "Galaxy Watch 5",
            "producer": "Samsung",
            "price": 279,
            "size": "40mm",
            "color": "Black",
            "water_resistant": True
        }
    ]
    
    laptops: List[Dict[str, Any]] = [
        {
            "category": "Laptop",
            "model": "MacBook Pro",
            "producer": "Apple",
            "price": 1999,
            "screen_size": "16 inch",
            "processor": "M2 Pro",
            "ram": "16GB"
        },
        {
            "category": "Laptop",
            "model": "XPS 13",
            "producer": "Dell",
            "price": 1299,
            "screen_size": "13 inch",
            "processor": "Intel i7",
            "ram": "16GB"
        }
    ]
    
    all_products: List[Dict[str, Any]] = phones + tvs + smart_watches + laptops
    result = db.products.insert_many(all_products)
    
    print(f"Inserted {len(result.inserted_ids)} products")
    return result.inserted_ids

def query_products() -> None:
    """Perform various product queries"""
    print_section("QUERYING PRODUCTS")
    
    print_result("All Products", list(db.products.find({}, {"_id": 1, "category": 1, "model": 1, "producer": 1, "price": 1})))
    
    phone_count: int = db.products.count_documents({"category": "Phone"})
    print_result("Number of Phone products", {"count": phone_count})
    
    categories: List[str] = db.products.distinct("category")
    print_result("Distinct Categories", {"categories": categories, "count": len(categories)})
    
    manufacturers: List[str] = db.products.distinct("producer")
    print_result("Unique Manufacturers", {"manufacturers": manufacturers})
    
    category_and_price: List[Dict[str, Any]] = list(db.products.find({
        "$and": [
            {"category": "Phone"},
            {"price": {"$gte": 700, "$lte": 1000}}
        ]
    }))
    print_result("Phones with price between $700 and $1000", category_and_price)
    
    or_query: List[Dict[str, Any]] = list(db.products.find({
        "$or": [
            {"producer": "Apple"},
            {"price": {"$lt": 300}}
        ]
    }))
    print_result("Products made by Apple OR less than $300", or_query)
    
    in_query: List[Dict[str, Any]] = list(db.products.find({
        "producer": {"$in": ["Apple", "Samsung"]}
    }))
    print_result("Products made by Apple or Samsung", in_query)

def update_products() -> None:
    """Update products"""
    print_section("UPDATING PRODUCTS")
    
    update_price = db.products.update_one(
        {"model": "iPhone 14 Pro"},
        {"$set": {"price": 1099}}
    )
    print_result("Updated iPhone 14 Pro price", {"matched": update_price.matched_count, "modified": update_price.modified_count})
    
    add_property = db.products.update_many(
        {"category": "Phone"},
        {"$set": {"warranty_years": 2}}
    )
    print_result("Added warranty to all phones", {"matched": add_property.matched_count, "modified": add_property.modified_count})
    
    has_property: List[Dict[str, Any]] = list(db.products.find({"water_resistant": {"$exists": True}}))
    print_result("Products with water_resistant property", has_property)
    
    increase_price = db.products.update_many(
        {"water_resistant": True},
        {"$inc": {"price": 50}}
    )
    print_result("Increased price of water-resistant products", {"matched": increase_price.matched_count, "modified": increase_price.modified_count})
    
    updated_products: List[Dict[str, Any]] = list(db.products.find({
        "$or": [
            {"model": "iPhone 14 Pro"}, 
            {"water_resistant": True}
        ]
    }))
    print_result("Updated Products", updated_products)

def create_orders(product_ids: List[ObjectId]) -> List[ObjectId]:
    """Create orders with products"""
    print_section("CREATING ORDERS")
    
    db.orders.drop()
    
    customers: List[Dict[str, Any]] = [
        {
            "name": "Andrii",
            "surname": "Rodionov",
            "phones": [9876543, 1234567],
            "address": "PTI, Peremohy 37, Kyiv, UA"
        },
        {
            "name": "Maria",
            "surname": "Johnson",
            "phones": [5556789],
            "address": "123 Main St, New York, US"
        },
        {
            "name": "John",
            "surname": "Smith",
            "phones": [4447890, 1112233],
            "address": "45 Oxford Road, London, UK"
        }
    ]
    
    payments: List[Dict[str, Any]] = [
        {
            "card_owner": "Andrii Rodionov",
            "cardId": 12345678
        },
        {
            "card_owner": "Maria Johnson",
            "cardId": 55556666
        },
        {
            "card_owner": "John Smith",
            "cardId": 98765432
        }
    ]
    
    orders: List[Dict[str, Any]] = [
        {
            "order_number": 201513,
            "date": datetime.now(),
            "total_sum": 1398,
            "customer": customers[0],
            "payment": payments[0],
            "items_id": [str(product_ids[0]), str(product_ids[6])]  # iPhone 14 Pro and Apple Watch
        },
        {
            "order_number": 201514,
            "date": datetime(2025, 2, 15),
            "total_sum": 2298,
            "customer": customers[1],
            "payment": payments[1],
            "items_id": [str(product_ids[1]), str(product_ids[3])]  # Galaxy S23 and LG OLED
        },
        {
            "order_number": 201515,
            "date": datetime(2025, 3, 25),
            "total_sum": 878,
            "customer": customers[2],
            "payment": payments[2],
            "items_id": [str(product_ids[2]), str(product_ids[6])]  # Pixel 7 and Apple Watch
        },
        {
            "order_number": 201516,
            "date": datetime(2025, 4, 1),
            "total_sum": 2999,
            "customer": customers[0],
            "payment": payments[0],
            "items_id": [str(product_ids[0]), str(product_ids[7])]  # iPhone 14 Pro and MacBook Pro
        }
    ]
    
    result = db.orders.insert_many(orders)
    print(f"Created {len(result.inserted_ids)} orders")
    return result.inserted_ids

def query_orders() -> None:
    """Perform various order queries"""
    print_section("QUERYING ORDERS")
    
    print_result("All Orders", list(db.orders.find()))
    
    high_value_orders: List[Dict[str, Any]] = list(db.orders.find({"total_sum": {"$gt": 2000}}))
    print_result("Orders with value greater than $2000", high_value_orders)
    
    customer_orders: List[Dict[str, Any]] = list(db.orders.find({"customer.surname": "Rodionov"}))
    print_result("Orders made by Rodionov", customer_orders)
    
    iphone_id: ObjectId = db.products.find_one({"model": "iPhone 14 Pro"})["_id"]
    orders_with_product: List[Dict[str, Any]] = list(db.orders.find({"items_id": str(iphone_id)}))
    print_result("Orders containing iPhone 14 Pro", orders_with_product)
    
    first_order: Dict[str, Any] = db.orders.find_one({})
    product_count: int = len(first_order["items_id"])
    print_result("Number of products in first order", {"order_number": first_order["order_number"], "product_count": product_count})
    
    high_value_customer_info: List[Dict[str, Any]] = list(db.orders.find(
        {"total_sum": {"$gt": 2000}},
        {"customer": 1, "payment.cardId": 1, "_id": 0}
    ))
    print_result("Customer and payment info for high-value orders", high_value_customer_info)
    
    first_order = db.orders.find_one({})
    order_with_products: Dict[str, Any] = {
        "order_number": first_order["order_number"],
        "total_sum": first_order["total_sum"],
        "customer_name": f"{first_order['customer']['name']} {first_order['customer']['surname']}",
        "products": []
    }
    
    for item_id in first_order["items_id"]:
        product: Dict[str, Any] = db.products.find_one({"_id": ObjectId(item_id)})
        if product:
            order_with_products["products"].append({
                "model": product["model"],
                "producer": product["producer"],
                "price": product["price"]
            })
    
    print_result("Order with product details", order_with_products)

def update_orders() -> None:
    """Update orders"""
    print_section("UPDATING ORDERS")
    
    apple_watch_id: ObjectId = db.products.find_one({"model": "Apple Watch Series 8"})["_id"]
    pixel_id: ObjectId = db.products.find_one({"model": "Pixel 7"})["_id"]
    
    apple_watch_orders: List[Dict[str, Any]] = list(db.orders.find({"items_id": str(apple_watch_id)}))
    
    for order in apple_watch_orders:
        if str(pixel_id) not in order["items_id"]:
            pixel_price: int = db.products.find_one({"_id": pixel_id})["price"]
            db.orders.update_one(
                {"_id": order["_id"]},
                {
                    "$push": {"items_id": str(pixel_id)},
                    "$inc": {"total_sum": pixel_price}
                }
            )
    
    print_result("Updated orders that had Apple Watch", list(db.orders.find({"items_id": str(apple_watch_id)})))
    
    remove_result = db.orders.update_many(
        {
            "date": {
                "$gte": datetime(2025, 2, 1),
                "$lte": datetime(2025, 3, 31)
            },
            "items_id": str(apple_watch_id)
        },
        {
            "$pull": {"items_id": str(apple_watch_id)}
        }
    )
    
    print_result("Removed Apple Watch from orders in Feb-Mar 2025", {"matched": remove_result.matched_count, "modified": remove_result.modified_count})
    
    rename_result = db.orders.update_many(
        {},
        [
            {
                "$set": {
                    "order_name": "$customer.name"
                }
            }
        ]
    )
    
    print_result("Renamed orders to customer's first name", {"matched": rename_result.matched_count, "modified": rename_result.modified_count})
    
    updated_orders: List[Dict[str, Any]] = list(db.orders.find({}, {"order_number": 1, "order_name": 1, "items_id": 1, "_id": 0}))
    print_result("Updated Orders", updated_orders)

def create_capped_collection() -> None:
    """Create a capped collection for reviews"""
    print_section("CREATING CAPPED COLLECTION FOR REVIEWS")
    
    db.drop_collection("reviews")
    
    db.create_collection("reviews", capped=True, size=5120, max=5)
    
    reviews: List[Dict[str, Any]] = [
        {"user": "user1", "product": "iPhone 14 Pro", "rating": 5, "text": "Great phone!", "date": datetime.now()},
        {"user": "user2", "product": "Galaxy S23", "rating": 4, "text": "Good phone but battery life could be better", "date": datetime.now()},
        {"user": "user3", "product": "MacBook Pro", "rating": 5, "text": "Best laptop I've owned", "date": datetime.now()},
        {"user": "user4", "product": "OLED C2", "rating": 5, "text": "Amazing picture quality", "date": datetime.now()},
        {"user": "user5", "product": "Apple Watch Series 8", "rating": 4, "text": "Great smartwatch", "date": datetime.now()}
    ]
    
    for review in reviews:
        db.reviews.insert_one(review)
    
    print_result("Initial Reviews", list(db.reviews.find()))
    
    new_reviews: List[Dict[str, Any]] = [
        {"user": "user6", "product": "XPS 13", "rating": 4, "text": "Very portable and powerful", "date": datetime.now()},
        {"user": "user7", "product": "Pixel 7", "rating": 5, "text": "Best camera on a smartphone", "date": datetime.now()}
    ]
    
    for review in new_reviews:
        db.reviews.insert_one(review)
    
    print_result("Updated Reviews (should only have 5)", list(db.reviews.find()))

def main() -> None:
    """Main function to run all examples"""
    print("MONGODB ONLINE STORE IMPLEMENTATION")
    print("=" * 80)
    
    product_ids: List[ObjectId] = create_products()
    query_products()
    update_products()
    
    create_orders(product_ids)
    query_orders()
    update_orders()
    
    create_capped_collection()
    
    print("\nAll operations completed successfully!")

if __name__ == "__main__":
    main()