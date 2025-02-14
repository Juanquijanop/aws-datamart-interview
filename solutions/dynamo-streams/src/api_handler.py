import json
import uuid
import boto3
import datetime
import os

# AWS Clients
dynamodb = boto3.resource("dynamodb")

# Environment Variables
TABLE_NAME = os.getenv("DYNAMODB_TABLE")
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
    Validates input and stores data in DynamoDB.
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

def response(status_code, body):
    """
    Returns an API Gateway-compatible response.
    """
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }
