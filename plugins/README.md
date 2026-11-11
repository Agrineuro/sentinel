# Sentinel plugins

This directory contains the official plugin catalog and contributor guidance. The catalog is displayed in Sentinel and links to source packages hosted in this repository.

## Runtime status

Sentinel Core currently loads built-in plugins from core/app/plugins/builtins and trusted plugin folders under the configured PLUGIN_DIR (default /data/plugins) when Core starts. Plugins execute in-process with Core permissions. Only install code you trust.

The Proxmox connector is included in Core and can be configured in Connectors. It uses a read-only API token, polls inventory, creates node/VM/container/storage assets, links guests to their hosting node, and records status changes as observations. It does not install plugins directly from GitHub yet. To add an external plugin today, place its package folder in PLUGIN_DIR and restart Core.

## Catalog

catalog.json is fetched by the dashboard from the raw GitHub URL. Keep it valid JSON and update it alongside each plugin. An entry marked planned is a roadmap item and is not runtime-installable.

## Developing connector plugins

Start with templates/connector. Each plugin package contains a manifest.json and Python module exposing create_plugin(). This is an initial internal contract; a stable SDK, isolation boundary, and dashboard install/upgrade workflow are future work.

Initial optional plugin priorities are SNMP monitoring, Syslog, Prometheus metrics, and Docker/container monitoring. Each plugin must state whether it reads, receives events, sends messages, or performs actions. Use read-only access by default.
