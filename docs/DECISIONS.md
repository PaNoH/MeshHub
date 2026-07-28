# MeshHub Architecture Decision Log

**Status:** Living ADR-style log
**Last updated:** 2026-07-28

This file records important decisions and why they were made.

## D001 — MQTT remains the internal event bus

**Date:** 2026-07-26
**Status:** Accepted

**Decision:** Use MQTT as the lightweight internal event bus.

**Reason:** It is simple, local, transport-neutral, suitable for the Orange Pi, and already works with the MeshCore adapter.

**Consequence:** Matrix may later be an external/high-level transport rather than replacing MQTT internally.

## D002 — Development is RX-first

**Date:** 2026-07-26
**Status:** Accepted

**Decision:** The first public milestone does not retransmit received traffic onto another RF network.

**Reason:** Cross-network LoRa forwarding can consume scarce shared airtime and multiply traffic.

**Consequence:** M1 is an Observatory/non-RF-output milestone.

## D003 — Reception does not imply forwarding

**Date:** 2026-07-26
**Status:** Accepted

**Decision:** Receiving an event never automatically authorizes forwarding.

**Reason:** Transports differ in privacy expectations, routing semantics, trust, payload constraints, and resource costs.

**Consequence:** Routing is explicit and policy-controlled; unmatched cross-network traffic defaults to deny/drop or local-only.

## D004 — Public MeshCore traffic is not mirrored to Telegram by default

**Date:** 2026-07-26
**Status:** Accepted

**Decision:** Do not copy ordinary MeshCore Public traffic to Telegram for M1.

**Reason:** Public RF traffic does not necessarily imply an expectation of Internet republication.

**Consequence:** Use a dedicated test channel whose purpose is explicit.

## D005 — M1 uses a dedicated logical test channel

**Date:** 2026-07-27
**Status:** Accepted

**Decision:** Use `MeshHub-Test` as the initial logical test channel.

**Consequence:**

```text
MeshCore MeshHub-Test -> MeshHub -> Telegram MeshHub-Test
```

Telegram -> mesh is out of scope for M1.

## D006 — Display names are not routing identifiers

**Date:** 2026-07-27
**Status:** Accepted

**Decision:** Matching human-visible names are useful, but routing uses stable transport-native identifiers.

**Consequence:** Map MeshCore `channel_idx`, Telegram `chat_id`, and future transport IDs to logical channels.

## D007 — Telegram Channel rather than Group for M1

**Date:** 2026-07-27
**Status:** Accepted

**Decision:** Use a Telegram Channel for the first RX-only demo.

**Reason:** The initial flow is one-way publication rather than bidirectional discussion.

## D008 — RF forwarding must be resource-aware

**Date:** 2026-07-26
**Status:** Accepted

**Decision:** A logically valid route is not sufficient to authorize constrained RF TX.

**Reason:** LoRa airtime is a limited shared resource.

**Consequence:** Future policy may consider airtime, payload size, congestion, rate limits, hop behaviour, priority, and destination capabilities.

## D009 — Shadow routing precedes RF TX

**Date:** 2026-07-26
**Status:** Accepted

**Decision:** Support dry-run/shadow evaluation before cross-network RF TX.

**Consequence:** Future routing can produce:

```text
WOULD_FORWARD
WOULD_TX
estimated_airtime = ...
```

without transmitting.

## D010 — Matrix complements MeshHub

**Date:** 2026-07-26
**Status:** Accepted

**Decision:** Do not rebuild Matrix-like rooms, persistence, federation, synchronization, and client UX inside MeshHub.

**Reason:** MeshHub's distinct role is edge interoperability, transport adaptation, policy, identity mapping, and constrained-resource awareness.

## D011 — Forwarding does not create identity trust

**Date:** 2026-07-26
**Status:** Accepted

**Decision:** Keep claimed, transport, logical, and verified identity concepts distinct.

**Reason:** A gateway can carry a claim but cannot make it trustworthy merely by forwarding it.

## D012 — Bidirectional routing requires loop prevention

**Date:** 2026-07-26
**Status:** Accepted

**Decision:** General bidirectional bridging requires message identity, deduplication, TTL/hop controls, and provenance.

**Reason:** Otherwise a logical message can circulate between networks or gateways.

## D013 — MeshHub is a working name

**Date:** 2026-07-27
**Status:** Accepted

**Decision:** Continue using `MeshHub` as the repository/project working name while final branding remains unresolved.

**Reason:** Name collisions exist in adjacent mesh/Meshtastic space.

## D014 — GitHub documentation is canonical project memory

**Date:** 2026-07-28
**Status:** Accepted

**Decision:** Preserve current state and architectural reasoning in repository documentation.

**Reason:** Conversation history is useful but should not be the canonical engineering record.

**Consequence:** Maintain:

```text
README.md
docs/PROJECT-CONTEXT.md
docs/DECISIONS.md
```

Update project context at meaningful handoff points and add new decisions here rather than silently losing architectural history.

## Adding a decision

Use the next sequential ID and record date, status, decision, reason, and consequence. If an accepted decision changes, add a new decision that supersedes it rather than silently rewriting history.
