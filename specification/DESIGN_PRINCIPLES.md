# Design Principles

> Sentinel is not another dashboard.
>
> Sentinel is an operating environment for infrastructure.

---

## Purpose

This document defines the design principles that guide Sentinel.

These principles should influence architecture, development, user experience, security, community decisions, and long-term project direction.

When there is uncertainty, Sentinel should return to these principles.

---

## 1. Software Should Adapt to People

Sentinel exists because modern infrastructure often forces people to adapt to tools.

Sentinel should reverse that relationship.

The platform should learn how users work, understand their environments, and present information in ways that feel natural, useful, and personal.

---

## 2. Infrastructure Agnostic

Sentinel should never assume the size, type, vendor, or purpose of the infrastructure it manages.

Sentinel should work across:

- ESP32 devices
- Linux systems
- Windows systems
- Virtual machines
- Containers
- Smart homes
- Network devices
- Storage platforms
- Telecom systems
- Industrial systems
- Data centers
- Cloud infrastructure
- Future systems not yet imagined

A homelab and an enterprise data center should use the same architectural foundation.

---

## 3. Native Protocols First

Sentinel should communicate using protocols systems already support whenever possible.

Examples include:

- SSH
- WinRM
- REST
- WebSocket
- MQTT
- SNMP
- TL1
- NETCONF
- gNMI
- Serial
- Telnet
- Modbus

Agents may enhance Sentinel, but they should not be required for basic operation.

---

## 4. Assets, Not Just Devices

Sentinel should model the world as assets.

An asset may be:

- A server
- A VM
- A container
- A switch
- A service
- A camera
- A sensor
- A circuit
- A storage pool
- A software application
- A person-defined object

Assets have identity, state, capabilities, relationships, history, ownership, and policies.

---

## 5. Build a Digital Twin

Sentinel should maintain an internal representation of each asset.

This representation should include:

- Current state
- Expected state
- Historical behavior
- Relationships
- Events
- Health
- Policies
- Capabilities

The digital twin allows Sentinel to reason about infrastructure even when individual systems are offline or temporarily unreachable.

---

## 6. Events Over Polling

Sentinel should prefer event-driven design.

Everything meaningful should become an event:

- Device online
- Device offline
- Backup completed
- Container restarted
- Interface down
- User logged in
- Camera detected motion
- AI recommendation created
- Automation executed

Events allow Sentinel to understand change, not just display state.

---

## 7. Knowledge Before Intelligence

Artificial intelligence is only useful when it has context.

Sentinel should build a knowledge layer that understands:

- Assets
- Relationships
- History
- Ownership
- Normal behavior
- Maintenance windows
- Dependencies
- Policies

The AI should reason from knowledge, not raw data alone.

---

## 8. AI Assists, Humans Decide

AI should help users understand, decide, and act.

AI should not bypass permissions, policies, approvals, or audit logging.

Every AI action should be explainable.

Every risky AI action should be reviewable.

The user remains in control.

---

## 9. Secure by Default

Security is not optional.

Sentinel should assume:

- Networks may be hostile.
- Credentials may be sensitive.
- Plugins may be risky.
- Automation may cause damage.
- AI may make mistakes.

Secure defaults should protect beginners while allowing experts to build advanced environments.

---

## 10. Progressive Complexity

Sentinel should be easy to start and deep enough to grow.

A beginner should be able to install Sentinel and see useful information quickly.

A power user should be able to customize dashboards, connectors, workflows, policies, automations, and personality.

The same platform should serve both.

---

## 11. Plugin Before Modification

Sentinel should favor extension over modification.

New features should be implemented as plugins, connectors, workflows, or UI extensions whenever practical.

This keeps the core stable and allows the community to expand the platform.

---

## 12. API First

Every meaningful capability should be available through a documented API.

The web UI, mobile app, CLI, voice interface, automations, and third-party tools should all use the same platform capabilities.

---

## 13. Explain Everything

Sentinel should help users understand their environment.

When something happens, Sentinel should answer:

- What happened?
- When did it happen?
- What caused it?
- What was affected?
- What changed?
- What can be done?
- What are the risks?

Understanding is as important as control.

---

## 14. Scale Without Redesign

Sentinel should be useful for one device and capable of growing to thousands.

Architecture should support:

- Single-user deployments
- Families
- Homelabs
- Small businesses
- Enterprises
- Multiple sites
- Data centers
- Multi-tenant environments

Scaling should not require replacing the platform.

---

## 15. Build a Home for the Digital World

Sentinel should not feel like a collection of tools.

It should feel like an environment.

A place where infrastructure, automation, intelligence, security, personality, and people come together.

The goal is not simply to manage systems.

The goal is to make infrastructure feel alive, understandable, and personal.
