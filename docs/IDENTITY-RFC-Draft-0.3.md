# MeshHub Identity Model

**Status:** RFC Draft / Public Review  
**Version:** 0.3

**Review purpose:** Public technical discussion. This draft intentionally uses
synthetic identities, locations, gateway names and keys. It contains no secrets
and MUST NOT be used as an operational configuration guide.


## 1. Purpose

MeshHub connects heterogeneous networks such as MeshCore, Meshtastic, Reticulum, APRS, MQTT, Matrix and future transports.

These networks use different identity models. Some provide cryptographic identities, some provide node IDs, callsigns or destination hashes, and some provide only display names.

MeshHub MUST NOT treat a display name as a trusted identity.

This document defines logical identities, device identities, network identities, aliases, verification levels, signed messages, gateway attestations, replay protection, duplicate detection and identity preservation across bridged networks.

## 2. Core principle

MeshHub MUST distinguish between:

1. what a message claims about its sender
2. what the originating network can prove
3. what MeshHub can cryptographically verify

Example:

```text
User1212: Hello
```

The string `User1212` is only a claimed display name unless stronger identity information is available.

## 3. Identity layers

### 3.1 Logical identity

Represents a person, organisation, bot, service or other actor.

Example:

```text
mh:7f3a91c8...
```

The identifier SHOULD NOT encode the cryptographic algorithm directly.

```json
{
  "id": "mh:7f3a91c8...",
  "algorithm": "ed25519",
  "public_key": "..."
}
```

This allows future algorithm migration without changing the identity namespace.

### 3.2 Device identity

A logical identity MAY own multiple devices.

```text
@panxyz
  |
  +-- phone
  +-- notebook
  +-- lilygo-01
  +-- gateway-home
```

Each device SHOULD have its own key pair. Private keys SHOULD NOT be copied across devices. A logical identity MAY certify device keys.

### 3.3 Network identity

A network identity is an identifier originating from a specific transport.

Examples:

```text
MeshCore: contact public key / node name / channel index
Meshtastic: !a1b2c3d4
Reticulum: destination hash
APRS: OK1ABC-7
Matrix: @user:server
```

A network identity MUST NOT automatically become a MeshHub logical identity.

## 4. Claimed and verified identity

MeshHub MUST keep claimed identity and verified identity separate.

```json
{
  "origin": {
    "claimed": {
      "display_name": "User1212"
    },
    "verified": null,
    "network": {
      "type": "meshcore",
      "address": "mesh://meshcore/channel/0"
    }
  }
}
```

If cryptographic verification succeeds:

```json
{
  "origin": {
    "claimed": {
      "display_name": "panxyz"
    },
    "verified": {
      "identity": "mh:7f3a91c8...",
      "device": "lilygo-01",
      "verification": "verified"
    },
    "network": {
      "type": "meshcore",
      "address": "mesh://meshcore/node/85f6..."
    }
  }
}
```

Code consuming MeshHub messages MUST NOT infer verified identity from `claimed.display_name`.

## 5. Verification levels

### VERIFIED

The message contains a valid MeshHub end-to-end signature.

```text
✓ panxyz
```

### NETWORK_VERIFIED

The originating network authenticated the sender, but the message does not contain a MeshHub end-to-end signature.

```text
◉ Alice via Reticulum
```

### UNVERIFIED

Only unauthenticated information is available.

```text
? User1212
```

Current MeshCore Public channel messages SHOULD normally enter MeshHub as `UNVERIFIED` unless stronger sender information is available.

## 6. Canonical network addresses

Format:

```text
mesh://<network>/<type>/<identifier>
```

Examples:

```text
mesh://meshcore/node/0123456789abcdef...
mesh://meshcore/channel/0
mesh://meshtastic/node/!a1b2c3d4
mesh://meshtastic/channel/LongFast
mesh://reticulum/destination/abc123...
mesh://aprs/callsign/<CALLSIGN>-7
```

Logical identities use:

```text
mh:<identity-id>
```

## 7. Aliases

