import json
import boto3
import os

# AWS Clients
sqs = boto3.client("sqs")

# Environment Variables
SQS_QUEUES = {
    "received": os.getenv("SQS_RECEIVED"),
    "in_progress": os.getenv("SQS_IN_PROGRESS"),
    "completed": os.getenv("SQS_COMPLETED"),
    "canceled": os.getenv("SQS_CANCELED"),
}

def lambda_handler(event, context):
    """
    Processes DynamoDB Stream events and sends work orders to the correct SQS queue.
    """
    try:
        for record in event["Records"]:
            if record["eventName"] in ["INSERT", "MODIFY"]:
                new_image = record["dynamodb"]["NewImage"]
                work_order = convert_dynamodb_item(new_image)

                # Send to SQS based on status
                send_to_sqs(work_order)

        return {"statusCode": 200, "body": "Processed successfully"}

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}

def send_to_sqs(work_order):
    """
    Sends a work order message to the correct SQS FIFO queue.
    """
    try:
        queue_url = SQS_QUEUES.get(work_order["status"])
        if not queue_url:
            raise ValueError(f"No queue configured for status: {work_order['status']}")

        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(work_order),
            MessageGroupId=work_order["status"],
            MessageDeduplicationId=work_order["id"]
        )
    except Exception as e:
        print(f"Error sending to SQS: {e}")

def convert_dynamodb_item(item):
    """
    Converts DynamoDB format to a normal Python dictionary.
    """
    return {key: list(value.values())[0] for key, value in item.items()}
