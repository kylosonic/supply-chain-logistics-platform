import random
import time
from datetime import datetime, timezone

from locust import HttpUser, task, between

class WebhookLoadTestUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def post_iot_telemetry(self):
        # We simulate IoT webhooks for cold chain temperature tracking
        sku = f"SKU-{random.randint(1000, 9999)}"
        payload = {
            "sku": sku,
            "temperature_c": round(random.uniform(-5.0, 15.0), 2),
            "humidity_percent": round(random.uniform(30.0, 90.0), 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.client.post("/api/v1/ingestion/iot-telemetry", json=payload)

    @task(1)
    def post_telematics(self):
        # We simulate telematics data points for fleet assets
        asset_id = f"VEH-{random.randint(100, 999)}"
        payload = {
            "asset_id": asset_id,
            "latitude": round(random.uniform(-90.0, 90.0), 6),
            "longitude": round(random.uniform(-180.0, 180.0), 6),
            "speed_kmh": round(random.uniform(0, 120.0), 1),
            "heading_degrees": round(random.uniform(0, 360.0), 1),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.client.post("/api/v1/ingestion/telematics", json=payload)

    def on_start(self):
        """Called when a Locust start before any task is scheduled"""
        pass
