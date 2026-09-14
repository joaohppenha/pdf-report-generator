import sqlite3
import random
from datetime import datetime, timedelta

def seed_database():
    conn = sqlite3.connect("report.db")
    cursor = conn.cursor()

    # Create table for Stage 1 dataset
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Ensure idempotency by wiping previous records before re-populating
    cursor.execute("DELETE FROM orders")

    # Seed data mocks
    products = ["SaaS Subscription", "API Credits", "Consulting Hour", "Data Export Plugin", "Enterprise SLA"]
    customers = [f"Customer {i}" for i in range(1, 30)]

    orders = []
    now = datetime.now()

    for _ in range(200):
        customer = random.choice(customers)
        product = random.choice(products)
        amount = round(random.uniform(15.0, 350.0), 2)
        random_days = random.randint(0, 30)
        created_at = (now - timedelta(days=random_days)).strftime("%Y-%m-%d %H:%M:%S")
        
        orders.append((customer, product, amount, created_at))

    cursor.executemany("""
        INSERT INTO orders (customer, product, amount, created_at)
        VALUES (?, ?, ?, ?)
    """, orders)

    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    print(f"Checkpoint Stage 1: {count} records seeded into report.db successfully!")
    
    conn.close()

if __name__ == "__main__":
    seed_database()