Aliases exist only for human convenience.

Examples:

```text
@panxyz
@pcb4ham
#public
#expedice
```

Aliases MUST NOT be treated as cryptographic identities. Two unrelated users MAY use the same display alias.

```yaml
aliases:
  "@panxyz":
    identity: "mh:7f3a91c8..."

  "#expedice":
    targets:
      - "mesh://meshcore/channel/2"
      - "mesh://meshtastic/channel/Expedition"
```

## 8. Message envelope

```json
{
  "id": "019b...",
  "origin": {
    "claimed": {
      "display_name": "panxyz"
    },
    "verified": {
      "identity": "mh:7f3a91c8...",
      "device": "lilygo-01",
      "verification": "verified"
    },
    "network": {
      "type": "meshcore",
      "address": "mesh://meshcore/node/0123456789abcdef..."
    }
  },
  "target": {
    "logical": "#expedice",
    "address": "mesh://meshtastic/channel/Expedition"
  },
  "type": "text",
  "payload": {
    "text": "We arrived."
  },
  "security": {
    "signature": "...",
    "key_id": "device:lilygo-01",
    "algorithm": "ed25519",
    "created_at": 1785024085,
    "expires_at": 1785024385,
    "nonce": "..."
  },
  "transport": {
    "ingress": "meshcore",
    "gateway": "gateway:node01"
  }
}
```

## 9. Signed content

The signature MUST cover fields whose modification could alter meaning, sender identity or intended recipient.

At minimum:

```text
message id
origin identity
logical target
message type
payload
created_at
expires_at
nonce
```

The signed representation MUST be canonical. Raw JSON text MUST NOT be signed directly without canonicalization.

## 10. Canonical serialization

Candidates:

- Canonical CBOR
- RFC 8785 JSON Canonicalization Scheme
- other deterministic binary encoding

Initial preference: **Canonical CBOR**.

Reasons:

- compact representation
- deterministic encoding
- suitable for constrained transports
- binary data without Base64 overhead

This remains an open design decision.

## 11. Signature size and constrained networks

A full Ed25519 signature is 64 bytes. On LoRa networks this may represent significant overhead.

MeshHub therefore defines two security modes.

### 11.1 Native signed envelope

Used where the transport can carry the complete identity envelope.

Examples: Reticulum, MQTT, Matrix, IP transports.

### 11.2 Compact / session verification

Used for constrained transports.

Possible approaches include:

- shortened key references
- session-established identity
- gateway attestation
- signature carried separately
- message authentication over multiple packets
- transport-specific compact format

MeshHub MUST NOT falsely represent a gateway-attested message as end-to-end verified.

The exact compact signature mechanism is NOT defined in v0.1.


## 11A. MeshHub security layer vs. transport

Trusted identity is a property of the MeshHub security layer, not of MeshCore or any other transport.

MeshCore, Meshtastic, Reticulum, APRS and other networks are transports from the MeshHub point of view. Their native identity mechanisms MAY provide useful evidence, but they MUST NOT automatically be interpreted as MeshHub end-to-end identity.

A normal MeshCore message may therefore be received without modification:

```text
panxyz: Ahoj
```

The MeshCore adapter normalizes it into the MeshHub internal model:

```json
{
  "origin": {
    "claimed": {
      "display_name": "panxyz"
    },
    "verified": null,
    "verification": "UNVERIFIED"
  },
  "payload": {
    "text": "Ahoj"
  }
}
```

Creating this richer internal representation does NOT upgrade the sender's identity.

### 11A.1 Trusted end-to-end messages

For a message to become `END_TO_END_VERIFIED`, a trusted component acting for the origin identity MUST create authentication data before the message enters an untrusted transport.

```text
MeshHub-aware client
      |
      | "Ahoj"
      v
MeshHub identity + authentication
      |
      v
compact MeshHub envelope
      |
      v
MeshCore / other transport
      |
      v
receiving MeshHub
      |
      v
verify origin authentication
      |
      v
END_TO_END_VERIFIED
```

