import json

import aio_pika

from src.domain.order.entities import Order


class RabbitMQOrderPublisher:
    def __init__(self, amqp_url: str, exchange_name: str = "orders_exchange") -> None:
        self._amqp_url = amqp_url
        self._exchange_name = exchange_name

    async def publish_order_created(self, order: Order) -> None:
        connection = await aio_pika.connect_robust(self._amqp_url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                self._exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
            )
            payload = {
                "event": "order.created",
                "order_id": str(order.id),
                "user_id": str(order.user_id),
                "total_amount": str(order.total_amount),
                "items": [
                    {
                        "product_id": i.product_id,
                        "quantity": i.quantity,
                        "unit_price": str(i.unit_price),
                    }
                    for i in order.items
                ],
            }
            message = aio_pika.Message(
                body=json.dumps(payload).encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
            )
            await exchange.publish(message, routing_key="order.created")
