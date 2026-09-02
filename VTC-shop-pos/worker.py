# worker.py - Isolated queue system that updates
# WooCommerce background balues every 3 seconds.
#

import time
import requests
from requests.auth import HTTPBasicAuth
from database import SessionLocal, SyncQueue

WOO_URL = "https://yourdomain.com"
CONSUMER_KEY = "ck_your_actual_key"
CONSUMER_SECRET = "cs_your_actual_secret"

def run_sync_pipeline():
    db = SessionLocal()
    try:
        job = db.query(SyncQueue).filter(SyncQueue.status.in_(["PENDING", "FAILED"]), SyncQueue.attempts < 5).order_by(SyncQueue.created_at.asc()).first()
        if not job:
            return
        
        try:
            endpoint = f"{WOO_URL}/{job.woo_product_id}"
            response = requests.put(
                endpoint, 
                json={"stock_quantity": job.new_stock_qty}, 
                auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET),
                timeout=10
            )
            if response.status_code == 200:
                job.status = "COMPLETED"
                print(f"Synced SKU to web. ID: {job.woo_product_id} | Stock: {job.new_stock_qty}")
            else:
                raise Exception(f"API Bad Code: {response.status_code}")
        except Exception as e:
            job.attempts += 1
            job.status = "FAILED"
            job.last_error = str(e)
            print(f"Error executing sync action: {str(e)}")
        
        db.commit()
    except Exception as dbe:
        print(f"Worker Loop Structural Failure: {dbe}")
    finally:
        db.close()

if __name__ == "__main__":
    print("WooCommerce Real-time Synchronization Active...")
    while True:
        run_sync_pipeline()
        time.sleep(3)
