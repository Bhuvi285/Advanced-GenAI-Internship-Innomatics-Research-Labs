from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# =====================================
# PRODUCTS DATABASE
# =====================================

products = [
    {"id": 1, "name": "Laptop", "price": 1000, "in_stock": True},
    {"id": 2, "name": "Mouse", "price": 25, "in_stock": True},
    {"id": 3, "name": "Keyboard", "price": 75, "in_stock": False},
    {"id": 4, "name": "Monitor", "price": 300, "in_stock": True},
]

# =====================================
# CART + ORDER DATA
# =====================================

cart = []
orders = []
order_counter = 1


# =====================================
# HELPER
# =====================================

def find_product(product_id):
    for product in products:
        if product["id"] == product_id:
            return product
    return None

def calculate_total(product, quantity):
    return product["price"] * quantity


# =====================================
# POST /cart/add
# =====================================

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):

    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(
            status_code=400,
            detail=f"{product['name']} is out of stock"
        )

    # check if product already in cart
    for item in cart:
        if item["product_id"] == product_id:

            item["quantity"] += quantity
            item["subtotal"] = calculate_total(product, item["quantity"])

            return {
                "message": "Cart updated",
                "cart_item": item
            }

    cart_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": calculate_total(product, quantity)
    }

    cart.append(cart_item)

    return {
        "message": "Added to cart",
        "cart_item": cart_item
    }


# =====================================
# GET /cart
# =====================================

@app.get("/cart")
def view_cart():

    if not cart:
        return {"message": "Cart is empty"}

    grand_total = sum(item["subtotal"] for item in cart)

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }


# =====================================
# DELETE /cart/{product_id}
# =====================================

@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):

    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": "Item removed from cart"}

    raise HTTPException(status_code=404, detail="Item not in cart")


# =====================================
# CHECKOUT MODEL
# =====================================

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


# =====================================
# POST /cart/checkout
# =====================================

@app.post("/cart/checkout")
def checkout(data: CheckoutRequest):

    global order_counter

    if not cart:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty — add items first"
        )

    orders_placed = []
    grand_total = 0

    for item in cart:

        order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "delivery_address": data.delivery_address,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "total_price": item["subtotal"]
        }

        orders.append(order)
        orders_placed.append(order)

        grand_total += item["subtotal"]
        order_counter += 1

    cart.clear()

    return {
        "message": "Checkout successful",
        "orders_placed": orders_placed,
        "grand_total": grand_total
    }


# =====================================
# GET /orders
# =====================================

@app.get("/orders")
def get_orders():

    return {
        "orders": orders,
        "total_orders": len(orders)
    }