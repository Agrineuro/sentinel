# Credential Vault Specification

> Trust begins with protecting secrets.

Version: 1.0 (Draft)

---

# Purpose

The Sentinel Credential Vault provides secure storage, management, rotation, and controlled access to secrets used throughout the platform.

The Vault serves as the single authoritative source for all sensitive credentials.

No subsystem should permanently store credentials outside the Vault.

---

# Philosophy

Credentials represent trust.

Trust should never be scattered throughout the platform.

Instead, Sentinel centralizes credential management through the Vault.

The Vault should be:

* Secure
* Auditable
* Extensible
* Encrypted
* Policy-aware
* Permission-controlled

---

# Types of Secrets

The Vault may store:

Passwords

SSH Keys

API Keys

OAuth Tokens

TLS Certificates

Private Keys

SNMP Credentials

WinRM Credentials

Database Credentials

Cloud Credentials

Bearer Tokens

Encryption Keys

Custom Secret Types

---

# Security Principles

The Vault follows:

Least Privilege

Zero Trust

Encryption by Default

Need-to-Know

Auditable Access

Short-Lived Access

---

# Secret Lifecycle

```text
Create

↓

Encrypt

↓

Store

↓

Use

↓

Rotate

↓

Archive

↓

Delete
```

Every stage should be recorded.

---

# Encryption

Secrets must be encrypted before storage.

Requirements:

Encryption at rest

Encryption in transit

Key separation

Key rotation support

Future cryptographic agility

Sentinel should support replacing encryption algorithms without redesigning the Vault.

---

# Access Flow

```text
Connector

↓

Vault Request

↓

RBAC

↓

Policy Engine

↓

Approval (if required)

↓

Temporary Secret

↓

Connector

↓

Target System
```

The connector never permanently stores the credential.

---

# Temporary Access

Secrets should be provided only when needed.

After use:

Memory should be cleared.

Sessions should expire.

Temporary tokens should be revoked where possible.

Persistent exposure should be avoided.

---

# Secret Metadata

Every secret should include metadata.

Examples:

Name

Description

Owner

Organization

Site

Rotation Schedule

Expiration

Creation Date

Last Used

Last Rotated

Classification

Connector Usage

Metadata should never include the secret itself.

---

# Secret Classification

Suggested classifications:

Public

Internal

Confidential

Restricted

Highly Sensitive

Classification may influence RBAC and Policy evaluation.

---

# Secret Rotation

The Vault should support scheduled rotation.

Examples:

SSH Keys

Passwords

API Tokens

Certificates

Rotation should generate events.

AI may recommend rotation but should not automatically rotate secrets without authorization.

---

# Version History

Secrets may maintain version history.

Example:

Password v1

↓

Password v2

↓

Password v3

Older versions should remain protected and expire according to policy.

---

# Secret Consumers

Consumers include:

Connectors

Plugins

Automations

Workflows

API Clients

Notification Services

External Integrations

Every consumer must authenticate before requesting a secret.

---

# Secret Permissions

Permissions include:

View Metadata

Use Secret

Create Secret

Update Secret

Rotate Secret

Delete Secret

Export Secret

Audit Secret

Permissions should remain granular.

---

# Audit Logging

Every Vault operation should generate an audit event.

Examples:

Secret Created

Secret Used

Secret Rotated

Secret Deleted

Access Denied

Export Attempt

Audit records should include:

Identity

Timestamp

Reason

Asset

Policy Result

Approval Result

---

# Secret Sharing

Secrets should never be copied between systems unnecessarily.

Instead:

Multiple connectors may reference the same Vault entry.

Example:

```text
SSH Credential

↓

Linux Connector

↓

Utility Server

↓

Backup Server

↓

Immich Server
```

The credential exists only once.

---

# Connectors

Connectors should reference Vault IDs.

Never credentials.

Example:

```yaml
connector:
  credential: vault:ssh-production-root
```

---

# Plugins

Plugins never receive unrestricted Vault access.

Plugins request permissions.

The Vault determines:

Whether access is allowed

Which secret may be used

How long access remains valid

---

# AI Integration

The Intelligence Engine may know that secrets exist.

It should not know the secrets themselves.

AI may:

Recommend rotation

Identify expired credentials

Identify duplicate credentials

Detect insecure configurations

AI should never expose secret values.

---

# Secret Discovery

Future versions may discover unmanaged credentials.

Examples:

SSH Keys

Certificates

Expired Tokens

Hardcoded Credentials

Discovery should generate recommendations rather than immediate changes.

---

# High Availability

Enterprise deployments may replicate Vault data securely.

Replication should preserve:

Encryption

Audit Logs

Version History

Access Policies

---

# Import and Export

Supported operations:

Secure Import

Encrypted Backup

Encrypted Restore

Migration

Plaintext export should be disabled by default.

---

# Disaster Recovery

The Vault should support:

Encrypted Backup

Offline Recovery

Key Escrow (optional)

Recovery Validation

Recovery procedures should be documented.

---

# Extensibility

Plugins may contribute:

Secret Types

Rotation Providers

External Vault Integrations

Validation Rules

Future integrations may include:

HashiCorp Vault

CyberArk

Azure Key Vault

AWS Secrets Manager

Google Secret Manager

---

# Design Rules

1. The Vault is the only source of secrets.
2. Secrets remain encrypted.
3. Secrets are never logged.
4. Secrets are accessed through RBAC.
5. Policies govern secret usage.
6. Temporary access is preferred.
7. Secret use is audited.
8. Connectors reference secrets, never store them.
9. AI never sees secret values.
10. Rotation should be encouraged.

---

# Long-Term Vision

The Credential Vault should become one of the foundational trust services within Sentinel.

Rather than simply storing passwords, it should provide secure identity for the entire infrastructure ecosystem.

Every connector, plugin, workflow, automation, and Intelligence Engine should rely upon the Vault for secure access while remaining fully auditable, policy-aware, and transparent.

The Vault is not a password manager.

It is the trust foundation of Sentinel.
