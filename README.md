# MeshHub

**Experimental interoperability layer for heterogeneous mesh and off-grid communication networks.**

> Current development stage: **RX-first / experimental**  
> MeshHub is not intended to operate as an uncontrolled cross-network RF bridge.

## Overview

MeshHub explores how different communication networks can be observed, normalized and eventually interconnected through explicit routing, identity, trust and resource policies.

The project is being developed around networks and transports such as:

- MeshCore
- Meshtastic
- Reticulum
- APRS
- MQTT
- Matrix
- Telegram
- other future transports

These systems have very different addressing models, routing behaviour, payload limits, trust models and resource constraints.

MeshHub provides a common layer between them without pretending that all transports are equivalent.

## Current goal: MeshHub Observatory

The first milestone is intentionally simple:

**Receive traffic from a selected mesh network, normalize it, analyse it and publish selected data to non-RF outputs.**

```text
MeshCore RF
    |
    v
USB Companion
    |
    v
MeshCore Adapter
    |
    v
   MQTT
    |
    v
 MeshHub
    |
    +--> statistics
    +--> logging
    +--> Telegram
    +--> Matrix (future)
```

The current experiment is **RX-first**.

Receiving a message does not imply forwarding it to another RF network.

## Why RX-first?

Cross-network RF forwarding can consume scarce shared radio capacity.

A naive bridge such as:

```text
MeshCore -> Meshtastic
         -> another LoRa network
         -> ...
```

could multiply traffic and negatively affect networks that never requested the additional traffic.

MeshHub therefore follows a fundamental principle:

> **Reception does not imply forwarding.**

Cross-network forwarding must eventually require explicit routing policy and destination resource policy.

Before RF forwarding is enabled, MeshHub should be able to observe and estimate the effects of a policy without transmitting it.

## Controlled demo

The first public demonstration is planned as a one-way path from a dedicated MeshCore test channel to a Telegram channel.

```text
MeshCore Public -----------------> ignored

MeshCore test channel
         |
         | RX
         v
      MeshHub
         |
         v
      Telegram
```

The normal MeshCore Public channel will not be mirrored to Telegram.

Only traffic from a channel explicitly configured for the experiment should be eligible for publication.

This avoids turning ordinary public mesh conversations into Internet content without the participants expecting it.

## Architecture

MeshHub uses transport adapters around a normalized internal event model.

Current prototype:

```text
MeshCore
   |
   v
adapter
   |
   v
  MQTT
   |
   v
MeshHub Core
```

Future architecture:

```text
                     MeshHub
                        |
          +-------------+-------------+
          |             |             |
       Identity       Routing      Resources
        mapping        policy       / airtime
          |             |             |
          +-------------+-------------+
                        |
                 normalized events
                        |
      +-----------------+-----------------+
      |                 |                 |
   MeshCore         Meshtastic           RNS
      |
   other adapters
```

MQTT currently acts as a lightweight internal event bus.

Matrix may later provide higher-level messaging, rooms, persistence and federation rather than MeshHub reinventing those mechanisms.

## Design principles

### Explicit routing

MeshHub must not automatically copy every received message to every connected network.

Default behaviour for unmatched cross-network traffic should be:

```text
DROP
```

or:

```text
LOCAL ONLY
```

not:

```text
FORWARD EVERYWHERE
```

### Resource-aware forwarding

A valid route does not automatically authorize transmission.

For constrained RF transports, forwarding policy may consider:

- airtime
- payload size
- rate limits
- network congestion
- hop behaviour
- destination capabilities
- message priority

### Identity preservation

Different networks represent identity differently.

MeshHub aims to preserve the distinction between:

- claimed identity
- transport identity
- verified identity
- logical identity
- gateway observations

A gateway must not create trust merely by forwarding a message.

### Loop prevention

Future bidirectional bridges must protect against forwarding loops using mechanisms such as:

- globally unique message IDs
- deduplication
- TTL
- hop limits
- route traces

### Fail closed

Configuration errors must not accidentally turn MeshHub into a blanket bridge.