The transport does not need to understand MeshHub identity semantics. It only needs to carry the MeshHub representation.

### 11A.2 Internal representation vs. radio representation

The rich MeshHub JSON envelope is the internal interchange model and MAY be used over MQTT or other unconstrained transports.

It SHOULD NOT be assumed to be the on-air representation for constrained networks such as LoRa.

A compact transport representation MAY encode equivalent information, conceptually:

```text
[MH][version][message-id][time][payload][auth]
```

The exact binary format is outside the scope of v0.3.

A receiving MeshHub node converts the compact representation back into the normal internal message model.

### 11A.3 Gateway wrapping of legacy messages

A MeshHub gateway MAY receive an ordinary unsigned message and wrap it in a MeshHub envelope.

```text
phone
  |
  | normal MeshCore message
  v
MeshCore companion
  |
  v
MeshHub gateway
```

The gateway MAY authenticate the fact that it observed the message.

However, the gateway MUST NOT claim that it cryptographically verified the original human sender.

These statements are different:

```text
Origin identity:
  panxyz is cryptographically verified as author.
```

and:

```text
Gateway identity:
  node01 cryptographically confirms that it received
  a MeshCore message claiming to be from panxyz.
```

The second statement is a gateway attestation, not an end-to-end sender signature.

## 11B. Origin trust and gateway trust

Origin trust and gateway trust MUST be represented independently.

Proposed origin verification states:

```text
UNVERIFIED
NETWORK_VERIFIED
END_TO_END_VERIFIED
```

`UNVERIFIED` means MeshHub has only an unauthenticated claim, display name or equivalent weak identifier.

`NETWORK_VERIFIED` means the originating network provides authenticated sender information that the MeshHub adapter can verify or reliably bind to the message, but there is no MeshHub end-to-end origin authentication.

`END_TO_END_VERIFIED` means MeshHub can cryptographically verify the logical origin independently of intermediate gateways and transports.

Gateway trust is separate.

Initial gateway attestation states:

```text
NONE
ATTESTED
```

Example:

```json
{
  "origin": {
    "claimed": {
      "display_name": "panxyz"
    },
    "verification": "UNVERIFIED"
  },
  "gateway": {
    "id": "gateway:node01",
    "verification": "ATTESTED"
  }
}
```

This means:

```text
Claimed sender: panxyz
Origin: UNVERIFIED
Gateway observation: ATTESTED by node01
```

It MUST NOT be displayed or processed as equivalent to:

```text
Origin: END_TO_END_VERIFIED
```

A message may also have both:

```text
Origin: END_TO_END_VERIFIED
Gateway: ATTESTED
```

The origin authentication remains valid across transports as long as the signed content is preserved.

## 11C. MeshHub-aware and legacy clients

MeshHub SHOULD support both legacy/native clients and MeshHub-aware clients.

### 11C.1 Legacy/native client

A normal MeshCore or other network client sends a native message.

MeshHub may normalize, route and bridge it, but its origin trust remains limited to the evidence provided by the source network.

### 11C.2 MeshHub-aware client

A MeshHub-aware client can create an authenticated MeshHub message before transport.

Such a client MAY be:

- a dedicated MeshHub application
- a gateway-side client with access to a user's identity key
- firmware with MeshHub envelope support
- another trusted signing component

MeshHub MUST distinguish signing by the actual origin identity from signing by a gateway.

A gateway signature alone MUST NOT create `END_TO_END_VERIFIED` origin trust.

## 11D. Architectural consequence

The identity architecture is:

```text
Application / client
        |
        v
MeshHub Identity + Trust
        |
        v
MeshHub message / compact envelope
        |
        v
Transport adapter
        |
        v
MeshCore / Meshtastic / RNS / APRS / MQTT / ...
```

On receive:

```text
Transport
    |
    v
Adapter
    |
    v
Normalization
    |
    v
MeshHub Core
  +-- Identity
  +-- Trust
  +-- Routing
  +-- Deduplication
  +-- Bridging
```

