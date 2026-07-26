# MeshHub Airtime Policy

**Status:** RFC Draft / Public Review  
**Version:** 0.1

**Review purpose:** Public technical discussion. This document describes proposed
policy for responsible bridging between heterogeneous off-grid and mesh networks.
Examples are synthetic and are not operational configuration.

## 1. Purpose

MeshHub can bridge messages between transports with radically different capacity,
latency and airtime constraints.

A gateway MUST NOT treat a shared LoRa channel as if it were an unlimited IP link.

The purpose of this RFC is to define rules that prevent bridging from causing
uncontrolled airtime consumption on a destination network.

MeshHub is therefore not a transparent forwarder.

It is a policy-controlled interoperability layer.

## 2. Fundamental rule

Receiving a message on one network does NOT imply permission to transmit it on
another network.

Conceptually:

```text
Source network
      |
      v
   Adapter
      |
      v
 MeshHub Core
      |
      +-- Routing
      +-- Identity / Trust
      +-- Deduplication
      +-- Airtime Policy
      |
      v
 Destination adapter
      |
      v
Destination network
```

Every cross-network transmission MUST pass destination policy before radio TX.

## 3. Why airtime matters

LoRa networks use a shared and capacity-constrained radio medium.

The cost of forwarding a message depends on more than message count.

Relevant factors may include:

- payload size
- spreading factor
- bandwidth
- coding rate
- packet overhead
- retransmissions
- acknowledgements
- routing behaviour
- network-specific flooding
- regulatory duty-cycle limits
- local channel occupancy

Therefore:

```text
20 messages/hour
```

is not by itself a sufficient airtime policy.

MeshHub SHOULD ultimately reason in estimated or measured airtime.

## 4. No default public-channel mirroring

MeshHub MUST NOT automatically mirror complete public channels between networks.

For example, this MUST NOT be the default:

```text
Network A / Public
        |
        v
     MeshHub
        |
        v
Network B / Public
```

A busy source network could otherwise consume radio capacity on a destination
network whose participants never requested that traffic.

Cross-network forwarding SHOULD require an explicit route or bridge policy.

## 5. Explicit bridge mappings

Example conceptual configuration:

```yaml
bridges:
  expedition:
    source: "network-a/channel/2"
    target: "network-b/channel/Expedition"

    policy:
      enabled: true
      deduplicate: true
      forward_unverified: false
      priority: bridged
      max_payload_bytes: 120
      max_messages_per_hour: 20
```

This is an example data model, not a final configuration syntax.

A bridge SHOULD identify:

- source
- destination
- permitted message classes
- identity/trust requirements
- rate limits
- airtime budget
- payload limits
- duplicate policy
- priority

## 6. Airtime budget

Each constrained destination transport SHOULD have an independent airtime budget.

Conceptually:

```text
Destination: network-b / LoRa

Configured bridge budget: 2.0 %
Estimated used:          0.7 %
Remaining:               1.3 %
```

The exact unit and accounting window remain open design questions.

Possible models include:

- percentage of channel airtime
- milliseconds per rolling minute
- seconds per hour
- token bucket where tokens represent airtime
- network-specific channel-utilisation budget

Airtime accounting SHOULD be based on expected TX cost where practical.

## 7. Native traffic vs. bridged traffic

Bridged traffic SHOULD have lower default priority than traffic originating
natively on the destination network.

A suggested priority model:

```text
EMERGENCY
CONTROL
DIRECT
NATIVE
BRIDGED
BULK
```

These names describe MeshHub policy classes and do not redefine transport-native
priority mechanisms.

When capacity is constrained, MeshHub SHOULD degrade bridged traffic before
ordinary native traffic.

Example:

```text
EMERGENCY       PASS
CONTROL         PASS
DIRECT          PASS
NATIVE          PASS
BRIDGED         THROTTLE
BULK            DROP or DEFER
```

Emergency classification MUST NOT allow arbitrary users to bypass airtime policy.

Authorisation rules for emergency/control classes are required.

## 8. Rate limiting

Rate limiting is a coarse protection layer in addition to airtime accounting.

Possible limits:

```text
per bridge
per source identity
per source network
per destination network
per logical group
per gateway
```

Example:

```yaml
limits:
  bridge_messages_per_hour: 20
  source_messages_per_minute: 3
  burst: 5
```

Rate limiting MUST NOT be the only protection for constrained radio transports.

## 9. Deduplication

A message already transmitted or processed by a gateway SHOULD NOT be transmitted
again merely because it returned through another bridge path.

MeshHub messages SHOULD carry a globally unique message ID.

Recommended initial candidate:

```text
UUIDv7
```

Gateways SHOULD maintain a recent-message cache.

Example:

```text
Network A
   |
Gateway 1
   |
Network B
   |
Gateway 2
   |
Network A
```

