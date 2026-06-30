# Architecture

> Sentinel is designed as a local-first, plugin-driven operating platform for self-hosted infrastructure.

---

## Overview

Sentinel is built around one core idea:

**Everything is a connector.**

Rather than hardcoding support for specific services, Sentinel communicates with systems through connectors, APIs, protocols, and optional agents.

This allows Sentinel to manage many types of environments while keeping the core platform stable.

---

## High-Level Layers

```text
Sentinel
├── Interface Layer
│   ├── Web UI
│   ├── Mobile UI
│   ├── Voice UI
│   └── API Clients
│
├── Personality Layer
│   ├── Themes
│   ├── Voice
│   ├── Tone
│   ├── Assistant behavior
│   └── User preferences
│
├── Intelligence Layer
│   ├── LLM providers
│   ├── Local models
│   ├── Memory
│   ├── Context
│   ├── Planning
│   └── Explanation engine
│
├── Automation Layer
│   ├── Events
│   ├── Rules
│   ├── Workflows
│   ├── Schedules
│   └── Actions
│
├── Integration Layer
│   ├── Connectors
│   ├── Plugins
│   ├── Credential vault
│   ├── Discovery
│   └── Protocol adapters
│
└── Infrastructure Layer
    ├── Linux
    ├── Windows
    ├── Proxmox
    ├── TrueNAS
    ├── Home Assistant
    ├── Docker
    ├── Cameras
    ├── Network devices
    └── Future systems
```

---

## Core Components

### Sentinel Core

The core coordinates the platform.

Responsibilities include:

* Authentication
* Authorization
* Configuration
* Plugin loading
* Connector registry
* Event routing
* API exposure
* Audit logging
* Credential access control

The core should remain small, stable, and predictable.

---

### Connectors

Connectors allow Sentinel to communicate with external systems.

Examples:

* SSH connector
* WinRM connector
* Proxmox connector
* TrueNAS connector
* Home Assistant connector
* Docker connector
* MQTT connector
* SNMP connector
* REST API connector

Connectors should expose capabilities in a consistent way.

For example, a Linux server and a Windows server may use different protocols, but both may expose:

* System status
* Services
* Files
* Logs
* Updates
* Commands
* Reboot actions

---

### Plugins

Plugins extend Sentinel.

A plugin may add:

* A connector
* Dashboard widgets
* Automation actions
* AI tools
* Voice commands
* Device types
* API routes
* Documentation
* UI panels

Plugins should be installable, removable, and upgradable without modifying the core platform.

---

### Optional Agent

Sentinel should not require an agent for basic management.

Native protocols should be used first.

Examples:

* Linux through SSH
* Windows through WinRM or OpenSSH
* Proxmox through API
* TrueNAS through API
* Home Assistant through API
* Docker through socket or API

An optional agent may be used for advanced features such as:

* Real-time telemetry
* Local event streaming
* Hardware sensors
* Offline buffering
* Faster file operations
* Secure reverse connections
* Remote networks

The agent should enhance Sentinel, not be required by it.

---

## Credential Vault

Sentinel may need to store credentials, tokens, SSH keys, API keys, and certificates.

Security requirements:

* Credentials must be encrypted at rest.
* Secrets must never be logged.
* Access must be permission-controlled.
* Every credential use should be auditable.
* Users must be able to rotate credentials.
* Users must be able to delete credentials permanently.

Sentinel should prefer least-privilege access wherever possible.

---

## API-First Design

Every feature should be available through the API.

The web interface should not contain special hidden capabilities.

This allows:

* Web UI
* Mobile apps
* CLI tools
* Voice interfaces
* Automations
* Third-party integrations

to all use the same platform.

---

## Event System

Sentinel should understand changes across the environment.

Examples:

* A VM goes offline.
* A Docker container crashes.
* A backup completes.
* A camera detects motion.
* Home Assistant changes state.
* Disk usage crosses a threshold.
* A security update becomes available.
* A user asks Sentinel to perform an action.

Events can trigger:

* Notifications
* Automations
* AI summaries
* Dashboard updates
* Logs
* Workflows
* User approval prompts

---

## Automation Engine

Automations should be clear, inspectable, and reversible when possible.

Example automation:

```text
When Docker updates are available:
1. Snapshot the VM.
2. Update one container.
3. Run health check.
4. Continue if healthy.
5. Roll back if failed.
6. Notify the user.
```

Automation should never hide risk from the user.

---

## Intelligence Layer

Artificial intelligence is part of Sentinel, but it is not the entire platform.

AI should help Sentinel:

* Explain system state
* Summarize events
* Recommend actions
* Generate automations
* Interpret logs
* Assist troubleshooting
* Personalize the user experience

AI actions should be transparent.

Sentinel should show:

* What action is being taken
* Why it is being taken
* What systems are affected
* Whether approval is required

---

## Personality System

Sentinel should allow users to shape how the platform feels.

Personality may include:

* Tone
* Voice
* Theme
* Dashboard style
* Notification style
* Assistant behavior
* Names for rooms, systems, and people
* Preferred level of technical detail

A user should be able to create a professional NOC, a friendly home assistant, a futuristic command center, or something entirely personal.

---

## Frontend

The frontend should prioritize clarity over complexity.

Initial UI goals:

* Dashboard
* Devices
* Services
* Automations
* Plugins
* Logs
* Settings

The frontend should consume the same public API available to other clients.

---

## Backend

The backend should provide:

* REST API
* WebSocket event stream
* Plugin registry
* Connector management
* Credential vault access
* Automation execution
* Audit logs
* User management

The backend should be modular and testable.

---

## Deployment

Sentinel should eventually support multiple deployment models.

Initial target:

* Docker Compose

Future targets:

* Bare metal Linux
* Proxmox LXC
* Kubernetes
* Home server appliance image
* Cloud-hosted relay mode
* Offline local-only mode

---

## Guiding Architectural Rules

1. Keep the core small.
2. Prefer connectors over hardcoded integrations.
3. Prefer native protocols before requiring agents.
4. Make every action auditable.
5. Make every automation explainable.
6. Make AI optional but powerful.
7. Make local operation the default.
8. Make cloud services optional.
9. Make the UI simple for beginners.
10. Make the platform deep enough for power users.

---

## Long-Term Vision

Sentinel should become the environment where self-hosted systems work together.

Not a replacement for existing tools.

A layer above them.

A place where infrastructure, automation, intelligence, and personality become one connected experience.
