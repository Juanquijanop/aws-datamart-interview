# AWS Datamart Interview Solutions

Este repositorio contiene múltiples soluciones serverless implementadas en AWS para el procesamiento de órdenes de trabajo. Cada solución utiliza una combinación de **API Gateway, Lambda, DynamoDB** y un mecanismo para enrutar eventos (ya sea mediante SQS directo, DynamoDB Streams, EventBridge o SNS con filtering). Todas las implementaciones se realizaron siguiendo las mejores prácticas de AWS, y en mi experiencia cada enfoque tiene sus ventajas y se adapta a distintos escenarios según los requerimientos.

---

## Soluciones Incluidas

- **Direct-to-SQS**  
  Esta solución envía órdenes de trabajo directamente a una cola SQS según el estado, garantizando el orden (FIFO).  
  [Ver documentación »](./solutions/direct-to-sqs/README.md)

- **DynamoDB Streams**  
  Utiliza DynamoDB Streams para detectar cambios en la tabla y enviar mensajes a SQS de forma asíncrona.  
  [Ver documentación »](./solutions/dynamo-streams/README.md)

- **EventBridge-SQS**  
  Publica eventos en EventBridge y los enruta a colas SQS específicas según reglas definidas.  
  [Ver documentación »](./solutions/eventbridge-sqs/README.md)

- **SNS Filtering**  
  Publica eventos en un tópico SNS y utiliza filter policies para enviar mensajes a las colas SQS correspondientes.  
  [Ver documentación »](./solutions/sns-filtering/README.md)

---

## Características Comunes

- **Serverless:** Todas las soluciones se implementan utilizando AWS Lambda y se despliegan mediante Serverless Framework, lo que me permite lograr una arquitectura completamente escalable y de bajo costo.
- **API REST:** Cada solución expone un endpoint REST para la creación y consulta de órdenes de trabajo, facilitando la integración con otras aplicaciones.
- **Validación y Almacenamiento:** Valido los datos de entrada y los almaceno en una tabla DynamoDB, asegurando la integridad de la información.
- **Procesamiento Asíncrono:** Utilizo distintos mecanismos (SQS, Streams, EventBridge o SNS) para desacoplar el procesamiento de las órdenes, lo que me permite optimizar la respuesta y el escalado de la aplicación.

---

## Requisitos

- **AWS CLI:** Debe estar instalado y configurado con las credenciales adecuadas.
- **Perfil AWS:** Es **crucial** contar con un perfil de AWS con permisos administrativos para crear todos los recursos (API Gateway, Lambda, DynamoDB, SQS, SNS, EventBridge, etc.) y evitar problemas durante el despliegue.
- **Serverless Framework:** [Instalar globalmente](https://www.serverless.com/framework/docs/getting-started/).
- **Python 3.11** y **pip** para gestionar las dependencias.

---

## Despliegue

En mi experiencia, el proceso de despliegue es sencillo y rápido utilizando Serverless Framework. Para desplegar cualquiera de las soluciones, sigue estos pasos:

1. Navega al directorio de la solución que deseas desplegar. Por ejemplo, para la solución Direct-to-SQS:
   ```bash
   cd solutions/direct-to-sqs
    ```
## Testing

python3 -m venv venv
source venv/bin/activate   # En Linux/MacOS

pip install pytest moto boto3

python -m unittest discover -s solutions/<solution>/tests

## Opinion y Experiencia Personal

Desde mi experiencia y conocimiento, si se parte de requerimientos básicos y sin especificaciones adicionales muy particulares, la solución Direct-to-SQS es mi primera recomendación. Es sencilla, tiene baja latencia y garantiza el orden de procesamiento gracias a las colas FIFO.

Sin embargo, para escenarios que prevean una mayor escalabilidad o la necesidad de enrutar eventos a múltiples destinos de manera flexible, optaría por la solución basada en EventBridge-SQS. Su capacidad para definir reglas de enrutamiento de eventos la hace ideal para arquitecturas complejas y en crecimiento.

Cada solución se implementó aplicando las mejores prácticas de AWS, y la elección dependerá de los requerimientos específicos del proyecto y de la perspectiva de escalabilidad a futuro.