If Gateway 1 sees the same message ID again:

```text
DROP: duplicate
```

Deduplication saves airtime and prevents bridge loops.

## 10. Hop limits and trace

Messages MAY contain:

```json
{
  "hop_count": 2,
  "trace": [
    "gateway:node01",
    "gateway:node02"
  ]
}
```

MeshHub SHOULD support a maximum bridge hop count.

Trace data MUST be designed with payload cost and privacy in mind.

A compact representation MAY be required on constrained transports.

## 11. Payload limits

Destination transports MAY impose bridge-specific payload limits.

Example:

```yaml
max_payload_bytes: 120
```

If a source message is too large, policy MAY:

```text
DROP
TRUNCATE
SUMMARISE
DEFER
USE AN ALTERNATE TRANSPORT
```

Silent truncation SHOULD NOT be the default because it changes message meaning.

Fragmentation SHOULD be used cautiously because multiple packets can multiply
airtime cost and failure probability.

## 12. Trust-aware forwarding

Airtime is a scarce resource.

MeshHub MAY therefore use identity and trust information when deciding whether a
message is worth transmitting.

Example policy:

```text
END_TO_END_VERIFIED     normal bridge quota
NETWORK_VERIFIED        restricted quota
UNVERIFIED              disabled or very small quota
```

Trust MUST NOT automatically grant unlimited airtime.

Identity verification and resource authorisation are separate decisions.

## 13. Per-source quotas

One source MUST NOT be able to consume the complete bridge budget.

A destination policy SHOULD support per-source quotas.

Conceptually:

```text
bridge budget
    |
    +-- source A
    +-- source B
    +-- source C
```

Unknown or unverified sources MAY receive a smaller quota than explicitly trusted
sources.

## 14. Broadcast amplification

Broadcast and flooded messages can have a much larger network cost than a single
gateway transmission suggests.

MeshHub SHOULD account for transport behaviour when estimating cost.

A single bridge TX may cause:

```text
1 gateway transmission
        |
        +-- relay
        +-- relay
        +-- relay
        +-- retransmission
```

Therefore local TX airtime and estimated network impact are different metrics.

Future versions SHOULD distinguish:

```text
local_tx_airtime
estimated_network_cost
```

## 15. Acknowledgements and retries

Acknowledgements, retries and transport-level reliability consume capacity.

Airtime estimation SHOULD include expected protocol overhead where known.

MeshHub SHOULD avoid creating cross-network acknowledgement loops.

An acknowledgement from Network A MUST NOT automatically become an acknowledgement
on Network B unless a bridge protocol explicitly defines that semantic mapping.

## 16. Backpressure

When the destination network is congested, MeshHub SHOULD be able to apply
backpressure rather than blindly queueing traffic.

Possible actions:

```text
PASS
DEFER
THROTTLE
DROP
REROUTE
```

Queues SHOULD have bounded size and message lifetime.

Expired low-priority messages SHOULD be discarded instead of transmitted late.

## 17. Message lifetime

Bridged messages SHOULD support an expiration time.

Example:

```json
{
  "created_at": 1785024085,
  "expires_at": 1785024385
}
```

A gateway MUST NOT spend scarce airtime transmitting a message whose useful
lifetime has expired.

Different message classes MAY use different lifetimes.

## 18. Scheduling

A constrained destination adapter MAY maintain a priority queue.

Conceptually:

```text
TX scheduler
    |
    +-- emergency
    +-- control
    +-- direct
    +-- native
    +-- bridged
    +-- bulk
```

Scheduling SHOULD consider:

- priority
- message age
- expiration
- source quota
- bridge quota
- airtime cost
- destination availability

## 19. Airtime estimation

For LoRa transports, estimated packet airtime depends on radio parameters and
payload length.

MeshHub SHOULD NOT assume one fixed cost per message.

The adapter SHOULD expose enough transport information for policy evaluation where
possible.

Conceptual interface:

```json
{
  "payload_bytes": 74,
  "estimated_airtime_ms": 412,
  "transport": "lora"
}
```

The exact airtime calculation belongs in the transport adapter or a
transport-specific policy module.

## 20. Regulatory constraints

Airtime policy MUST NOT be used to bypass regulatory requirements.

Where applicable, adapters MUST respect local radio regulations and
transport/firmware restrictions independently of MeshHub's own budget.

MeshHub's configured budget may be stricter than the legal maximum.

It MUST NOT be treated as permission to transmit up to a regulatory limit.

## 21. Fail-safe behaviour

If MeshHub cannot determine whether a constrained destination is safe to use, the
default behaviour SHOULD be conservative.

Examples:

```text
unknown destination capacity -> restrict bridged traffic
airtime estimator failure    -> use conservative fallback
policy configuration invalid -> disable affected bridge
dedup cache unavailable      -> prevent uncontrolled multi-bridge forwarding
```

