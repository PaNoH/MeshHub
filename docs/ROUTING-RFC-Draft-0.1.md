# MeshHub Routing Model

**Status:** RFC Draft / Public Review  
**Version:** 0.1

**Review purpose:** Public technical discussion. This draft defines the routing
model for a policy-controlled interoperability router spanning heterogeneous
off-grid and mesh transports. All names, locations and identifiers in examples
are synthetic.

## 1. Purpose

MeshHub routes messages between heterogeneous networks such as MeshCore,
Meshtastic, Reticulum, APRS, MQTT, Matrix and future transports.

This RFC defines logical and transport-specific destinations, explicit
cross-network routing, route selection, forwarding policy, priorities, fallback
paths, TTL and hop limits, deduplication, loop prevention, and interaction with
Identity and Airtime policy.

MeshHub is NOT a transparent bridge.

A message received on one network MUST NOT be forwarded to another network unless
routing policy explicitly permits it.

## 2. Fundamental rule

Reception does not imply forwarding.

```text
Network A
   |
   v
Adapter
   |
   v
Normalization
   |
   v
MeshHub Core
   |
   +-- Identity / Trust
   +-- Routing Policy
   +-- Deduplication
   +-- Airtime Policy
   |
   +--> DROP
   +--> LOCAL ONLY
   +--> Network B
   +--> Network C
```

The default action for unmatched cross-network traffic SHOULD be `DROP` or
`LOCAL ONLY`, never `FORWARD EVERYWHERE`.

## 3. Routing layers

### 3.1 Logical destination

Human- or application-facing destination.

```text
@panxyz
@pcb4ham
#expedition
#operations
```

A logical destination does not directly identify one transport.

### 3.2 Canonical network destination

Format:

```text
mesh://<network>/<type>/<identifier>
```

Examples:

```text
mesh://meshcore/channel/2
mesh://meshtastic/node/!a1b2c3d4
mesh://reticulum/destination/0123456789abcdef
mesh://aprs/callsign/<CALLSIGN>-7
```

### 3.3 Physical route

Actual transport selected for delivery.

```text
@panxyz
   |
   +-- mesh://meshcore/node/<id>
   +-- mesh://meshtastic/node/!a1b2c3d4
   +-- mesh://reticulum/destination/<hash>
```

The Routing layer selects one or more physical routes according to policy.

## 4. Logical aliases

Aliases MAY map to one or more destinations.

```yaml
aliases:
  "@panxyz":
    targets:
      - "mesh://meshcore/node/012345..."
      - "mesh://meshtastic/node/!a1b2c3d4"

  "#expedition":
    targets:
      - "mesh://meshcore/channel/2"
      - "mesh://meshtastic/channel/Expedition"
```

Alias expansion does NOT imply forwarding permission.

Every resulting destination MUST still pass route and airtime policy.

## 5. Message routing envelope

Proposed routing-relevant internal fields:

```json
{
  "id": "019b...",
  "origin": {
    "claimed": {
      "display_name": "User1212"
    },
    "verification": "UNVERIFIED"
  },
  "target": {
    "logical": "#expedition",
    "addresses": [
      "mesh://meshcore/channel/2",
      "mesh://meshtastic/channel/Expedition"
    ]
  },
  "type": "text",
  "payload": {
    "text": "We arrived."
  },
  "routing": {
    "priority": "BRIDGED",
    "ttl": 300,
    "max_hops": 4,
    "hop_count": 1,
    "trace": [
      "gateway:node01"
    ]
  }
}
```

The exact internal schema remains subject to change.

## 6. Explicit bridge definitions

Cross-network forwarding SHOULD be driven by explicit bridge definitions.

```yaml
bridges:
  expedition:
    source:
      network: meshcore
      address: "mesh://meshcore/channel/2"

    targets:
      - "mesh://meshtastic/channel/Expedition"

    policy:
      enabled: true
      priority: BRIDGED
      forward_unverified: false
      max_hops: 3
      ttl_seconds: 300
```

A bridge MUST NOT be inferred solely because source and destination channel names
look similar.

`Public` on two different networks MUST NOT automatically mean `Public <-> Public`.

