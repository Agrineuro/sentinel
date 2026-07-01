# Automation Engine Specification

> Automation should accomplish goals, not simply execute rules.

Version: 1.0 (Draft)

---

# Purpose

The Automation Engine enables Sentinel to translate events, policies, user intent, and intelligence into coordinated actions.

Rather than executing isolated commands, the Automation Engine orchestrates workflows that achieve desired outcomes safely, transparently, and consistently.

Automation exists to reduce repetitive operational work while keeping humans in control.

---

# Philosophy

Automation should never be surprising.

Users should understand:

* Why automation started.
* What it intends to accomplish.
* What systems are affected.
* What risks exist.
* Whether approval is required.

Automation should solve operational problems—not simply execute scripts.

---

# Core Responsibilities

The Automation Engine is responsible for:

* Executing workflows
* Evaluating triggers
* Enforcing policies
* Coordinating actions
* Requesting approvals
* Handling retries
* Performing rollbacks
* Recording execution history
* Reporting results
* Publishing automation events

---

# Inputs

Automation may be triggered by:

* Events
* Scheduled jobs
* User requests
* AI recommendations
* Connector discoveries
* Policies
* External webhooks
* API calls

Every automation begins with a trigger.

---

# Goals vs Tasks

Traditional automation executes tasks.

Sentinel should understand goals.

Example:

Traditional

```text
Restart Docker.
```

Sentinel

```text
Goal:

Restore media availability.

Possible actions:

Restart container

Restart Docker

Fail over service

Notify user

Delay maintenance

Escalate incident
```

The goal remains constant.

The chosen actions may vary depending on context.

---

# Workflow Model

Every automation consists of:

Trigger

↓

Evaluation

↓

Planning

↓

Approval (optional)

↓

Execution

↓

Validation

↓

Rollback (if needed)

↓

Reporting

---

# Automation Planning

Before execution, Sentinel should determine:

* Dependencies
* Required permissions
* Maintenance windows
* System health
* Risk level
* Potential impact
* Rollback availability

Planning reduces unintended consequences.

---

# Approval Levels

Automations should support multiple approval models.

Examples:

Automatic

User Approval

Administrator Approval

Dual Approval

Emergency Override

Approval requirements should be configurable.

---

# Risk Classification

Every automation should estimate operational risk.

Suggested levels:

* Informational
* Low
* Moderate
* High
* Critical

Risk should consider:

* Asset importance
* Dependencies
* Time
* Maintenance windows
* Business impact
* Previous failures

---

# Rollback

Whenever practical, Sentinel should prepare rollback plans.

Examples:

* VM snapshots
* Configuration backups
* Database backups
* Container image rollback
* Previous firmware
* Previous configuration

Rollback should be considered before execution whenever feasible.

---

# Validation

Automation is not complete until results are validated.

Examples:

* Service healthy
* API responding
* Container running
* Backup successful
* Network reachable
* Health checks passing

Validation should use measurable criteria.

---

# Dependencies

Automations should understand dependencies.

Example:

```text
Immich

↓

Docker

↓

Ubuntu

↓

Proxmox

↓

Storage

↓

UPS
```

Actions should occur in dependency-aware order.

---

# AI Integration

The Intelligence Engine may recommend automations.

The Automation Engine executes them.

Responsibilities remain separate.

AI recommends.

Automation performs.

Policies approve.

Users remain in control.

---

# Event Integration

Every stage should generate events.

Examples:

automation.started

automation.waiting.approval

automation.executing

automation.validation.failed

automation.rollback.started

automation.completed

automation.failed

Automation should remain observable.

---

# Reusable Actions

Automations should use reusable actions.

Examples:

* Restart service
* Reboot system
* Execute command
* Deploy container
* Send notification
* Create snapshot
* Wait for condition
* Request approval
* Run script

Reusable actions reduce duplication.

---

# Conditions

Automations should evaluate conditions.

Examples:

* CPU usage
* Time
* User presence
* Maintenance window
* Asset health
* Policy
* Dependency status
* Event history

Conditions determine execution paths.

---

# Variables

Workflows should support variables.

Examples:

Asset ID

Connector ID

User

Organization

Site

Timestamp

Event

Previous State

Variables make workflows reusable.

---

# Human Interaction

Users should be able to:

Pause

Resume

Cancel

Approve

Reject

Modify

Observe

Automation should remain collaborative.

---

# Scheduling

Automations should support:

Immediate

Delayed

Scheduled

Recurring

Maintenance windows

Event-driven execution should remain the primary model.

---

# Failure Handling

Failures should not end workflows immediately.

Supported behaviors:

Retry

Wait

Escalate

Rollback

Continue

Abort

Behavior should be configurable.

---

# Audit Logging

Every automation should record:

Who started it

Why it started

Trigger

Actions

Approvals

Results

Failures

Duration

Auditability is mandatory.

---

# Security

Automation must respect:

RBAC

Policies

Vault permissions

Connector permissions

Approval rules

Maintenance windows

Automation must never bypass Sentinel's security model.

---

# Extensibility

Plugins should contribute:

Actions

Triggers

Conditions

Validators

Approval methods

Notification channels

Automation should remain extensible.

---

# Design Rules

1. Automate goals, not commands.
2. Plan before executing.
3. Explain every automation.
4. Validate outcomes.
5. Prepare rollback whenever possible.
6. Respect policies.
7. Keep humans in control.
8. Generate events.
9. Audit everything.
10. Learn from previous executions.

---

# Long-Term Vision

The Automation Engine should become an operational orchestrator.

It should coordinate infrastructure rather than simply execute scripts.

The goal is not to remove people from operations.

The goal is to remove repetitive work, reduce operational risk, and allow people to focus on solving meaningful problems.
