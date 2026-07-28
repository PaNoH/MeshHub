# MeshHub Project Context

**Status:** Living project context
**Last updated:** 2026-07-28

This document is the canonical short-form context for continuing MeshHub development across sessions.

## Purpose

MeshHub is an experimental interoperability layer for heterogeneous mesh, radio, and off-grid communication networks. It is not intended to be an uncontrolled universal RF bridge.

Current principle:

> Reception does not imply forwarding.

Development is **RX-first**, with explicit policy for routing, identity, trust, deduplication, and constrained resources such as LoRa airtime.

## Current milestone — M1 MeshHub Observatory

Target:

```text
Dedicated MeshCore test channel
        |
        | RF RX only
        v
MeshCore Companion
        |
        v
MeshCore adapter
        |
        v
MQTT normalized event
        |
        v
policy/filter
        |
        v
Telegram test channel
```

Ordinary MeshCore Public traffic is not mirrored to Telegram by default.

## Working prototype

Current working path:

```text
MeshCore RF -> USB Companion -> Python adapter -> Mosquitto/MQTT
```

Host: Orange Pi Zero class Linux gateway.

Repository: `PaNoH/MeshHub`
Default branch: `master`

Adapter:

```text
adapters/meshcore/adapter.py
```

Configuration:

```text
config/meshcore.json
```

Current MQTT input topic:

```text
meshhub/input/meshcore
```

The MeshCore systemd service has been verified as enabled and active.

## Initial radio configuration

```text
Frequency: 869.432 MHz
Bandwidth: 62.5 kHz
SF:        7
CR:        5
```

These values are deployment configuration, not universal MeshHub defaults.

## Event model

MeshCore channel messages are normalized before MQTT publication. The event carries transport/network, event type, sender, destination, timestamp, and payload.

Useful MeshCore receive metadata includes `channel_idx`, `sender_timestamp`, `path_hash_mode`, and `path_len`. Observatory statistics should preserve useful path metadata where practical.

## MQTT and Matrix

MQTT remains the lightweight internal event bus:

```text
adapter -> normalized event -> MQTT -> policy/consumer/output adapter
```

Matrix may later provide higher-level messaging, rooms, persistence, federation, and client UX. It does not replace MeshHub's edge-specific transport adaptation, policy routing, identity mapping, or RF resource awareness.

## Safety stages

1. **Observatory:** RF RX -> normalization -> MQTT -> logging/statistics.
2. **Non-RF outputs:** explicitly selected sources -> Telegram/Matrix/IP services.
3. **Shadow routing:** evaluate `WOULD_FORWARD`, `WOULD_TX`, estimated airtime; no RF TX.
4. **Controlled RF TX:** opt-in only after routing, identity, authorization, deduplication, loop prevention, and resource policies are tested.

Default cross-network posture is deny/drop unless explicitly configured.

## Telegram M1 demo

Use a Telegram **Channel**, not Group, for the initial one-way publication demo.

Logical name:

```text
MeshHub-Test
```

Initial direction:

```text
MeshCore MeshHub-Test -> MeshHub -> Telegram MeshHub-Test
```

Human-visible names may match, but routing uses stable transport identifiers such as MeshCore `channel_idx` and Telegram `chat_id`.

Telegram -> mesh TX is out of scope for M1.

## Identity and routing

Gateway forwarding does not make an identity trustworthy. Keep claimed identity, transport identity, logical identity, verified identity, and gateway observations distinct.

Future bidirectional routing requires message IDs, deduplication, TTL/hop controls, provenance/route information, authorization, and destination policy.

A logically valid route does not automatically authorize constrained RF transmission. Airtime and other resource costs are part of future policy.

## RFCs

```text
docs/IDENTITY-RFC-Draft-0.3.md
docs/AIRTIME-RFC-Draft-0.1.md
docs/ROUTING-RFC-Draft-0.1.md
```

These are drafts.

## Naming

`MeshHub` is the working repository/project name. Name collisions exist in adjacent mesh/Meshtastic space, so final branding remains unresolved.

## Repository hygiene

Never commit passwords, API tokens, Telegram bot tokens, private keys, personal data captured from traffic, or deployment secrets.

## NEXT STEP

1. Create/configure the dedicated MeshCore test channel.
2. Confirm its `channel_idx`.
3. Configure the Telegram test channel and bot publishing access.
4. Add a Telegram output adapter/consumer for normalized MQTT events.
5. Add a default-deny filter allowing only the configured MeshCore test channel.
6. Verify MeshCore RF RX -> MQTT -> Telegram.
7. Confirm MeshHub performs zero RF TX.
8. Add Observatory statistics/path metadata after the basic path is stable.

## Resume instructions

In a new development session, read:

```text
README.md
docs/PROJECT-CONTEXT.md
docs/DECISIONS.md
```

plus the relevant RFC. Continue from `NEXT STEP`.
