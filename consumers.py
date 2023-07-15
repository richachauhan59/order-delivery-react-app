import json
from fastapi import HTTPException


def create_delivery(state, event):
    data = json.loads(event.data)
    return {
        "id" : event.delivery_id,
        "budget" : int(data["budget"]),
        "notes" : data["notes"],
        "status" : "ready"
    }

def start_delivery(state, event):
    if state['status'] != 'ready':
        raise HTTPException(status_code=400, detail = "Delivery already started")

    return state | {
        "status" : "active"
    }

def pickup_products(state, event):
    data = json.loads(event.data)
    
    purchase_price = data.get('purchase_price')
    if purchase_price is None:
        raise HTTPException(status_code=400, detail="Missing 'purchase_price' in input data")

    quantity = data.get('quantity')
    if quantity is None:
        raise HTTPException(status_code=400, detail="Missing 'quantity' in input data")

    new_budget = state["budget"] - int(purchase_price) * int(quantity)

    if new_budget < 0:
        raise HTTPException(status_code=400, detail="Not enough budget")

    return state | {
        "budget": new_budget,
        "purchase_price": int(purchase_price),
        "quantity": int(quantity),
        "status": "collected"
    }


def deliver_products(state, event):
    data = json.loads(event.data)
    new_budget = state["budget"] + int(data['sell_price']) * int(data['quantity'])
    new_quantity = state["quantity"] - int(data['quantity'])

    return state | {
        "budget" : new_budget,
        "sell_price" : int(data['sell_price']),
        "quantity" : int(data['quantity']),
        "status" : "completed"
    }


CONSUMERS = {
    "CREATE_DELIVERY" : create_delivery,
    "START_DELIVERY" : start_delivery,
    "PICKUP_PRODUCTS" : pickup_products,
    "DELIVER_PRODUCTS" : deliver_products
}