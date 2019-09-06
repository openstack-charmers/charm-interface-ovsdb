# Overview

This repository contains a set of similar interfaces with common code broken
out to a separate module.

This interface facilitates a provider charm to publish connection properties
of a OVSDB and a requirer charm to consume a remote OVSDB.

# Usage

No explicit handler is required to consume this interface in charms
that consume this interface.

In addittion to the states automatically set based on relation data by
``charms.reactive.Endpoint``, the interface provides the
``ovsdb.available`` state.

# metadata

To consume this interface in your charm or layer, add the following to `layer.yaml`:

```yaml
includes: ['interface:ovsdb']
```

and add a provider or requires interface of type `ovsdb` to your charm or
layers `metadata.yaml`:

```yaml
requires:
  ovsdb:
    interface: ovsdb
```

# Bugs

Please report bugs on [Launchpad](https://bugs.launchpad.net/openstack-charms/+filebug).

For development questions please refer to the OpenStack [Charm Guide](https://github.com/openstack/charm-guide).
