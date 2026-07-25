import asyncio
import json
import logging
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from meshcore import MeshCore, EventType


SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5968021541-if00"
SERIAL_BAUD = 115200

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "meshhub/input/meshcore"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

mqtt_client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="meshhub-meshcore",
)


def json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, bytes):
        return value.hex()

    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]

    if hasattr(value, "__dict__"):
        return {
            str(k): json_safe(v)
            for k, v in vars(value).items()
            if not k.startswith("_")
        }

    return str(value)


def publish_event(kind, event):
    event_payload = json_safe(getattr(event, "payload", {}))
    event_attributes = json_safe(getattr(event, "attributes", {}))

    sender = "unknown"
    destination = "broadcast"
    payload = event_payload

    if kind == "channel_message":
        raw_text = str(event_payload.get("text", ""))
        channel_idx = event_payload.get("channel_idx")

        # MeshCore Public zpráva typicky přichází jako "Jmeno: text".
        if ": " in raw_text:
            sender, text = raw_text.split(": ", 1)
        else:
            text = raw_text

        destination = f"channel:{channel_idx}"

        payload = {
            "text": text,
            "channel_idx": channel_idx,
            "sender_timestamp": event_payload.get("sender_timestamp"),
        }

    message = {
        "source": "meshcore",
        "network": "meshcore",
        "type": kind,
        "sender": sender,
        "destination": destination,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "metadata": {
            "adapter": "meshcore",
            "serial_port": SERIAL_PORT,
            "meshcore_attributes": event_attributes,
        },
    }

    encoded = json.dumps(message, ensure_ascii=False)

    result = mqtt_client.publish(MQTT_TOPIC, encoded)

    logging.info(
        "MeshCore event %s -> MQTT rc=%s",
        kind,
        result.rc,
    )


async def on_contact_message(event):
    logging.info("CONTACT_MSG_RECV: %s", event)
    publish_event("contact_message", event)


async def on_channel_message(event):
    logging.info("CHANNEL_MSG_RECV: %s", event)
    publish_event("channel_message", event)


async def on_connected(event):
    logging.info("MeshCore CONNECTED: %s", event)


async def on_disconnected(event):
    logging.warning("MeshCore DISCONNECTED: %s", event)


async def main():
    logging.info("Spouštím MeshCore adapter")
    logging.info("Serial: %s @ %s", SERIAL_PORT, SERIAL_BAUD)

    mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
    mqtt_client.loop_start()

    mc = await MeshCore.create_serial(
        SERIAL_PORT,
        baudrate=SERIAL_BAUD,
        auto_reconnect=True,
    )

    mc.subscribe(EventType.CONTACT_MSG_RECV, on_contact_message)
    mc.subscribe(EventType.CHANNEL_MSG_RECV, on_channel_message)
    mc.subscribe(EventType.CONNECTED, on_connected)
    mc.subscribe(EventType.DISCONNECTED, on_disconnected)

    try:
        await mc.connect()

        logging.info("MeshCore serial connection established")

        # Companion může mít čekající zprávy.
        await mc.start_auto_message_fetching()

        while True:
            await asyncio.sleep(3600)

    finally:
        logging.info("Ukončuji MeshCore adapter")

        try:
            await mc.disconnect()
        except Exception:
            pass

        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