A configuration error SHOULD NOT turn MeshHub into an unrestricted public-channel
mirror.

## 22. Observability

MeshHub SHOULD expose airtime and bridge-policy metrics.

Useful metrics include:

```text
messages_received
messages_forwarded
messages_dropped
messages_deduplicated
messages_throttled
estimated_airtime_used
airtime_budget_remaining
queue_depth
expired_messages
per_source_usage
```

Operators SHOULD be able to determine why a message was not forwarded.

Example:

```text
DROP bridge=expedition
reason=AIRTIME_BUDGET_EXCEEDED
source=User1212
```

## 23. Dry-run mode

A bridge SHOULD support a dry-run mode.

In dry-run mode MeshHub evaluates routing and airtime policy but does not transmit.

Example:

```yaml
bridge:
  enabled: true
  dry_run: true
```

This allows operators to observe:

```text
would_forward
would_drop
estimated_airtime
budget impact
```

before enabling radio forwarding.

## 24. Bridge activation

New radio bridges SHOULD initially be deployed in stages:

```text
1. receive only
2. dry run
3. restricted trusted sources
4. low airtime budget
5. normal controlled operation
```

Public bidirectional bridging SHOULD NOT be the first deployment mode.

## 25. Default policy proposal

Initial safe defaults:

```text
public channel mirroring: OFF
bridge creation: explicit
deduplication: ON
hop limit: ON
airtime budget: required for constrained radio TX
unverified forwarding: OFF by default
bulk forwarding: OFF
dry-run support: ON
bounded queues: ON
message expiration: ON
```

Individual deployments MAY relax these rules deliberately.

## 26. Relationship to Identity RFC

The Identity RFC answers:

```text
Who claims to have sent this?
What identity can MeshHub verify?
What did a gateway attest?
```

The Airtime RFC answers:

```text
Should this message consume capacity on the destination network?
When should it be transmitted?
How much scarce radio resource may it consume?
```

Identity verification is an input to airtime policy, not a replacement for it.

A fully verified message may still be dropped because its bridge has exhausted its
airtime budget.

## 27. Proposed MeshHub architecture

```text
                    MeshHub Core
                         |
       +-----------------+-----------------+
       |                 |                 |
    Identity          Routing        Airtime Policy
       |                 |                 |
     Trust             Dedup          +-- Budget
                                         +-- Priority
                                         +-- Quotas
                                         +-- Rate limit
                                         +-- Scheduler
                                         +-- Expiry
                         |
                         v
                  Transport Adapter
                         |
                         v
                   Radio / Network
```

The TX adapter MUST NOT bypass policy for bridged traffic.

## 28. Open questions

### Q1. Budget unit

Should the primary budget be:

```text
airtime milliseconds
percentage of observed channel capacity
token bucket
transport-specific metric
```

Initial preference: airtime-based token bucket for constrained radio transports.

### Q2. Native traffic visibility

Can MeshHub reliably observe enough native destination traffic to estimate total
channel occupancy?

If not, the bridge budget MUST remain conservative.

### Q3. Network amplification

How should MeshHub estimate the downstream cost of flooded or relayed packets?

Unresolved.

### Q4. Emergency priority

How is emergency classification authorised without creating a trivial airtime
bypass?

Requires Identity/Authorisation integration.

### Q5. Congestion feedback

Can destination adapters expose channel utilisation, queue state or other
congestion signals?

Transport-specific.

### Q6. Cross-gateway coordination

Should multiple MeshHub gateways sharing one destination network coordinate a
common airtime budget?

Desirable, but not required for the first implementation.

### Q7. Store-and-forward

Should deferred traffic be transmitted when capacity later becomes available?

Probably only for explicitly delay-tolerant message classes.

## 29. Implementation milestones

### Airtime M1 — Safe routing

Implement:

```text
explicit bridge mappings
deduplication
hop limit
payload limit
rate limiting
```

No automatic public-channel mirroring.

### Airtime M2 — Accounting

Add:

```text
estimated TX airtime
per-bridge counters
per-source counters
bounded rolling windows
```

### Airtime M3 — Budget enforcement

Implement per-destination airtime budgets and token-bucket enforcement.

### Airtime M4 — Priority scheduler

Introduce priority, expiry, bounded queues and backpressure.

### Airtime M5 — Transport awareness

Allow adapters to expose:

```text
estimated airtime
channel utilisation
retry cost
network amplification hints
```

### Airtime M6 — Multi-gateway coordination

Explore shared budgets and congestion information between cooperating MeshHub
gateways.

## 30. Fundamental rule

MeshHub MUST be a good citizen of every destination network.

Interoperability does not grant permission to consume unlimited destination
airtime.

The safe default is:

```text
Do not forward unless routing policy permits it.
Do not transmit unless airtime policy permits it.
```
