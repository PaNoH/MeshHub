import json
import logging
import signal
import sys
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_HOST = "localhost"
MQTT_PORT = 1883
INPUT_TOPIC = "meshhub/input/#"
OUTPUT_TOPIC = "meshhub/internal/messages"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="meshhub-core",
)


def normalize_message(topic: str, raw_payload: bytes) -> dict:
    text = raw_payload.decode("utf-8", errors="replace")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {"text": text}

    if not isinstance(data, dict):
        data = {"payload": data}

    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    payload = data.get("payload")
    if payload is None:
        payload = {"text": data.get("text", "")}

    return {
        "id": data.get("id")
        or f"mqtt-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "source": data.get("source", "mqtt"),
        "network": data.get("network", "local"),
        "type": data.get("type", "text"),
        "sender": data.get("sender", "unknown"),
        "destination": data.get("destination", "broadcast"),
        "timestamp": data.get("timestamp")
        or datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "metadata": {
            **metadata,
            "mqtt_topic": topic,
        },
    }


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        logging.info("Připojeno k MQTT brokeru")
        client.subscribe(INPUT_TOPIC)
        logging.info("Odebírám téma %s", INPUT_TOPIC)
    else:
        logging.error("MQTT připojení selhalo: %s", reason_code)


def on_message(client, userdata, message):
    normalized = normalize_message(message.topic, message.payload)

    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    result = client.publish(OUTPUT_TOPIC, encoded)

    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        logging.info(
            "Zpráva %s publikována do %s",
            normalized["id"],
            OUTPUT_TOPIC,
        )
    else:
        logging.error(
            "Publikování zprávy %s selhalo: %s",
            normalized["id"],
            result.rc,
        )


def shutdown(signum, frame):
    logging.info("Ukončuji MeshHub Core")
    client.disconnect()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

client.on_connect = on_connect
client.on_message = on_message

logging.info("Spouštím MeshHub Core")
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_forever()
