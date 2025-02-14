import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# Configuramos las variables de entorno necesarias para los tests
os.environ["DYNAMODB_TABLE"] = "TestTable"
os.environ["SNS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123456789012:TestTopic"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Agregamos la carpeta 'src' al PYTHONPATH para poder importar el módulo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import api_handler  # Asegúrate de que el archivo se llame api_handler.py

# Actualizamos las variables globales del módulo según las variables de entorno
api_handler.TABLE_NAME = os.environ["DYNAMODB_TABLE"]
api_handler.SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

class TestSNSHandler(unittest.TestCase):

    @patch("api_handler.sns")
    @patch("api_handler.dynamodb")
    def test_create_work_order_valid(self, mock_dynamodb, mock_sns):
        # Simulamos la tabla DynamoDB
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Simulamos la respuesta de SNS
        mock_sns.publish.return_value = {"MessageId": "test-message-id"}

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
        # Verificamos que se haya llamado a DynamoDB y SNS
        mock_table.put_item.assert_called_once()
        mock_sns.publish.assert_called_once()

    @patch("api_handler.sns")
    @patch("api_handler.dynamodb")
    def test_create_work_order_missing_fields(self, mock_dynamodb, mock_sns):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Falta deliveryDate y status"
            })
        }
        context = {}
        response = api_handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("Missing required fields", body["message"])

    def test_create_work_order_invalid_date(self):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Fecha inválida",
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
                "description": "Estado inválido",
                "deliveryDate": "2025-02-14T12:00:00Z",
                "status": "unknown"
            })
        }
        context = {}
        response = api_handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("Invalid status", body["message"])

    @patch("api_handler.sns")
    @patch("api_handler.dynamodb")
    def test_create_work_order_canceled_without_reason(self, mock_dynamodb, mock_sns):
        event = {
            "httpMethod": "POST",
            "body": json.dumps({
                "description": "Orden cancelada sin razón",
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
        # Simulamos la respuesta de scan en DynamoDB
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
