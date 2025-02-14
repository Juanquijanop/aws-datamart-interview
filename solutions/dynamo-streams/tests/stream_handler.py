import os
import sys
import json
import unittest
from unittest.mock import patch

# Configuramos las variables de entorno necesarias para SQS
os.environ["SQS_RECEIVED"] = "https://sqs.us-east-1.amazonaws.com/123456789012/work-orders-received"
os.environ["SQS_IN_PROGRESS"] = "https://sqs.us-east-1.amazonaws.com/123456789012/work-orders-in-progress"
os.environ["SQS_COMPLETED"] = "https://sqs.us-east-1.amazonaws.com/123456789012/work-orders-completed"
os.environ["SQS_CANCELED"] = "https://sqs.us-east-1.amazonaws.com/123456789012/work-orders-canceled"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Agregamos la carpeta 'src' al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import stream_handler  # asumiendo que el archivo se llama stream_handler.py

class TestStreamHandler(unittest.TestCase):

    @patch("stream_handler.sqs")
    def test_process_dynamodb_stream_insert(self, mock_sqs):
        # Preparamos un registro de evento DynamoDB con evento INSERT
        fake_record = {
            "eventName": "INSERT",
            "dynamodb": {
                "NewImage": {
                    "id": {"S": "1234"},
                    "description": {"S": "Test work order"},
                    "deliveryDate": {"S": "2025-02-14T12:00:00Z"},
                    "status": {"S": "received"}
                }
            }
        }
        event = {"Records": [fake_record]}
        context = {}
        response = stream_handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 200)
        # Verificamos que se haya llamado a sqs.send_message
        mock_sqs.send_message.assert_called_once()

    @patch("stream_handler.sqs")
    def test_process_dynamodb_stream_no_insert(self, mock_sqs):
        # Evento sin registros INSERT o MODIFY
        event = {"Records": [
            {"eventName": "REMOVE", "dynamodb": {"NewImage": {}}}
        ]}
        context = {}
        response = stream_handler.lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 200)
        # No se debería llamar a sqs.send_message
        mock_sqs.send_message.assert_not_called()

if __name__ == "__main__":
    unittest.main()
