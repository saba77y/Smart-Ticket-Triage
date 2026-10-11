import json, os, uuid, boto3
from datetime import datetime, timezone

sqs = boto3.client("sqs")
table = boto3.resource("dynamodb").Table(os.environ.get("TABLE_NAME", "Tickets"))
QUEUE_URL = os.environ.get("QUEUE_URL", "")

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}

def reply(code, body):
    return {"statusCode": code, "headers": CORS, "body": json.dumps(body, default=str)}

def lambda_handler(event, context):
    try:
        try:
            data = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return reply(400, {"error": "Invalid JSON"})

        text = (data.get("text") or "").strip() if isinstance(data, dict) else ""
        if not text:
            return reply(400, {"error": "Ticket text is required"})
        if len(text) > 2000:
            return reply(400, {"error": "Ticket is too long (max 2000 characters)"})

        ticket_id = str(uuid.uuid4())
        table.put_item(Item={
            "ticketId": ticket_id,
            "text": text,
            "status": "PENDING",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        })
        if QUEUE_URL:
            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps({"ticketId": ticket_id, "text": text}),
            )
        return reply(202, {"ticketId": ticket_id, "status": "PENDING"})

    except Exception as e:
        print("ERROR:", e)
        return reply(500, {"error": "Something went wrong"})
