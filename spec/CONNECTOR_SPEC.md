# Connector Specification

> Connectors are the bridge between Sentinel and the outside world.

Version: 1.0 (Draft)

---

# Purpose

Sentinel is designed to communicate with infrastructure rather than replace it.

Rather than requiring proprietary agents or vendor-specific implementations, Sentinel communicates through standardized protocols and product-specific integrations called **Connectors**.

Every interaction between Sentinel and an external system should occur through a connector.

The Connector Framework exists to provide a consistent, secure, and extensible way to communicate with any supported technology.

---

# Philosophy

Sentinel follows a simple philosophy:

**If it can communicate, Sentinel should be able to understand it.**

This includes:

* Embedded devices
* Home automation platforms
* Servers
* Storage appliances
* Enterprise networking equipment
* Industrial equipment
* Legacy telecom systems
* Cloud platforms
* Future technologies

Sentinel should never be limited by vendor.

---

# Connector Hierarchy

Not every connector represents a product.

Sentinel supports multiple connector types.

```text
Protocol Connector
        │
        ├── SSH
        ├── SNMP
        ├── MQTT
        ├── REST
        ├── Serial
        ├── Telnet
        ├── WinRM
        ├── WebSocket
        ├── TL1
        ├── NETCONF
        ├── gNMI
        └── Modbus

                │

Product Connector

Proxmox

TrueNAS

Linux

Windows

Docker

Home Assistant

ESPHome

Cisco IOS

Juniper JunOS

Fujitsu 6500

Ciena 6500

Synology

UniFi

pfSense

OPNsense

Future Products
```

Product connectors should use one or more protocol connectors whenever possible.

---

# Connector Responsibilities

A connector is responsible for:

* Authentication
* Communication
* Discovery
* State retrieval
* Command execution
* Event generation
* Telemetry collection
* Error handling
* Capability reporting

A connector should not contain business logic.

Business logic belongs to Sentinel Core.

---

# Connector Lifecycle

Every connector should follow the same lifecycle.

```text
Install

↓

Configure

↓

Authenticate

↓

Discover

↓

Report Capabilities

↓

Operate

↓

Monitor

↓

Disconnect
```

This predictable lifecycle allows every connector to behave consistently.

---

# Capabilities

Instead of exposing product-specific features, connectors expose capabilities.

Example:

Linux

Capabilities

* Terminal
* Files
* Services
* Packages
* Logs
* Users
* Processes

Windows

Capabilities

* PowerShell
* Services
* Event Viewer
* Registry
* Files
* Updates

Docker

Capabilities

* Containers
* Images
* Volumes
* Networks
* Logs

Sentinel interacts with capabilities rather than products whenever practical.

---

# Protocol-First Design

Protocol support should come before product support.

Examples include:

* SSH
* REST
* MQTT
* SNMP
* Serial
* WebSocket
* WinRM
* WMI
* TL1
* NETCONF
* gNMI
* Modbus
* BACnet
* OPC UA

This enables Sentinel to support thousands of products with a relatively small number of protocol implementations.

---

# Discovery

Connectors should discover as much information as possible automatically.

Examples:

Linux

* Distribution
* Kernel
* CPU
* Memory
* Network Interfaces
* Services
* Installed Packages

Proxmox

* Nodes
* Virtual Machines
* LXC Containers
* Storage
* Backups

Network Switch

* Interfaces
* VLANs
* Neighbors
* Routing
* Firmware

Optical Transport

* Shelves
* Cards
* Ports
* Circuits
* Alarms
* Performance Metrics

Users should not have to manually build inventory whenever it can be discovered safely.

---

# Authentication

Connectors should never store credentials directly.

Credentials should always be requested from the Sentinel Credential Vault.

Supported authentication methods may include:

* Username and Password
* SSH Keys
* Certificates
* API Tokens
* OAuth
* SNMPv3
* Kerberos
* LDAP
* Active Directory

The connector should receive temporary access to the required credential.

---

# Read and Write Modes

Every connector should declare its operating mode.

Examples:

Read Only

Suitable for:

* Monitoring
* Inventory
* Reporting

Read / Write

Suitable for:

* Configuration
* Updates
* Automation
* Recovery

Users should understand exactly what a connector is capable of before enabling write access.

---

# Safety

Potentially destructive operations should require explicit confirmation.

Examples:

* Delete
* Factory Reset
* Format
* Firmware Upgrade
* Mass Configuration
* Service Shutdown

AI-generated actions should also respect these requirements.

---

# Event Integration

Connectors should emit events rather than directly triggering automation.

Examples:

* Device Online
* Device Offline
* High Temperature
* Authentication Failure
* Backup Completed
* Link Down
* Service Restarted
* New Firmware Available

Sentinel's Event Engine decides what should happen next.

---

# Telemetry

Connectors should expose telemetry whenever available.

Examples:

* CPU Usage
* Memory Usage
* Storage Usage
* Power Consumption
* Fan Speed
* Temperature
* Network Throughput
* Interface Errors
* Optical Power
* Signal Quality
* UPS Runtime

Telemetry should use consistent units whenever practical.

---

# Command Execution

Some systems expose structured APIs.

Others expose only a command line.

Sentinel should support both.

Example:

Linux

SSH

```text
systemctl restart docker
```

Cisco

SSH

```text
show interface status
```

Fujitsu

TL1

```text
RTRV-ALM
```

Ciena

CLI

```text
rtrv-alm-all
```

The connector should translate product-specific syntax into standardized Sentinel capabilities whenever possible.

---

# Legacy Systems

Sentinel should support legacy systems whenever technically feasible.

Examples include:

* Telnet
* Serial Console
* RS-232
* TL1
* SNMPv1
* SNMPv2c

Support for legacy systems should not reduce the security of modern deployments.

Users should be warned when insecure protocols are enabled.

---

# AI Integration

Artificial Intelligence should never communicate directly with external systems.

Instead:

```text
AI

↓

Sentinel Core

↓

Connector

↓

Target Device
```

This ensures:

* Permission validation
* Audit logging
* Policy enforcement
* Explainability

---

# Plugin Integration

Most connectors should be installable through the Plugin Framework.

This allows the community to develop connectors independently of Sentinel Core.

Examples include:

* New vendor support
* New industrial protocols
* Specialized hardware
* Experimental integrations

---

# Testing Requirements

Every connector should support automated validation where possible.

Testing should verify:

* Authentication
* Capability reporting
* Error handling
* Event generation
* Security
* Version compatibility

Community-developed connectors should meet the same quality standards as official connectors.

---

# Performance

Connectors should minimize unnecessary communication.

Examples:

* Cache inventory when appropriate.
* Stream events instead of polling when possible.
* Batch requests where supported.
* Respect rate limits.
* Avoid excessive resource consumption.

Efficiency should be considered part of connector quality.

---

# Documentation

Every connector should include:

* Purpose
* Supported versions
* Supported capabilities
* Authentication methods
* Required permissions
* Limitations
* Examples
* Troubleshooting guidance

Users should never need to inspect source code to understand how a connector behaves.

---

# Future Vision

The Connector Framework is intended to become one of Sentinel's defining strengths.

Whether managing an ESP32 sensor, a Linux server, a virtualization cluster, a telecom transport platform, or an enterprise datacenter, every system should integrate through the same consistent architecture.

The goal is not simply to support more devices.

The goal is to create a universal language between Sentinel and infrastructure of every size, age, and complexity.

If a system can communicate, Sentinel should be able to understand it.