## 7. Directionality

Routes MAY be one-way, bidirectional or conditional.

```yaml
direction: A_TO_B
```

or:

```yaml
direction: BIDIRECTIONAL
```

Bidirectional routes require deduplication and loop prevention.

Bidirectional forwarding SHOULD NOT be enabled by default for public channels.

## 8. Route match conditions

A route MAY match on:

- source network
- source address
- logical origin
- verification level
- message type
- target
- content class
- priority
- time window
- transport state
- gateway role

Example:

```yaml
match:
  source_network: meshcore
  source_channel: 2
  verification:
    - NETWORK_VERIFIED
    - END_TO_END_VERIFIED
  message_type:
    - text
```

Matching rules SHOULD be explicit and inspectable.

## 9. Routing decision

A routing decision SHOULD result in one of:

```text
DROP
LOCAL
FORWARD
DEFER
REROUTE
```

`DROP` — discard for this route.  
`LOCAL` — retain inside MeshHub, no external forwarding.  
`FORWARD` — eligible for destination policy and TX.  
`DEFER` — may be transmitted later.  
`REROUTE` — select an alternative destination.

## 10. Route priority

Routing priority is separate from source-network priority.

Suggested MeshHub classes:

```text
EMERGENCY
CONTROL
DIRECT
NATIVE
BRIDGED
BULK
```

A gateway MUST NOT allow arbitrary senders to self-classify normal chat as
`EMERGENCY`.

## 11. Trust-aware routing

Identity verification MAY be an input to routing policy.

```yaml
policy:
  minimum_verification: NETWORK_VERIFIED
```

or:

```yaml
policy:
  allow:
    - END_TO_END_VERIFIED
  deny:
    - UNVERIFIED
```

Trust alone does NOT imply route permission.

A verified sender still requires a matching route and airtime approval.

## 12. Source preservation

When forwarding between networks, MeshHub SHOULD preserve logical origin.

Transport-specific sender information MAY change, but MeshHub SHOULD preserve:

```text
logical origin
original network
verification state
message ID
```

inside the MeshHub envelope or equivalent metadata where possible.

## 13. Target preservation

Logical target and physical destination are different concepts.

```text
logical target:
  #expedition

physical destinations:
  MeshCore channel 2
  Meshtastic channel Expedition
```

A bridge MAY add or remove physical routes while preserving the logical target.

## 14. Message IDs

Every MeshHub message MUST have a globally unique message ID.

Initial recommendation:

```text
UUIDv7
```

A forwarded copy of the same logical message SHOULD retain the same message ID.

A new user-authored message MUST receive a new message ID.

## 15. Deduplication

Gateways SHOULD maintain a recent-message cache.

If the same message ID arrives again, the default action SHOULD be:

```text
DROP duplicate
```

unless transport-specific semantics explicitly require otherwise.

Deduplication SHOULD occur before cross-network forwarding.

## 16. Loop prevention

Example loop:

```text
MeshCore
   |
Gateway A
   |
Meshtastic
   |
Gateway B
   |
MeshCore
```

Without protection:

```text
A -> B -> A -> B -> ...
```

MeshHub SHOULD use message ID cache, hop count, route trace, maximum hops and
route-specific loop rules.

## 17. Hop count

Messages MAY contain:

```json
{
  "hop_count": 2,
  "max_hops": 4
}
```

Before forwarding:

```text
hop_count + 1 > max_hops
```

results in:

```text
DROP: HOP_LIMIT
```

Transport-native hop counts SHOULD NOT automatically be treated as MeshHub bridge
hop counts.

## 18. Route trace

MeshHub MAY maintain a route trace.

```json
{
  "trace": [
    "gateway:node01",
    "network:reticulum",
    "gateway:node02"
  ]
}
```

Trace is useful for debugging, loop detection, audit and policy evaluation.

Trace size SHOULD be bounded. Compact representation MAY be required on
constrained transports.

## 19. TTL and expiration

Messages SHOULD support a routing lifetime.

```json
{
  "created_at": 1785024085,
  "expires_at": 1785024385
}
```

A route MUST NOT forward an expired message.

