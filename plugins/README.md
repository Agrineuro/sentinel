# Sentinel plugins

This directory contains the official plugin catalog and contributor guidance. The catalog is displayed in Sentinel and links to source packages hosted in this repository.

## Runtime status

Sentinel Core currently loads built-in plugins from core/app/plugins/builtins and trusted plugin folders under the configured PLUGIN_DIR (default /data/plugins) when Core starts. Plugins execute in-process with Core permissions. Only install code you trust; installed plugin modules run in-process with Core permissions.

The Proxmox connector is included in Core. Optional Prometheus Metrics and Modbus TCP plugins are available from the catalog and can be installed by an administrator on the Plugins page. Once installed, each plugin appears as a configurable connection type. Prometheus runs a read-only PromQL query and maps vector samples into assets. Modbus TCP reads configured holding registers only; it does not write to equipment and does not directly support serial Modbus RTU. These plugins load into the Core process and use its network access. Install and update actions are restricted to administrators and accept only packages listed in the official GitHub catalog.

## Catalog

catalog.json is fetched by the dashboard from the raw GitHub URL. Keep it valid JSON and update it alongside each plugin. An entry marked planned is a roadmap item and is not runtime-installable.

## Developing connector plugins

Start with templates/connector. Each plugin package contains a manifest.json and Python module exposing create_plugin(). This is an initial internal contract; a stable SDK and isolation boundary are future work.

The next optional plugin priorities are SNMP monitoring, Syslog reception, Docker/container monitoring, and additional industrial protocols such as Modbus RTU through a serial gateway or Raspberry Pi bridge. Each plugin must state whether it reads, receives events, sends messages, or performs actions. Use read-only access by default.
