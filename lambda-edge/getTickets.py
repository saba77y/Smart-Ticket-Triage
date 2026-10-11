import json, os, boto3

table = boto3.resource("dynamodb").Table(os.environ.get("TABLE_NAME", "Tickets"))

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}

def reply(code, body):
    return {"statusCode": code, "headers": CORS, "body": json.dumps(body, default=str)}

def lambda_handler(event, context):
    try:
        ticket_id = (event.get("pathParameters") or {}).get("id")
        if ticket_id:
            item = table.get_item(Key={"ticketId": ticket_id}).get("Item")
            if not item:
                return reply(404, {"error": "Ticket not found"})
            return reply(200, item)

        items = table.scan(Limit=100).get("Items", [])
        order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        items.sort(key=lambda i: i.get("createdAt", ""), reverse=True)   # newest first
        items.sort(key=lambda i: order.get(str(i.get("urgency", "")).upper(), 3))  # then by urgency
        return reply(200, {"tickets": items})

    except Exception as e:
        print("ERROR:", e)
        return reply(500, {"error": "Something went wrong"})
