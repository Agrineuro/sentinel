# Sentinel

## The Open Infrastructure Operating Environment

> **Build a home for your digital world.**

## Quick start with Docker

Requirements: Docker Engine and the Docker Compose plugin.

    git clone https://github.com/Agrineuro/sentinel.git
    cd sentinel
    ./scripts/install-docker.sh

Open http://localhost:8080 and create the first administrator account. The installer creates a private `.env` with the vault encryption key; database data is kept in a named Docker volume.

For LAN access, updates, backups, restore, and security guidance, see [Docker deployment](docs/DOCKER_DEPLOYMENT.md).

---

# The Sentinel Manifesto

Infrastructure has become fragmented.

Every platform has its own dashboard.

Every vendor has its own interface.

Every device speaks a different language.

Every team builds another silo.

As our environments become more powerful, they also become more complicated.

The result is that people spend more time managing infrastructure than benefiting from it.

**Sentinel exists to change that.**

Not by replacing the technologies you already trust.

By understanding them.

By connecting them.

By giving them a common language.

By transforming isolated systems into one intelligent operating environment.

---

# What Is Sentinel?

Sentinel is an **open-source Infrastructure Operating Environment**.

It unifies infrastructure, automation, artificial intelligence, security, operational knowledge, and human interaction into a single extensible platform.

Sentinel is designed around one simple idea:

> **Infrastructure should adapt to people—not the other way around.**

Whether you're managing:

* an ESP32 sensor
* a Raspberry Pi
* a family homelab
* a virtualization cluster
* a telecommunications transport network
* a manufacturing facility
* an enterprise data center
* cloud infrastructure

Sentinel should provide the same consistent operational experience.

---

# What Sentinel Is Not

Sentinel is **not** another:

* Dashboard
* Chatbot
* Monitoring tool
* SSH client
* Container manager
* Hypervisor interface
* Home automation platform
* Network management system

Those tools already exist.

Many of them are excellent.

Sentinel is designed to sit **above** them.

It provides the intelligence, context, and operational environment that connects them into one cohesive platform.

---

# Why Sentinel Exists

Modern infrastructure spans dozens of technologies.

Examples include:

* Compute
* Storage
* Networking
* Virtualization
* Containers
* Artificial Intelligence
* Security
* Identity
* Automation
* Smart Homes
* Industrial Systems
* Telecommunications
* Cloud Services

Each platform solves its own problem.

Very few understand how those systems relate to one another.

Sentinel exists to become the operational layer that understands infrastructure as a whole.

---

# Core Design Principles

Sentinel is built around a small set of architectural principles.

* Software should adapt to people.
* Infrastructure should remain vendor-neutral.
* Native protocols should be preferred over proprietary agents.
* Security should be built into the foundation.
* Artificial intelligence should assist rather than replace human decision-making.
* Infrastructure should become more understandable over time.
* Complexity should remain optional.
* The same architecture should support both beginners and experts.
* The same platform should scale from a single device to enterprise deployments.

These principles are expanded throughout the project specifications.

---

# Core Architecture

Sentinel is built as a collection of independent systems working together.

```text
Users
    │
Workspaces
    │
Intelligence Layer
    │
Knowledge Engine
    │
Event Engine
    │
Automation Engine
    │
Connector Framework
    │
Infrastructure Assets
    │
Protocols
```

Each layer has a single responsibility.

This architecture allows Sentinel to remain modular, scalable, and extensible.

---

# Universal Connector Framework

Sentinel is designed around protocols rather than products.

Instead of supporting individual applications one at a time, Sentinel communicates using native protocols whenever possible.

Examples include:

* SSH
* WinRM
* REST
* MQTT
* SNMP
* WebSocket
* Serial
* TL1
* NETCONF
* gNMI
* Modbus
* OPC UA

Product-specific connectors are then built on top of these protocols.

This architecture allows Sentinel to communicate with everything from embedded IoT devices to enterprise infrastructure.

---

# Infrastructure Assets

Sentinel does not simply manage devices.

It models **Assets**.

An Asset may represent:

* A server
* A virtual machine
* A container
* A switch
* A storage pool
* A UPS
* A camera
* A service
* A sensor
* A circuit
* A building
* A cloud resource
* A telecommunications system

Each asset contains:

* Identity
* Capabilities
* Current state
* Historical state
* Relationships
* Events
* Policies
* Ownership
* Health

Together these form Sentinel's understanding of your environment.

---

# Knowledge Before Intelligence

Artificial Intelligence is only one part of Sentinel.

Before AI can reason, Sentinel builds knowledge.

It learns:

* What assets exist
* How they relate
* Normal operating behavior
* Historical trends
* Policies
* Maintenance windows
* Dependencies

Artificial Intelligence then reasons from that knowledge.

This allows Sentinel to explain recommendations rather than simply generate them.

---

# Event-Driven by Design

Everything meaningful becomes an event.

Examples include:

* Device connected
* Service restarted
* Backup completed
* Firmware available
* Link failure
* Camera motion detected
* High temperature
* Authentication failure
* AI recommendation created

Events become the heartbeat of the platform.

They drive:

* Automation
* Dashboards
* Notifications
* Intelligence
* Audit Logs
* Workflows

---

# Security by Design

Security is not an optional feature.

Sentinel is built around:

* Zero Trust principles
* Role-Based Access Control
* Secure Credential Vault
* Audit Logging
* Encrypted Secrets
* Plugin Sandboxing
* Policy Enforcement
* Explainable AI Actions

Security should protect beginners while remaining powerful enough for enterprise environments.

---

# Designed for Every Scale

Sentinel should never require users to migrate to another platform as their infrastructure grows.

The same architecture should support:

* Individual makers
* Home users
* Homelabs
* Small businesses
* Universities
* Research organizations
* Telecommunications providers
* Manufacturing facilities
* Enterprise environments
* Multi-site deployments
* Data centers

Growth should expand capability—not require replacement.

---

# Project Status

Sentinel is currently in the architecture and design phase.

The project is intentionally being designed before implementation.

By establishing clear specifications first, we aim to build a platform that remains maintainable, extensible, and community-driven for years to come.

This is the best time to contribute ideas and help shape the future of the project.

---

# Project Specifications

Sentinel is specification-driven.

Current specifications include:

* Foundation
* Architecture
* Design Principles
* Security Architecture
* Connector Specification

Additional specifications covering events, plugins, APIs, workflows, intelligence, user interfaces, deployment, and data models will be added as the platform evolves.

---

# Contributing

Sentinel is built in the open.

Whether you are:

* a software engineer
* a systems administrator
* a network engineer
* a designer
* a technical writer
* a security researcher
* an infrastructure architect
* or simply someone with ideas

your contributions are welcome.

Please read `CONTRIBUTING.md` before opening issues or submitting pull requests.

---

# Roadmap

Development milestones are documented in `ROADMAP.md`.

The immediate goal is not rapid feature development.

The immediate goal is building a platform whose architecture can support the next decade of innovation.

---

# License

Sentinel is open source.

See `LICENSE` for licensing information.

---

# Vision

We believe infrastructure deserves a better operating experience.

One that learns.

One that adapts.

One that explains.

One that grows alongside its users.

One that respects privacy.

One that embraces openness.

One that connects rather than replaces.

Our goal is not simply to build another infrastructure management platform.

Our goal is to build the operating environment where modern infrastructure comes alive.

---

## One Platform.

## Infinite Infrastructure.

### Build a home for your digital world.