If policy cannot be evaluated safely, cross-network forwarding should remain disabled.

## Example normalized event

A received MeshCore message may be represented internally as:

```json
{
  "source": "meshcore",
  "network": "meshcore",
  "type": "channel_message",
  "sender": "User1212",
  "destination": "channel:0",
  "payload": {
    "text": "Hello mesh.",
    "channel_idx": 0,
    "sender_timestamp": 1785019048
  }
}
```

The normalized representation allows other components to process events without depending directly on the MeshCore protocol.

## Safety model

The initial development stages are intentionally conservative.

### Stage 1 — RX Observatory

```text
RF RX -> normalization -> MQTT -> statistics/logging
```

No cross-network RF transmission.

### Stage 2 — Non-RF outputs

```text
RF RX -> policy -> Telegram / Matrix / other IP services
```

Only explicitly configured sources are eligible.

### Stage 3 — Shadow routing

Routing policies are evaluated, but RF transmission is simulated.

Example:

```text
WOULD_FORWARD
WOULD_TX
estimated_airtime = ...
```

No RF packet is transmitted.

### Stage 4 — Controlled TX experiments

Only after routing, identity, deduplication and resource policies have been tested.

RF forwarding must be explicitly configured and disabled by default.

## Project status

MeshHub is currently a **research and learning project**.

It should not yet be considered production-ready infrastructure.

The immediate development target is a working RX-only observatory using the existing MeshCore adapter and MQTT pipeline.

## Current prototype

The current prototype includes:

- Orange Pi based gateway
- MeshCore USB Companion
- Python MeshCore adapter
- normalized received messages
- MQTT event transport
- systemd service
- external JSON configuration

Current data path:

```text
MeshCore RF
    |
    v
USB Companion
    |
    v
Python adapter
    |
    v
meshhub/input/meshcore
    |
    v
MQTT
```

## Roadmap

### M1 — MeshHub Observatory

- stable MeshCore RX adapter
- normalized event format
- MQTT integration
- RX statistics
- path metadata collection
- dedicated test channel
- Telegram RX-only output

### M2 — Observation and policy

- source filtering
- anonymization options
- message IDs
- deduplication
- metrics
- dry-run routing

### M3 — Additional transports

Candidates include:

- Meshtastic
- Reticulum
- Matrix
- APRS

### M4 — Controlled routing experiments

- explicit routes
- identity mapping
- authorization
- TTL and hop limits
- resource / airtime policy
- shadow TX simulation

### M5 — Experimental constrained-network TX

Only explicitly configured private or experimental routes.

Cross-network RF forwarding remains opt-in.

## RFCs

Current drafts:

- [Identity and Trust](docs/IDENTITY-RFC-Draft-0.3.md)
- [Airtime / Resource Policy](docs/AIRTIME-RFC-Draft-0.1.md)
- [Routing](docs/ROUTING-RFC-Draft-0.1.md)

These documents are drafts and are expected to change as practical experiments reveal weaknesses in the model.

## Non-goals

MeshHub is not intended to:

- replace MeshCore
- replace Meshtastic
- replace Reticulum
- replace Matrix
- create an uncontrolled universal LoRa bridge
- mirror public conversations to the Internet by default
- bypass transport-specific routing or security models

The goal is to understand the boundaries between these systems and build controlled interoperability where it is useful and responsible.

## Contributing

MeshHub is experimental and feedback is welcome, particularly around:

- constrained-network routing
- LoRa airtime impact
- identity across heterogeneous transports
- bridge loop prevention
- Reticulum integration
- MeshCore and Meshtastic interoperability
- privacy implications of gateways

Please treat current interfaces and schemas as unstable.

## License

A license has not yet been selected.

Do not assume a license merely because the repository is public.

---

**MeshHub: understand first, route intentionally.**


## Support the project

If you find MeshHub useful and want to support further development:

[![Support MeshHub on Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20MeshHub-ff5e5b?logo=ko-fi&logoColor=white)](https://ko-fi.com/pannoh)

Support is completely optional.