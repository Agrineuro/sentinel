# Asset Model Specification

> Everything Sentinel understands is represented as an Asset.

Version: 1.0 (Draft)

---

# Purpose

The Asset Model defines how Sentinel represents infrastructure.

Rather than treating every technology differently, Sentinel creates a standardized representation called an Asset.

Assets provide a common language between connectors, events, artificial intelligence, automations, dashboards, plugins, and users.

The Asset Model is the foundation of Sentinel's Digital Twin architecture.

---

# Philosophy

Infrastructure consists of many different technologies.

Servers.

Virtual machines.

Containers.

Switches.

Storage.

Sensors.

People.

Buildings.

Cloud resources.

Applications.

Instead of building special logic for every technology, Sentinel represents them all as Assets.

Every Asset follows the same architectural model.

---

# What Is An Asset?

An Asset is any identifiable object that Sentinel can understand, monitor, or interact with.

Examples include:

- Physical Server
- Virtual Machine
- Container
- Switch
- Router
- Firewall
- UPS
- PDU
- Storage Pool
- Dataset
- Volume
- Kubernetes Cluster
- Camera
- Door Sensor
- HVAC Unit
- ESP32
- Raspberry Pi
- Linux Host
- Windows Host
- Optical Shelf
- Optical Card
- Optical Port
- Circuit
- Building
- Rack
- Cloud Instance
- User
- Team
- Organization

Assets are not limited to hardware.

Anything meaningful within an environment may become an Asset.

---

# Asset Identity

Every Asset must have a unique identity.

Example

```json
{
  "asset_id": "asset_srv_utility01",
  "asset_type": "linux_server",
  "display_name": "Utility VM",
  "organization": "Home",
  "site": "Primary Rack"
}
```

Asset IDs should never change.

Display names may change.

---

# Asset Types

Assets belong to a type.

Examples:

Infrastructure

- Server
- VM
- Container
- Storage
- Network Device
- UPS
- Rack

Software

- Service
- Application
- Database
- API
- Workflow

Environment

- Building
- Room
- Site
- Data Center

Identity

- User
- Group
- Team
- Organization

Logical

- VLAN
- Circuit
- VPN
- Backup Job

Custom

Users may define additional Asset Types.

---

# Asset State

Every Asset has a current state.

Examples:

- Online
- Offline
- Starting
- Stopping
- Degraded
- Healthy
- Warning
- Critical
- Maintenance
- Unknown

State should represent current operational status.

---

# Asset Health

Health is independent from state.

Example

Server

State

Online

Health

Warning

Reason

High CPU temperature

Health should be determined through policies and telemetry.

---

# Asset Capabilities

Every Asset exposes capabilities.

Examples

Linux Server

- SSH
- Files
- Services
- Processes
- Packages

UPS

- Battery
- Runtime
- Load
- Temperature

Camera

- Video
- Motion Detection
- Snapshot

Capabilities allow Sentinel to interact with different assets consistently.

---

# Asset Relationships

Assets do not exist in isolation.

Relationships provide context.

Examples:

```text
Rack

contains

Server

Server

hosts

VM

VM

runs

Docker

Docker

hosts

Container

Container

uses

Database

Database

stored on

TrueNAS

TrueNAS

connected to

Switch
```

Relationship types include:

- Contains
- Connected To
- Hosts
- Uses
- Depends On
- Managed By
- Owned By
- Located In
- Monitors
- Protects
- Backs Up

Relationships form the foundation of the Knowledge Engine.

---

# Asset Ownership

Assets may have owners.

Examples:

- User
- Team
- Department
- Organization

Ownership allows notifications, permissions, maintenance, and reporting.

---

# Asset Location

Assets may have physical or logical locations.

Examples:

Physical

- Rack
- Building
- Room
- GPS

Logical

- Cluster
- Site
- VLAN
- Cloud Region

---

# Asset Metadata

Assets may contain metadata.

Examples:

- Vendor
- Model
- Serial Number
- Firmware
- BIOS
- Purchase Date
- Warranty Expiration
- Operating System
- Kernel
- IP Address
- MAC Address

Metadata should remain extensible.

---

# Asset History

Assets should retain historical information.

Examples:

- Firmware updates
- Reboots
- Configuration changes
- Ownership changes
- Health history
- Maintenance
- Failures

History enables AI reasoning and trend analysis.

---

# Asset Policies

Policies define expected behavior.

Examples:

- Maintenance window
- Backup schedule
- Patch cadence
- Allowed commands
- Required encryption
- Health thresholds

Policies should be inherited where appropriate.

---

# Digital Twin

Every Asset has a Digital Twin.

The Digital Twin is Sentinel's internal representation of that Asset.

The Digital Twin contains:

- Current State
- Desired State
- Historical State
- Capabilities
- Relationships
- Events
- Policies
- Ownership
- Health
- Metadata

The Digital Twin exists even if the physical Asset is temporarily unavailable.

---

# Asset Discovery

Connectors should discover Assets automatically whenever possible.

Discovery should include:

- Identification
- Capabilities
- Metadata
- Relationships
- Current State

Users should not need to manually define infrastructure that can be discovered.

---

# Asset Lifecycle

Every Asset follows a lifecycle.

```text
Discovered

↓

Identified

↓

Enriched

↓

Monitored

↓

Maintained

↓

Archived

↓

Removed
```

Historical information should remain available after removal when appropriate.

---

# Asset Events

Assets generate events.

Examples:

- Asset discovered
- Asset removed
- Asset online
- Asset offline
- Asset degraded
- Asset updated
- Asset moved
- Asset ownership changed

Assets should never directly execute actions.

They publish state changes.

---

# Asset Security

Assets should define security boundaries.

Examples:

- Required permissions
- Allowed operations
- Credential requirements
- Sensitive metadata
- Classification

Security policies should be evaluated before actions are executed.

---

# Asset Intelligence

Artificial Intelligence should reason about Assets rather than raw devices.

Example

Instead of:

"CPU is 96%."

Sentinel understands:

"The virtualization host supporting six production virtual machines has exceeded its normal CPU utilization for 45 minutes."

Context transforms telemetry into knowledge.

---

# Asset Extensibility

Users and plugin developers should be able to create custom Asset Types.

Examples:

- Telescope
- CNC Machine
- Amateur Radio
- Weather Station
- Solar Inverter
- Aquarium Controller

Sentinel should remain adaptable to future technologies.

---

# Design Rules

1. Everything meaningful is an Asset.
2. Assets have unique identities.
3. Assets expose capabilities.
4. Assets have relationships.
5. Assets maintain history.
6. Assets generate events.
7. Assets follow policies.
8. Assets support permissions.
9. Assets remain extensible.
10. Every Asset has a Digital Twin.

---

# Long-Term Vision

The Asset Model transforms infrastructure into a connected knowledge graph.

Rather than monitoring isolated devices, Sentinel understands an entire environment as a living ecosystem of interconnected Assets.

This shared understanding enables intelligent automation, explainable AI, enterprise-scale operations, and a consistent user experience regardless of infrastructure size or complexity.