TTL is especially important for deferred and store-and-forward routes.

## 20. Store-and-forward

Some routes MAY be delay tolerant.

```text
destination unavailable
        |
        v
       DEFER
        |
        v
queue with expiry
```

Store-and-forward MUST be explicit.

```yaml
store_and_forward:
  enabled: true
  max_age_seconds: 900
```

Normal chat SHOULD NOT silently become long-term queued traffic.

## 21. Fallback routes

Logical destinations MAY have fallback transports.

```yaml
routes:
  "@panxyz":
    preferred:
      - reticulum
    fallback:
      - meshcore
      - meshtastic
```

Fallback MAY depend on destination reachability, airtime budget, transport
availability, trust requirements, payload size and latency class.

Fallback MUST NOT cause duplicate delivery unless policy permits it.

## 22. Single-path vs. multi-path delivery

A route MAY use:

```text
SINGLE_PATH
MULTI_PATH
```

`SINGLE_PATH` selects one destination transport.

`MULTI_PATH` intentionally sends the same logical message over multiple
transports.

Multi-path SHOULD be used carefully because it increases resource usage.

## 23. Reachability

Adapters MAY expose reachability information.

Examples:

```text
node recently seen
active Reticulum path
MQTT connection available
radio adapter online
```

Reachability MAY influence route selection.

Absence of recent reachability data MUST NOT always mean unreachable, especially
on delay-tolerant networks.

## 24. Routing metrics

Future route selection MAY consider:

```text
latency
airtime cost
reliability
trust
hop count
transport availability
energy cost
payload capacity
```

The first implementation SHOULD remain deterministic and simple.

## 25. Airtime integration

A routing decision does NOT guarantee transmission.

```text
route match
    |
    v
FORWARD candidate
    |
    v
Airtime Policy
    |
    +--> PASS
    +--> DEFER
    +--> THROTTLE
    +--> DROP
```

Routing answers:

```text
Where is this message allowed to go?
```

Airtime policy answers:

```text
May it consume destination capacity now?
```

## 26. Identity integration

Identity answers:

```text
Who claims to have sent this?
What identity can MeshHub verify?
```

Routing MAY use this information.

Routing MUST NOT promote identity trust.

## 27. Transport adapters

Adapters SHOULD translate between transport-native addressing and MeshHub canonical
addresses.

```text
MeshCore channel 2
        |
        v
mesh://meshcore/channel/2
```

Adapters SHOULD NOT contain global cross-network routing policy.

Their primary responsibilities are:

- transport connection
- address translation
- RX normalization
- TX encoding
- transport metadata
- transport capability reporting

Cross-network policy belongs in MeshHub Core.

## 28. Adapter capabilities

An adapter MAY report capabilities such as:

```json
{
  "network": "meshcore",
  "supports_direct": true,
  "supports_channels": true,
  "supports_ack": false,
  "max_payload": 180,
  "constrained_airtime": true
}
```

Routing policy MAY use capabilities when selecting a path.

## 29. Public channels

Public channels are high-risk routing sources.

Default policy SHOULD be:

```text
public cross-network forwarding = OFF
```

A public-channel bridge MUST be explicitly enabled.

Recommended controls:

- strict rate limit
- small airtime budget
- deduplication
- source filtering
- payload limit
- dry-run before activation

## 30. Direct messages

Direct messages MAY have different routing policy from channel traffic.

A logical target such as:

```text
@panxyz
```

may resolve to a preferred transport and one fallback.

Direct routing SHOULD avoid broadcasting a private message into a public channel.

## 31. Groups

A logical group MAY span multiple transports.

```text
#expedition
   |
   +-- MeshCore channel 2
   +-- Meshtastic channel Expedition
   +-- Matrix room
```

Group fan-out MUST be explicit.

Each destination is evaluated independently.

One destination may PASS while another is DROP or DEFER.

## 32. Routing and privacy

Route expansion can reveal identity relationships.

```text
@panxyz
  -> MeshCore identity
  -> APRS callsign
  -> Matrix account
```

These mappings SHOULD NOT be exposed publicly by default.

