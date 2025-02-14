import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# Configuramos las variables de entorno necesarias
os.environ["DYNAMODB_TABLE"] = "TestTable"
os.environ["EVENT_BUS_NAME"] = "TestEventBus"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Agregamos la carpeta 'src' al PYTHONPATH para poder importar el módulo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import api_handler  # Asegúrate de que este sea el nombre del módulo que contiene el código

# Actualizamos las variables globales del módulo según las variables de entorno
api_handler.TABLE_NAME = os.environ["DYNAMODB_TABLE"]
api_handler.EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]

class TestEventBridgeHandler(unittest.TestCase):

    @patch("api_handler.eventbridge")
    @patch("api_handler.dynamodb")
    def test_create_work_order_valid(self, mock_dynamodb, mock_eventbridge):
        # Simulamos la tabla de DynamoDB
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Simulamos la respuesta de EventBridge
        mock_eventbridge.put_events.return_value = {"Entries": [{"EventId": "12345"}]}

        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Test work order",
                "deliveryDate": "2025-02-14T12:00:00Z",
                "status": "received"
            })
        }
        context = {}

        response = api_handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 201)
        body = json.loads(response["body"])
        self.assertIn("data", body)

        # Verificamos que se haya llamado a DynamoDB y a EventBridge
        mock_table.put_item.assert_called_once()
        mock_eventbridge.put_events.assert_called_once()

    @patch("api_handler.eventbridge")
    @patch("api_handler.dynamodb")
    def test_create_work_order_missing_fields(self, mock_dynamodb, mock_eventbridge):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Missing deliveryDate and status"
            })
        }
        context = {}
        response = api_handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertEqual(body["message"], "Missing required fields.")

    def test_create_work_order_invalid_date(self):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Invalid date format",
                "deliveryDate": "2025-02-14",  # Formato incorrecto
                "status": "received"
            })
        }
        context = {}
        response = api_handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("Invalid date format", body["message"])

    def test_create_work_order_invalid_status(self):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Invalid status",
                "deliveryDate": "2025-02-14T12:00:00Z",
                "status": "unknown"
            })
        }
        context = {}
        response = api_handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("Invalid status", body["message"])

    def test_create_work_order_canceled_without_reason(self):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Canceled without reason",
                "deliveryDate": "2025-02-14T12:00:00Z",
                "status": "canceled"
            })
        }
        context = {}
        response = api_handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("Cancellation reason is required", body["message"])

    @patch("api_handler.dynamodb")
    def test_list_work_orders(self, mock_dynamodb):
        # Simulamos la respuesta de scan de DynamoDB
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.scan.return_value = {"Items": [{"id": "1"}], "Count": 1}

        event = {"httpMethod": "GET"}
        context = {}
        response = api_handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["data"]["total"], 1)
        self.assertEqual(body["data"]["items"][0]["id"], "1")

if __name__ == "__main__":
    unittest.main()
