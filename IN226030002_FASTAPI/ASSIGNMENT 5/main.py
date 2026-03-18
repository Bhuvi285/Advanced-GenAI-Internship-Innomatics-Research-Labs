from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()

# =====================================
# PRODUCTS DATABASE
# =====================================

products = [
    {"id": 1, "name": "Laptop", "price": 1000, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Mouse", "price": 25, "category": "Electronics", "in_stock": True},
    {"id": 3, "name": "Keyboard", "price": 75, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Monitor", "price": 300, "category": "Electronics", "in_stock": True},
]

# =====================================
# CART + ORDER DATA
# =====================================

cart = []
orders = []
order_counter = 1


# =====================================
# HELPER FUNCTIONS
# =====================================

def find_product(product_id):
    for product in products:
        if product["id"] == product_id:
            return product
    return None

def calculate_total(product, quantity):
    return product["price"] * quantity


# =====================================
# SEARCH PRODUCTS (Q1)
# =====================================

@app.get("/products/search")
def search_products(keyword: str = Query(...)):

    result = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    if not result:
        return {"message": f"No products found for: {keyword}"}

    return {
        "keyword": keyword,
        "total_found": len(result),
        "products": result
    }


# =====================================
# SORT PRODUCTS (Q2)
# =====================================

@app.get("/products/sort")
def sort_products(
    sort_by: str = Query("price"),
    order: str = Query("asc")
):

    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    result = sorted(
        products,
        key=lambda p: p[sort_by],
        reverse=(order == "desc")
    )

    return {
        "sort_by": sort_by,
        "order": order,
        "products": result
    }


# =====================================
# PAGINATION (Q3)
# =====================================

@app.get("/products/page")
def paginate_products(
    page: int = Query(1, ge=1),
    limit: int = Query(2, ge=1)
):

    start = (page - 1) * limit

    return {
        "page": page,
        "limit": limit,
        "total": len(products),
        "total_pages": -(-len(products) // limit),
        "products": products[start:start + limit]
    }


# =====================================
# CART APIs
# =====================================

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):

    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = calculate_total(product, item["quantity"])
            return {"message": "Cart updated", "cart_item": item}

    cart_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": calculate_total(product, quantity)
    }

    cart.append(cart_item)

    return {"message": "Added to cart", "cart_item": cart_item}


@app.get("/cart")
def view_cart():

    if not cart:
        return {"message": "Cart is empty"}

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": sum(item["subtotal"] for item in cart)
    }


@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):

    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": "Item removed from cart"}

    raise HTTPException(status_code=404, detail="Item not in cart")


# =====================================
# CHECKOUT
# =====================================

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


@app.post("/cart/checkout")
def checkout(data: CheckoutRequest):

    global order_counter

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    orders_placed = []
    total = 0

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

        total += item["subtotal"]
        order_counter += 1

    cart.clear()

    return {
        "message": "Checkout successful",
        "orders_placed": orders_placed,
        "grand_total": total
    }


# =====================================
# GET ORDERS
# =====================================

@app.get("/orders")
def get_orders():
    return {"orders": orders, "total_orders": len(orders)}


# =====================================
# Q4 — SEARCH ORDERS
# =====================================

@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):

    result = [
        o for o in orders
        if customer_name.lower() in o["customer_name"].lower()
    ]

    if not result:
        return {"message": f"No orders found for: {customer_name}"}

    return {
        "customer_name": customer_name,
        "total_found": len(result),
        "orders": result
    }


# =====================================
# Q5 — SORT BY CATEGORY + PRICE
# =====================================

@app.get("/products/sort-by-category")
def sort_by_category():

    result = sorted(products, key=lambda p: (p["category"], p["price"]))

    return {"products": result, "total": len(result)}


# =====================================
# Q6 — BROWSE (SEARCH + SORT + PAGINATION)
# =====================================

@app.get("/products/browse")
def browse_products(
    keyword: str = Query(None),
    sort_by: str = Query("price"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1)
):

    result = products

    # search
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    # sort
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))

    # paginate
    total = len(result)
    start = (page - 1) * limit

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total,
        "total_pages": -(-total // limit),
        "products": result[start:start + limit]
    }


# =====================================
# ⭐ BONUS — ORDERS PAGINATION
# =====================================

@app.get("/orders/page")
def paginate_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1)
):

    start = (page - 1) * limit

    return {
        "page": page,
        "limit": limit,
        "total": len(orders),
        "total_pages": -(-len(orders) // limit),
        "orders": orders[start:start + limit]
    }