Logical identity-to-network mapping MUST respect Identity RFC privacy policy.

## 33. Routing authorisation

Being able to address a target does not imply permission to route to it.

MeshHub SHOULD support authorisation checks such as:

```text
who may send to #operations
who may use Network B
who may request MULTI_PATH
who may use CONTROL priority
```

Identity verification and authorisation are separate.

## 34. Policy order

Initial proposed processing order:

```text
1. Receive
2. Normalize
3. Assign / preserve message ID
4. Deduplicate
5. Determine identity evidence
6. Resolve logical target
7. Match routing policy
8. Check authorisation
9. Expand candidate destinations
10. Evaluate airtime/resource policy per destination
11. Encode through adapter
12. Transmit
13. Record trace and metrics
```

## 35. Dry-run routing

Routing policy SHOULD support dry-run mode.

```yaml
routing:
  dry_run: true
```

Dry-run logs decisions without transmitting:

```text
message=019b...
source=meshcore/channel/2
target=#expedition
decision=WOULD_FORWARD
destination=meshtastic/channel/Expedition
```

This is strongly recommended before activating new cross-network routes.

## 36. Observability

MeshHub SHOULD expose routing metrics such as:

```text
messages_received
messages_local
messages_forwarded
messages_dropped
messages_deferred
duplicates_dropped
hop_limit_drops
route_not_found
authorisation_denied
fallback_used
per_route_usage
per_destination_usage
```

Operators SHOULD be able to determine why a message was forwarded or dropped,
which rule matched and which destination was selected.

## 37. Audit log

Routing decisions SHOULD be auditable.

```text
message=019b...
rule=expedition-a-to-b
decision=FORWARD
destination=mesh://meshtastic/channel/Expedition
identity=NETWORK_VERIFIED
airtime=PASS
```

Audit logging SHOULD avoid unnecessary disclosure of private message contents.

## 38. Configuration errors

Fail-safe behaviour SHOULD be conservative.

```text
unknown target       -> DROP / LOCAL
invalid route        -> DISABLE route
adapter unavailable  -> DEFER or DROP according to policy
ambiguous alias      -> DO NOT guess
policy load failure  -> disable cross-network forwarding
```

A broken configuration MUST NOT turn MeshHub into a blanket bridge.

## 39. Route conflicts

Multiple rules MAY match the same message.

The routing engine MUST define deterministic conflict resolution.

Possible model:

```text
highest explicit priority
then most specific match
then configured rule order
```

Conflicting rules SHOULD generate diagnostics.

## 40. Route specificity

Example specificity ordering:

```text
exact source + exact target + message type
exact source + target
source network + target
global default
```

More specific rules SHOULD normally override less specific rules.

## 41. Negative rules

Routing policy SHOULD support explicit deny rules.

```yaml
deny:
  - source: "mesh://meshcore/channel/0"
    target_network: meshtastic
```

Explicit deny SHOULD take precedence over generic allow.

## 42. Route templates

Reusable route policies MAY be defined.

```yaml
templates:
  constrained-bridge:
    deduplicate: true
    priority: BRIDGED
    max_hops: 2
    ttl_seconds: 300
```

Templates MUST expand into deterministic effective policy.

## 43. Routing domains

MeshHub SHOULD distinguish:

```text
transport-native routing
MeshHub cross-network routing
```

MeshCore or Reticulum may route internally through many hops.

MeshHub does not need to understand every internal hop.

Its responsibility begins at ingress into MeshHub and ends at egress into a
selected transport.

## 44. Relationship to Reticulum

Reticulum provides its own addressing, path discovery and routing.

MeshHub SHOULD treat Reticulum as a capable transport/routing domain rather than
reimplementing Reticulum internals.

```text
MeshHub
   |
   v
Reticulum adapter
   |
   v
RNS routing domain
```

The MeshHub Routing layer decides whether and why to enter the Reticulum domain.

RNS decides how to deliver inside that domain.

The same principle applies to other transports with native routing.

## 45. Relationship to Identity RFC

Identity defines:

```text
claimed origin
verified origin
network identity evidence
gateway attestation
```

Routing consumes identity information but MUST NOT manufacture trust.

