# Organization Model Specification

> Infrastructure exists within organizations, not in isolation.

Version: 1.0 (Draft)

---

# Purpose

The Organization Model defines how Sentinel structures environments.

Whether Sentinel is deployed for a family homelab, a university, a managed service provider, or a global enterprise, the same organizational model should apply.

The Organization Model provides boundaries for:

* Assets
* Users
* Sites
* Policies
* Permissions
* Notifications
* Intelligence
* Automation
* Reporting

---

# Philosophy

Infrastructure belongs to people.

People belong to organizations.

Organizations contain environments.

Sentinel should understand these relationships.

The same architecture should support one user with one Raspberry Pi or thousands of users across multiple continents.

---

# Organizational Hierarchy

The recommended hierarchy is:

```text
Organization
        │
        ├── Sites
        │       │
        │       ├── Buildings
        │       │       │
        │       │       ├── Rooms
        │       │       │       │
        │       │       │       ├── Racks
        │       │       │       │       │
        │       │       │       │       ├── Assets
        │       │       │       │       │
        │       │       │       │       └── Sensors
```

Not every deployment requires every level.

Home users may only use:

Organization

↓

Assets

---

# Organization

The Organization is the highest logical boundary.

Examples:

Home

Small Business

School

Hospital

Research Lab

Telecommunications Provider

Cloud Tenant

Enterprise

Organizations isolate:

Users

Policies

Assets

Knowledge

Events

Notifications

Secrets

Automation

---

# Sites

Organizations may contain multiple Sites.

Examples:

Primary Home

Workshop

Office

Factory

Data Center

Branch Office

Cloud Region

Edge Site

Sites allow geographic organization.

---

# Buildings

Sites may contain Buildings.

Examples:

Office Building

Warehouse

House

Manufacturing Facility

Data Hall

Buildings improve navigation and reporting.

---

# Rooms

Buildings may contain Rooms.

Examples:

Server Room

Office

Garage

Lab

Closet

Living Room

Bedroom

Rooms are optional.

---

# Racks

Infrastructure may be organized into Racks.

Examples:

Rack A

Rack B

Network Rack

Storage Rack

Edge Cabinet

Rack awareness supports:

Power

Cooling

Cable Management

Capacity

Physical topology

---

# Assets

Assets belong somewhere.

Every Asset may reference:

Organization

Site

Building

Room

Rack

Location should always remain optional.

---

# Organizational Identity

Every organization has:

Organization ID

Display Name

Description

Time Zone

Locale

Branding

Default Policies

Default Roles

Default Notifications

Organizations remain isolated.

---

# Multi-Tenancy

Sentinel should support:

Single Organization

Multiple Organizations

Managed Service Providers

Hosted Environments

Organization isolation should be enforced throughout the platform.

---

# Ownership

Organizations own:

Assets

Secrets

Knowledge

Policies

Dashboards

Workflows

Reports

Events

Ownership defines administrative boundaries.

---

# Delegation

Organizations may delegate administration.

Examples:

Organization Owner

Site Administrator

Infrastructure Manager

Security Administrator

Storage Administrator

Network Administrator

Delegation should integrate with RBAC.

---

# Organization Metadata

Examples:

Industry

Contact Information

Maintenance Hours

Business Hours

Compliance Requirements

Languages

Regions

Metadata should remain extensible.

---

# Cross-Organization Isolation

Organizations should never share:

Secrets

Knowledge

Policies

Users (unless explicitly federated)

Events

Automation

Isolation should be enforced by Sentinel Core.

---

# Federation (Future)

Future versions may support:

Organization Federation

Shared Dashboards

Shared Assets

Shared Policies

Shared Connectors

Federation should remain optional.

---

# Design Rules

1. Organizations define security boundaries.
2. Assets belong to organizations.
3. Sites organize infrastructure.
4. Physical hierarchy is optional.
5. Isolation is mandatory.
6. Multi-tenancy should require no architectural changes.
7. Delegation should integrate with RBAC.
8. Knowledge belongs to organizations.
9. Policies inherit downward.
10. Organizations should remain extensible.

---

# Long-Term Vision

The Organization Model allows Sentinel to scale from a single household to globally distributed enterprises without changing its architectural foundation.

Organizations provide the context in which every Asset, Event, Policy, Workflow, and Intelligence decision exists.

Rather than treating infrastructure as isolated devices, Sentinel understands it as part of a larger operational environment owned and managed by people.
