# data-generators/clickstream/generate_clickstream.py
import json
import random
import time
from datetime import datetime
from faker import Faker
from azure.eventhub import EventHubProducerClient, EventData
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

fake = Faker()

EVENT_TYPES = ["page_view","product_view","add_to_cart","remove_from_cart","checkout_start","purchase","search"]
PRODUCTS = [
    {"id": "P001", "name": "Wireless Headphones", "category": "Electronics", "price": 79.99},
    {"id": "P002", "name": "Running Shoes",        "category": "Sports",      "price": 129.99},
    {"id": "P003", "name": "Coffee Maker",         "category": "Kitchen",     "price": 49.99},
    {"id": "P004", "name": "Yoga Mat",             "category": "Sports",      "price": 29.99},
    {"id": "P005", "name": "Laptop Stand",         "category": "Electronics", "price": 39.99},
]

def generate_event():
    product = random.choice(PRODUCTS)
    event_type = random.choice(EVENT_TYPES)
    return {
        "event_id":        str(fake.uuid4()),
        "event_type":      event_type,
        "event_timestamp": datetime.utcnow().isoformat() + "Z",
        "session_id":      str(fake.uuid4()),
        "user_id":         f"U{random.randint(1000, 9999)}",
        "anonymous_id":    str(fake.uuid4()),
        "page_url":        fake.url(),
        "referrer_url":    fake.url(),
        "device_type":     random.choice(["desktop", "mobile", "tablet"]),
        "browser":         random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
        "os":              random.choice(["Windows", "MacOS", "iOS", "Android"]),
        "country":         fake.country_code(),
        "city":            fake.city(),
        "product_id":      product["id"] if event_type != "page_view" else None,
        "product_name":    product["name"] if event_type != "page_view" else None,
        "product_category":product["category"] if event_type != "page_view" else None,
        "product_price":   product["price"] if event_type != "page_view" else None,
        "quantity":        random.randint(1, 5) if event_type in ["add_to_cart", "purchase"] else None,
        "search_query":    fake.word() if event_type == "search" else None,
        "revenue":         round(product["price"] * random.randint(1, 3), 2) if event_type == "purchase" else None,
    }

def get_connection_string():
    credential = DefaultAzureCredential()
    client = SecretClient(
        vault_url="https://kv-databrksanlytc-dev.vault.azure.net/",
        credential=credential
    )
    return client.get_secret("eventhub-producer-connection-string").value

def send_events(batch_size=10, interval_seconds=2):
    conn_str = get_connection_string()
    producer = EventHubProducerClient.from_connection_string(
        conn_str=conn_str,
        eventhub_name="clickstream-events"
    )
    print(f"Starting clickstream generator — {batch_size} events every {interval_seconds}s")
    with producer:
        while True:
            batch = producer.create_batch()
            for _ in range(batch_size):
                event = generate_event()
                batch.add(EventData(json.dumps(event)))
            producer.send_batch(batch)
            print(f"[{datetime.utcnow().isoformat()}] Sent {batch_size} events")
            time.sleep(interval_seconds)

if __name__ == "__main__":
    send_events()