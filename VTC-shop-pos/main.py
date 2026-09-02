# main.py - The web server component. It processes 
# incoming transactions from your HTML cash 
# register layout and hosts he user interface pages.
 
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import SessionLocal, Product, SyncQueue, init_db

app = FastAPI(title="Hobby Shop POS Engine")

# Run database setup configurations on start
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CartItem(BaseModel):
    product_id: str
    quantity: int

class CheckoutRequest(BaseModel):
    items: List[CartItem]
    payment_method: str

@app.get("/api/products/scan/{barcode}")
def scan_product(barcode: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.sku == barcode).first()
    if not product:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "price": float(product.price),
        "stock_qty": product.stock_qty
    }

@app.post("/api/checkout")
def checkout(payload: CheckoutRequest, db: Session = Depends(get_db)):
    try:
        with db.begin():
            for item in payload.items:
                product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
                if not product:
                    raise HTTPException(status_code=404, detail="Product structural fault")
                if product.stock_qty < item.quantity:
                    raise HTTPException(status_code=400, detail=f"Short stock for {product.name}")
                
                # Drop stock levels locally
                product.stock_qty -= item.quantity
                
                # Route into WooCommerce sync pipeline background process
                if product.woo_product_id:
                    sync_job = SyncQueue(woo_product_id=product.woo_product_id, new_stock_qty=product.stock_qty)
                    db.add(sync_job)
                    
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def index_interface():
    # Serves cash register layout explicitly straight into browser views
    with open("index.html", "r") as file:
        return file.read()