## 46. Relationship to Airtime RFC

Airtime policy is evaluated per constrained destination.

A route may be valid while transmission is denied.

```text
Routing: FORWARD to Meshtastic
Airtime: DROP - budget exhausted
```

This is expected behaviour.

## 47. Safe defaults

Initial recommended defaults:

```text
cross-network routes: NONE
public-channel bridging: OFF
bidirectional bridging: OFF
deduplication: ON
message IDs: REQUIRED
hop limit: ON
TTL: ON
unverified cross-network forwarding: OFF
multi-path: OFF
dry-run support: ON
fail closed on policy error: ON
```

Operators MAY explicitly relax these defaults.

## 48. Example: controlled one-way group bridge

```yaml
bridges:
  expedition-a-to-b:

    match:
      source: "mesh://meshcore/channel/2"
      type: text

    target:
      logical: "#expedition"
      addresses:
        - "mesh://meshtastic/channel/Expedition"

    policy:
      direction: A_TO_B
      minimum_verification: NETWORK_VERIFIED
      priority: BRIDGED
      max_hops: 2
      ttl_seconds: 300
```

The target still requires Airtime Policy approval.

## 49. Example: direct logical identity

```yaml
identities:
  "@panxyz":
    preferred:
      - "mesh://reticulum/destination/012345..."
    fallback:
      - "mesh://meshcore/node/abcdef..."
```

Sending to `@panxyz` may select Reticulum when available and MeshCore only as
fallback.

This MUST NOT disclose all linked identities to unrelated users.

## 50. Example: no route

Incoming:

```text
source = mesh://meshcore/channel/0
target = none
```

No cross-network rule matches.

Result:

```text
LOCAL
```

or:

```text
DROP
```

depending on local ingestion policy.

It MUST NOT result in broadcast to all configured networks.

## 51. Open questions

### Q1. Logical destination namespace

Should aliases such as `@user` and `#group` remain local configuration, or become
portable MeshHub identifiers?

Initial proposal: local aliases in v1.

### Q2. Multi-path

Should MeshHub support intentional delivery over several transports in v1?

Initial proposal: supported by model, disabled by default.

### Q3. Reachability

What minimum reachability model can work consistently across highly different
transports?

Unresolved.

### Q4. Rule language

Candidates:

```text
YAML declarative rules
JSON
Python plugins
Node-RED generated policy
```

Initial preference: simple declarative configuration with optional extension
points later.

### Q5. Route score

Should first implementation use route scoring or deterministic ordered rules?

Initial proposal: deterministic ordered rules.

### Q6. Store-and-forward

Which message classes may be queued and for how long?

Must be explicit per route.

### Q7. Negative routes

Should deny rules always override allow rules?

Initial proposal: YES.

### Q8. Cross-gateway routing

How should multiple MeshHub gateways exchange route availability?

Outside initial implementation scope.

## 52. Implementation milestones

### Routing M1 — Message identity and dedup

Implement:

```text
message ID
dedup cache
hop count
TTL
```

### Routing M2 — Explicit one-way routes

Implement simple deterministic:

```text
source -> target
```

rules.

No public automatic bridge.

### Routing M3 — Logical aliases

Add `@user` and `#group` resolution.

### Routing M4 — Policy integration

Integrate Identity verification, Authorisation and Airtime Policy.

### Routing M5 — Fallback routing

Add preferred route, fallback route and transport availability.

### Routing M6 — Store-and-forward

Add bounded deferred queues with expiry.

### Routing M7 — Multi-path

Support explicitly authorised redundant delivery.

### Routing M8 — Distributed route awareness

Explore coordination between multiple MeshHub gateways.

## 53. Fundamental rule

MeshHub routes intentionally, not automatically.

The safe model is:

```text
Receive
  |
  v
Understand
  |
  v
Match explicit policy
  |
  v
Authorise
  |
  v
Check destination resources
  |
  v
Forward
```

Never:

```text
Receive on A
  |
  +--> copy to B
  +--> copy to C
  +--> copy everywhere
```

unless an operator has explicitly defined that behaviour and destination policy
permits it.
