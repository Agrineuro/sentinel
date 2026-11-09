# Sentinel plugins

This directory is the source of truth for the official optional plugin catalog shown in the Sentinel dashboard. Plugins are kept out of Sentinel Core so small deployments, including Raspberry Pi installations, only add integrations they need.

## Catalog

catalog.json is fetched by the dashboard from the raw GitHub URL. Keep it valid JSON and update it in the same change as each plugin. An entry with status "planned" is a roadmap item and is not installable.

## Developing a connector plugin

Start with templates/connector. The template defines metadata and contribution expectations; it is not yet a runtime-installable package. The runtime plugin loader, installation and upgrade flow, and stable SDK are still being built.

Initial plugin priorities are broad, optional integrations: SNMP monitoring, Syslog, Prometheus metrics, and Docker/container monitoring. Each plugin must state whether it reads, receives events, sends messages, or performs actions. Use read-only access by default.
