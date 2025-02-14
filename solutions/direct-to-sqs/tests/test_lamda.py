import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Configuramos las variables de entorno necesarias para los tests
os.environ["DYNAMODB_TABLE"] = "TestTable"
os.environ["SQS_RECEIVED"] = "https://sqs.us-east-1.amazonaws.com/123456789012/work-orders-received.fifo"
os.environ["SQS_IN_PROGRESS"] = "https://sqs.us-east-1.amazonaws.com/123456789012/work-orders-in-progress.fifo"
os.environ["SQS_COMPLETED"] = "https://sqs.us-east-1.amazonaws.com/123456789012/work-orders-completed.fifo"
os.environ["SQS_CANCELED"] = "https://sqs.us-east-1.amazonaws.com/123456789012/work-orders-canceled.fifo"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Agregamos al sys.path la carpeta 'src' para poder importar el módulo handler
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Importamos el módulo completo
import handler

# Actualizamos las variables globales del módulo con las de entorno
handler.TABLE_NAME = os.environ["DYNAMODB_TABLE"]
handler.SQS_QUEUES = {
    "received": os.environ["SQS_RECEIVED"],
    "in_progress": os.environ["SQS_IN_PROGRESS"],
    "completed": os.environ["SQS_COMPLETED"],
    "canceled": os.environ["SQS_CANCELED"],
}

class TestLambdaHandler(unittest.TestCase):
    @patch("handler.dynamodb")
    @patch("handler.sqs")
    def test_create_work_order_valid_received(self, mock_sqs, mock_dynamodb):
        # Creamos un objeto simulado para la tabla DynamoDB
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Simulamos respuesta de SQS
        mock_sqs.send_message.return_value = {"MessageId": "test-message-id"}

        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Test work order",
                "deliveryDate": "2025-02-14T12:00:00Z",
                "status": "received"
            })
        }
        context = {}
        response = handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 201)
        body = json.loads(response["body"])
        self.assertIn("data", body)
        # Verificamos que se haya llamado a DynamoDB y SQS
        mock_table.put_item.assert_called_once()
        mock_sqs.send_message.assert_called_once()

    @patch("handler.dynamodb")
    @patch("handler.sqs")
    def test_create_work_order_missing_fields(self, mock_sqs, mock_dynamodb):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Falta deliveryDate y status"
            })
        }
        context = {}
        response = handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertEqual(body["message"], "Missing required fields.")

    def test_create_work_order_invalid_date(self):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Test work order",
                "deliveryDate": "2025-02-14",  # Formato incorrecto
                "status": "received"
            })
        }
        context = {}
        response = handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("Invalid date format", body["message"])

    def test_create_work_order_invalid_status(self):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Test work order",
                "deliveryDate": "2025-02-14T12:00:00Z",
                "status": "unknown"
            })
        }
        context = {}
        response = handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("Invalid status", body["message"])

    @patch("handler.dynamodb")
    @patch("handler.sqs")
    def test_create_work_order_canceled_without_reason(self, mock_sqs, mock_dynamodb):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Orden cancelada sin razón",
                "deliveryDate": "2025-02-14T12:00:00Z",
                "status": "canceled"
            })
        }
        context = {}
        response = handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("Cancellation reason is required", body["message"])

    @patch("handler.dynamodb")
    def test_list_work_orders(self, mock_dynamodb):
        # Simulamos la respuesta de scan en DynamoDB
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.scan.return_value = {"Items": [{"id": "1"}], "Count": 1}

        event = {
            "httpMethod": "GET"
        }
        context = {}
        response = handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["data"]["total"], 1)
        self.assertEqual(body["data"]["items"][0]["id"], "1")

if __name__ == "__main__":
    unittest.main()
