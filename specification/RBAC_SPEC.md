# Role-Based Access Control (RBAC) Specification

> Identity defines who you are. Authorization defines what you can do.

Version: 1.0 (Draft)

---

# Purpose

The Role-Based Access Control (RBAC) system governs authorization throughout Sentinel.

Every action performed by a user, service, connector, automation, plugin, API client, or Intelligence Engine must be evaluated through RBAC before execution.

RBAC exists to ensure that every identity has only the permissions necessary to perform its intended function.

---

# Philosophy

Authentication answers:

Who are you?

Authorization answers:

What are you allowed to do?

Sentinel separates these responsibilities.

Identity is established first.

Authorization is evaluated second.

Policy is evaluated third.

Execution occurs only after all three succeed.

---

# Authorization Flow

```text
Authentication
        │
        ▼
Identity
        │
        ▼
RBAC
        │
        ▼
Policy Engine
        │
        ▼
Approval Engine
        │
        ▼
Execution
```

Every privileged operation follows this path.

---

# Identity Types

Sentinel recognizes multiple identity types.

Examples include:

* User
* Service Account
* API Client
* Connector
* Plugin
* Automation
* Workflow
* Intelligence Engine
* Notification Service
* External System

Everything capable of performing an action has an identity.

---

# Organizations

Organizations represent the highest security boundary.

Examples:

Home

Business

Laboratory

Enterprise

University

MSP Customer

Assets, users, policies, and permissions belong to organizations.

Organizations should remain isolated from one another.

---

# Sites

Organizations may contain multiple Sites.

Examples:

Home

Office

Primary Data Center

Secondary Data Center

Factory

Cloud Region

Permissions may be scoped to specific Sites.

---

# Groups

Groups simplify administration.

Examples:

Network Team

Infrastructure Team

Storage Team

Developers

Security Team

Operations

Home Users

Groups receive Roles.

Users inherit permissions through group membership.

---

# Roles

Roles are collections of permissions.

Examples:

Viewer

Operator

Administrator

Security Administrator

Storage Administrator

Network Administrator

Automation Manager

Plugin Developer

Connector Developer

Organization Owner

Roles should remain descriptive rather than technical.

---

# Permissions

Permissions are the smallest unit of authorization.

Examples include:

View Assets

View Events

View Logs

View Audit Logs

Execute Commands

Restart Services

Reboot Systems

Create Workflows

Delete Workflows

Approve Automations

Install Plugins

Remove Plugins

Manage Connectors

View Secrets

Rotate Secrets

Manage Users

Manage Policies

Manage Organizations

Permissions should remain granular.

---

# Permission Scope

Permissions may be scoped.

Examples:

Entire Organization

Specific Site

Rack

Asset

Connector

Plugin

Workflow

API

This enables fine-grained delegation.

---

# Asset Permissions

Assets may define permissions.

Examples:

Read

Monitor

Configure

Restart

Delete

Backup

Restore

Console Access

Remote Command Execution

Different assets may expose different operations.

---

# Connector Permissions

Connectors should receive only required permissions.

Examples:

Read Telemetry

Execute Commands

Read Configuration

Modify Configuration

Discover Assets

Access Vault

Connectors should never receive unrestricted access.

---

# Plugin Permissions

Plugins operate under explicit permissions.

Examples:

Filesystem

Vault

Network

MQTT

Home Assistant

Docker

Camera

Notifications

Database

Terminal

Requested permissions should be visible before installation.

---

# Automation Permissions

Automations execute under identities.

Automations should receive only the permissions explicitly granted.

Automations should never inherit unrestricted administrative access.

---

# Intelligence Engine Permissions

The Intelligence Engine is an identity.

By default it may:

Read Assets

Read Events

Read Knowledge

Generate Recommendations

Generate Summaries

Generate Workflows

The Intelligence Engine should not automatically receive:

Delete

Reboot

Rotate Credentials

Install Plugins

Execute Commands

These require explicit authorization.

---

# API Permissions

API tokens should receive explicit scopes.

Examples:

Read Only

Assets

Automation

Events

Knowledge

Administration

Notifications

Secrets

Tokens should follow least privilege.

---

# Temporary Permissions

Sentinel should support temporary elevation.

Examples:

30 minutes

1 hour

Until workflow completion

Maintenance window only

Temporary permissions reduce long-term risk.

---

# Delegation

Users may delegate authority.

Examples:

Vacation coverage

Maintenance window

Emergency response

Temporary project assignment

Delegation should always be time-limited.

---

# Approval Integration

RBAC determines whether approval is required.

Example:

Restart Production Database

Operator

Requires Approval

Administrator

May Execute

Emergency Administrator

May Override

Approval remains separate from authorization.

---

# Audit

Every authorization decision should be logged.

Examples:

Permission Granted

Permission Denied

Role Assigned

Role Removed

Temporary Access Granted

Temporary Access Expired

Every privileged action should remain traceable.

---

# Authentication Providers

RBAC should remain independent from authentication.

Supported providers may include:

Local Accounts

LDAP

Active Directory

OpenID Connect

OAuth2

SAML

Kerberos

Future identity providers

Changing authentication providers should not require redesigning RBAC.

---

# Default Roles

Recommended defaults include:

Viewer

Operator

Administrator

Organization Owner

Users may create custom roles.

---

# Permission Inheritance

Permissions should inherit predictably.

```text
Organization
      │
      ▼
Site
      │
      ▼
Group
      │
      ▼
Role
      │
      ▼
User
```

Inheritance should remain transparent.

---

# Security

RBAC should follow:

Least Privilege

Need-to-Know

Separation of Duties

Explicit Authorization

Auditability

Zero Trust

---

# Extensibility

Plugins may contribute:

Permissions

Roles

Asset Operations

Approval Types

Permission Validators

RBAC should remain extensible without modifying Sentinel Core.

---

# Design Rules

1. Every actor has an identity.
2. Roles are collections of permissions.
3. Permissions are granular.
4. Least privilege is the default.
5. Temporary elevation is preferred over permanent access.
6. AI follows the same authorization model as users.
7. Plugins operate under explicit permissions.
8. Every authorization decision is auditable.
9. Authentication and authorization remain separate.
10. Security should scale from homelabs to enterprises.

---

# Long-Term Vision

RBAC should provide a consistent authorization model across the entire Sentinel ecosystem.

Regardless of whether an action originates from a user, automation, connector, plugin, API client, or Intelligence Engine, authorization should be evaluated using the same principles.

A single, consistent security model enables Sentinel to scale from individual home users to globally distributed enterprise infrastructure without architectural changes.
