from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse

import db
import helper

app = FastAPI()

inprogress_orders = {}

@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()

    intent = payload["queryResult"]["intent"]["displayName"]
    parameters = payload["queryResult"]["parameters"]
    output_contexts = payload["queryResult"]["outputContexts"]

    session_id = helper.extract_session_id(output_contexts[0]['name'])

    intent_handler_dict = {
        'order.add - context: ongoing-order': add_to_order,
        'order.remove - context: ongoing-order': remove_from_order,
        'order.complete - context: ongoing-order': complete_order,
        'track.order - context: ongoing-tracking': track_order
    }

    return intent_handler_dict[intent](parameters, session_id)

def add_to_order(paramaters: dict, session_id: str):
    forge_items = paramaters["forge-item"]
    quantities = paramaters["number"]

    if len(quantities) != len(forge_items):
        fulfillment_text = "You need to specify the forge items and quantities"
    else:
        new_forge_dict = dict(zip(forge_items, quantities))

        if session_id not in inprogress_orders:
            inprogress_orders[session_id] = new_forge_dict
        else:
            current_forge_dict = inprogress_orders[session_id]
            current_forge_dict.update(new_forge_dict)
            inprogress_orders[session_id] = current_forge_dict

        order_str = helper.get_str_from_forge_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
    })

def remove_from_order(paramaters: dict, session_id: str):
    fulfillment_text = ""
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I didn't find your order on my workbench. You need to place it again."
        })
    else:
        current_order = inprogress_orders[session_id]
        forge_items = paramaters["forge-item"]

        removed_items = []
        no_such_items = []

        for item in forge_items:
            if item not in current_order:
                no_such_items.append(item)
            else:
                removed_items.append(item)
                del current_order[item]
        if len(removed_items) > 0:
            fulfillment_text = f'Removed {", ".join(removed_items)} from your order.'

        if len(no_such_items) > 0:
            fulfillment_text = f'Your current order does not have {", ".join(no_such_items)}.'

        if len(current_order.keys()) == 0:
            fulfillment_text += f' Your order is empty!'
        else:
            order_str = helper.get_str_from_forge_dict(current_order)
            fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def complete_order(paramaters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = "I didn't find your order on my workbench. You need to place it again."
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)
        if order_id == -1:
            fulfillment_text = f"I couldn't process your order. Do it again"
        else:
            order_total = db.get_total_order_price(order_id)
            fulfillment_text = f"Gods be praised! I have placed your order. " \
                               f"Her is your order id: {order_id}. " \
                               f"Your order total is {order_total} which you can play at the time of delivery."

        del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
    })

def save_to_db(order: dict):
    next_order_id = db.get_next_order_id()

    for forge_item, quantity in order.items():
        rcode = db.insert_order_item(
            forge_item,
            quantity,
            next_order_id
        )
        if rcode == -1:
            return -1

    db.insert_order_tracking(next_order_id, "in progress")

    return next_order_id


def track_order(paramaters: dict, session_id: str):
    order_id = int(paramaters["order_id"])

    order_status = db.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text,
    })