Transport-specific adapters SHOULD expose available network identity evidence to MeshHub Core.

The Trust layer decides what verification level that evidence supports.

Adapters MUST NOT promote a claimed display name to a verified MeshHub identity.

## 12. Gateway identity

Gateways SHOULD have their own cryptographic identity.

Example:

```text
gateway:node01
```

A gateway MAY sign an attestation stating:

```text
Gateway node01 received message X
from network Y
at timestamp Z.
```

Gateway attestation proves what the gateway observed. It does NOT prove that an unverified claimed sender authored the message.

## 13. Bridging rules

Consider:

```text
MeshCore
   |
MeshHub Praha
   |
Reticulum
   |
MeshHub Utopia
   |
Meshtastic
```

The following fields SHOULD remain stable across bridges:

```text
message id
logical origin
logical target
payload
origin signature
```

Transport metadata MAY change or grow.

```json
{
  "trace": [
    "meshcore",
    "gateway:site-a",
    "reticulum",
    "gateway:site-b",
    "meshtastic"
  ]
}
```

## 14. Identity preservation

A gateway MUST NOT convert an unverified sender into a verified sender.

Incoming:

```text
User1212: Hello
```

Correct internal representation:

```json
{
  "claimed": {
    "display_name": "User1212"
  },
  "verified": null
}
```

If forwarded to another network, the unverified status MUST remain visible.

Example:

```text
[User1212 via MeshCore] Hello
```

## 15. Replay protection

Signed messages SHOULD contain:

```text
message_id
created_at
expires_at
nonce
```

MeshHub nodes SHOULD maintain a replay cache.

First delivery:

```text
signature: valid
message_id: unseen
ACCEPT
```

Repeated delivery:

```text
signature: valid
message_id: already seen
DROP or mark duplicate
```

Security-sensitive operations MUST reject expired messages.

## 16. Duplicate detection and bridge loops

Every MeshHub message MUST have a globally unique message identifier.

Recommended:

```text
UUIDv7
```

Gateways SHOULD maintain a recent-message cache.

Example loop:

```text
MeshCore
    |
 MeshHub A
    |
Meshtastic
    |
 MeshHub B
    |
MeshCore
```

If MeshHub A receives the same `message_id` again:

```text
DROP: already processed
```

Messages MAY additionally include `hop_count` and `trace`. A configurable maximum hop count SHOULD exist.

## 17. Key discovery

Possible public key discovery mechanisms:

- QR code
- direct exchange
- local configuration
- introduction by trusted identity
- trusted directory
- transport-specific discovery

Automatic discovery MUST NOT imply automatic trust.

## 18. Trust model

MeshHub v1 SHOULD use decentralized local trust.

Suggested trust states:

```text
unknown
seen
trusted
verified
revoked
```

Example:

```yaml
identities:
  "mh:7f3a91c8...":
    alias: "@panxyz"
    trust: verified
```

A global identity authority is NOT required.

## 19. Device keys

Each device SHOULD use a unique key.

```text
mh:7f3a91c8...
  |
  +-- phone
  +-- notebook
  +-- lilygo-01
```

A compromised device can then be revoked independently.

## 20. Key revocation

Revocation records SHOULD contain:

```text
device key id
revocation timestamp
reason
signature of parent identity
```

Messages signed by revoked device keys SHOULD be rejected after the effective revocation time.

## 21. Root identity

A logical identity MAY have a long-lived root key. The root key SHOULD normally remain offline. It MAY sign device keys.

```text
Root identity
  |
  +-- signs phone key
  +-- signs notebook key
  +-- signs radio key
```

Root identities are OPTIONAL in v1. Simple installations MAY initially use a single identity key.

## 22. Identity recovery

Future versions SHOULD define recovery mechanisms.

Candidates:

- offline recovery key
- multi-signature recovery
- trusted recovery contacts
- organisation recovery authority

Recovery is outside the scope of v0.1.

## 23. Legacy and unsigned transports

Some transports cannot carry a complete MeshHub envelope.

Examples:

- APRS
- small LoRa packets
- legacy gateways
- plain text channels

MeshHub MAY use compact identity references, gateway attestations, transport-specific metadata or unsigned forwarding.

Identity confidence MUST NOT be silently upgraded.

## 24. Privacy

MeshHub SHOULD avoid leaking stable global identities unnecessarily.

A user MAY use different public aliases on different networks.

```text
MeshHub identity:
  mh:7f3a91c8...

Local mappings:
  MeshCore -> panxyz
  APRS -> <CALLSIGN>-7
  Matrix -> @foo:example.org
```

Whether these identities are publicly linked MUST be configurable.

## 25. Security-sensitive message classes

Verification requirements MAY depend on message type.

```text
chat:
  unverified allowed

routing announcement:
  network-verified preferred

device control:
  verified required

gateway administration:
  verified + authorised required
```

Identity verification and authorisation are separate concepts.

A verified user is not automatically authorised to control a device.

## 26. Initial cryptographic recommendation

Initial candidate:

```text
signature: Ed25519
hash: SHA-256
message ID: UUIDv7
```

Algorithm agility MUST be preserved.

The identity namespace MUST NOT depend permanently on one algorithm.

## 27. Current MeshCore adapter behaviour

Current MeshHub prototypes receive Public messages such as:

```text
User1212: Brno - Sparta 3:1
```

The current parser extracts:

```json
{
  "sender": "User1212"
}
```

This is NOT an authenticated identity.

The future identity-aware representation SHOULD instead be:

```json
{
  "origin": {
    "claimed": {
      "display_name": "User1212"
    },
    "verified": null,
    "verification": "unverified"
  }
}
```

This change SHOULD happen before identity-aware TX routing is implemented.

## 28. Open questions

### Q1. Identity namespace

Should logical identity IDs be derived from public key fingerprints, random stable IDs, or another method?

Current proposal: stable ID derived from public key material, but the algorithm should not appear directly in the namespace.

### Q2. Signature transport

How should signatures be transported on small LoRa payloads?

Candidates:

- complete signature per message
- session-based verification
- detached signature
- signature batching
- gateway-only attestation
- compact transport encoding

Unresolved.

### Q3. Canonical encoding

CBOR or canonical JSON?

Initial preference: Canonical CBOR.

### Q4. Alias uniqueness

Should aliases be globally unique?

Proposal: NO. Aliases are human-readable labels only.

### Q5. Global identity directory

Should MeshHub operate a global searchable identity service?

Proposal: NO for v1. Identity discovery remains decentralized.

### Q6. Root identities

Should offline root keys be mandatory?

Proposal: NO. Supported and recommended for advanced deployments, but not mandatory.

### Q7. Gateway attestations

Should all gateways sign transport attestations?

Proposal: optional initially, supported by the protocol.

### Q8. Bridging unsigned messages

Should unverified messages be bridged?

Proposal: configurable.

```yaml
routing:
  bridge_unverified: true
```

Their verification status MUST remain `unverified`.

## 29. Implementation milestones

### Identity M1

Replace:

```text
sender: "User1212"
```

with:

```json
{
  "origin": {
    "claimed": {
      "display_name": "User1212"
    },
    "verified": null,
    "verification": "unverified"
  }
}
```

No cryptography yet.

M1 MUST preserve the distinction between claimed identity, network-derived evidence, MeshHub end-to-end verification and gateway attestation.

### Identity M2

Add `message_id`, `created_at`, `hop_count` and `trace`. Implement duplicate detection.

### Identity M3

Introduce MeshHub identity keys and message signatures.

### Identity M4

Introduce device keys and revocation.

### Identity M5

Introduce logical aliases `@user` and `#group` and identity-aware routing.

### Identity M6

Introduce gateway identities and attestations.

## 30. Fundamental rule

MeshHub MUST always be able to answer two different questions:

```text
Who does this message CLAIM to be from?
```

and:

```text
What identity can MeshHub PROVE this message came from?
```

These answers MUST never be silently treated as equivalent.
