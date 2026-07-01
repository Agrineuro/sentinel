# Knowledge Engine Specification

> Data becomes information. Information becomes knowledge. Knowledge enables intelligence.

Version: 1.0 (Draft)

---

# Purpose

The Knowledge Engine is responsible for transforming raw infrastructure data into structured operational knowledge.

Connectors collect information.

Events report changes.

Assets model infrastructure.

The Knowledge Engine connects everything together.

It provides Sentinel with context, memory, relationships, history, and understanding.

Artificial Intelligence should reason from the Knowledge Engine rather than directly from connectors or telemetry.

---

# Philosophy

Infrastructure generates enormous amounts of data.

CPU utilization.

Disk usage.

Temperatures.

Logs.

Alerts.

Configuration.

Relationships.

By themselves, these are only facts.

The Knowledge Engine turns facts into knowledge by understanding:

* Identity
* Relationships
* History
* Ownership
* Dependencies
* Normal behavior
* Policies
* Context

Knowledge allows Sentinel to answer questions rather than simply display numbers.

---

# Responsibilities

The Knowledge Engine is responsible for:

* Building the Digital Twin of every Asset
* Maintaining asset relationships
* Tracking historical state
* Understanding topology
* Recording dependencies
* Learning operational baselines
* Enriching events
* Providing context to AI
* Supporting automation decisions
* Supplying dashboards with meaningful information

---

# Inputs

Knowledge is built from many sources.

Examples include:

* Connector discovery
* Events
* Asset metadata
* Telemetry
* User input
* Policies
* Inventory
* Documentation
* Plugin data
* External APIs

Knowledge should continuously improve as additional information becomes available.

---

# Knowledge Graph

Sentinel maintains a graph of relationships.

Example:

```text
Organization
        │
        ├── Site
        │      │
        │      ├── Rack
        │      │      │
        │      │      ├── Server
        │      │      │      │
        │      │      │      ├── Virtual Machine
        │      │      │      │      │
        │      │      │      │      ├── Docker
        │      │      │      │      │      │
        │      │      │      │      │      ├── Container
        │      │      │      │      │      └── Database
```

Relationships become first-class knowledge.

---

# Context

Context answers questions such as:

* What is this?
* Who owns it?
* Where is it?
* What depends on it?
* What does it depend on?
* Is this normal?
* Has this happened before?
* What changed recently?
* Is maintenance scheduled?

Context transforms isolated data into operational understanding.

---

# Baselines

Sentinel should learn normal behavior.

Examples:

CPU:

Average: 14%

Peak: 32%

Memory:

Typical: 61%

Temperature:

Typical: 39°C

Network:

Average: 1.2 Gbps

AI can compare current behavior against learned baselines rather than fixed thresholds alone.

---

# Historical Knowledge

Knowledge should include history.

Examples:

* Firmware upgrades
* Configuration changes
* Ownership changes
* Hardware replacements
* Performance trends
* Failure history
* Maintenance records
* Incident timelines

History enables predictive reasoning.

---

# Topology

The Knowledge Engine should understand infrastructure topology.

Examples:

* Physical topology
* Network topology
* Virtualization topology
* Storage topology
* Service topology
* Dependency topology

Topology enables impact analysis.

---

# Dependency Modeling

Dependencies should be explicit.

Example:

```text
Immich

depends on

Docker

depends on

Ubuntu

depends on

Proxmox

depends on

Storage

depends on

UPS
```

Sentinel should understand cascading failures.

---

# Operational Memory

Sentinel should remember previous observations.

Examples:

* Repeated failures
* Successful repairs
* User preferences
* Maintenance history
* Seasonal patterns
* Performance trends

Memory improves recommendations over time.

---

# Event Enrichment

The Knowledge Engine enriches events.

Raw event:

```text
VM Offline
```

Enriched event:

```text
The VM "Immich" is offline.

This affects:

- Photo management
- Mobile uploads
- Facial recognition

Host:

Utility Server

Maintenance Window:

No

Severity:

High
```

---

# AI Context

Artificial Intelligence should request knowledge rather than raw data.

Example:

Instead of:

"What is CPU usage?"

The AI asks:

"What do I know about this Asset?"

The Knowledge Engine returns:

* Current state
* Historical behavior
* Dependencies
* Policies
* Related incidents
* Recent changes
* Owner
* Health

---

# Knowledge Confidence

Not all knowledge has equal confidence.

Sources may include:

* Direct observation
* User input
* Connector discovery
* Imported documentation
* AI inference

Confidence should be tracked where appropriate.

---

# Documentation Integration

Future versions may allow Sentinel to understand documentation.

Examples:

* Network diagrams
* Runbooks
* Architecture documents
* Standard operating procedures
* Wikis
* Manuals

This allows AI recommendations to reference organizational knowledge.

---

# Search

Knowledge should support semantic search.

Examples:

"What servers host Home Assistant?"

"What changed yesterday?"

"Which UPS protects this rack?"

"What systems depend on TrueNAS?"

Search should operate on knowledge, not only names.

---

# Privacy

Knowledge belongs to the organization.

Sensitive knowledge should respect:

* RBAC
* Policies
* Encryption
* Audit logging
* Data retention rules

---

# Scalability

The Knowledge Engine should support:

* Home deployments
* Multi-site organizations
* Enterprise infrastructure
* Large-scale asset graphs

Architecture should scale without redesign.

---

# Design Rules

1. Knowledge is built, not collected.
2. Relationships are first-class citizens.
3. Context is more valuable than raw data.
4. History improves intelligence.
5. Dependencies should be explicit.
6. Events enrich knowledge.
7. Knowledge enriches AI.
8. Users remain the owners of organizational knowledge.
9. Knowledge should be searchable.
10. The Digital Twin is the authoritative representation of an Asset.

---

# Long-Term Vision

The Knowledge Engine is Sentinel's memory.

Without it, Sentinel only reports what is happening.

With it, Sentinel understands why it is happening, what it affects, what has happened before, and what is likely to happen next.

Knowledge transforms infrastructure into an environment that can be understood, explained, and intelligently managed.
