import json
import uuid
import boto3
import datetime
import os

# AWS Clients
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

# Environment Variables
TABLE_NAME = os.getenv("DYNAMODB_TABLE")
SQS_QUEUES = {
    "received": os.getenv("SQS_RECEIVED"),
    "in_progress": os.getenv("SQS_IN_PROGRESS"),
    "completed": os.getenv("SQS_COMPLETED"),
    "canceled": os.getenv("SQS_CANCELED"),
}

VALID_STATUSES = {"received", "in_progress", "completed", "canceled"}

def lambda_handler(event, context):
    """
    Lambda entry point. Routes requests based on HTTP method.
    """
    method = event["httpMethod"]

    if method == "POST":
        return create_work_order(event)
    elif method == "GET":
        return list_work_orders()
    else:
        return response(405, {"message": "Method Not Allowed"})

def create_work_order(event):
    """
    Handles POST requests to create a new work order.
    Validates input, stores data in DynamoDB, and sends it to the correct SQS queue.
    """
    try:
        body = json.loads(event["body"])
        
        # Validate required fields
        required_fields = ["description", "deliveryDate", "status"]
        if not all(field in body for field in required_fields):
            return response(400, {"message": "Missing required fields."})
        
        # Validate status
        if body["status"] not in VALID_STATUSES:
            return response(400, {
                "message": f"Invalid status '{body['status']}'.",
                "validStatuses": list(VALID_STATUSES)
            })

        # Validate deliveryDate format (ISO 8601)
        if not is_valid_iso8601(body["deliveryDate"]):
            return response(400, {
                "message": "Invalid date format. The 'deliveryDate' must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."
            })

        if body["status"] == "canceled" and "cancellationReason" not in body:
            return response(400, {"message": "Cancellation reason is required when status is 'canceled'."})

        # Validate status
        valid_statuses = SQS_QUEUES.keys()
        if body["status"] not in valid_statuses:
            return response(400, {"message": f"Invalid status. Must be one of {list(valid_statuses)}"})

        # Generate unique ID
        work_order_id = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow().isoformat()

        # Create work order item
        work_order = {
            "id": work_order_id,
            "createdAt": created_at,
            "description": body["description"],
            "deliveryDate": body["deliveryDate"],
            "status": body["status"],
            "cancellationReason": body.get("cancellationReason")
        }

        # Store in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item=work_order)

        # Send to the correct SQS queue
        send_to_sqs(work_order)

        return response(201, {
            "message": "Resource created successfully",
            "data": work_order
        })

    except Exception as e:
        return response(500, {"message": str(e)})

def list_work_orders():
    """
    Handles GET requests to list all work orders.
    """
    try:
        table = dynamodb.Table(TABLE_NAME)
        result = table.scan()
        
        return response(200, {
            "data": {
                "items": result.get("Items", []),
                "total": result.get("Count", 0)
            }
        })

    except Exception as e:
        return response(500, {"message": str(e)})

def is_valid_iso8601(date_str):
    """
    Validates if a string is in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ).
    """
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False

def send_to_sqs(work_order):
    """
    Sends a work order message to the correct SQS FIFO queue.
    """
    try:
        queue_url = SQS_QUEUES.get(work_order["status"])
        if not queue_url:
            raise ValueError(f"No queue configured for status: {work_order['status']}")

        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(work_order),
            MessageGroupId=work_order["status"],
            MessageDeduplicationId=work_order["id"]
        )
        return response
    except Exception as e:
        print(f"Error sending to SQS: {e}")

def response(status_code, body):
    """
    Returns an API Gateway-compatible response.
    """
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }
