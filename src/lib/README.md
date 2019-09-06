The python modules kept in this directory contain code shared among the
individual interfaces distributed as part of this repository.

> **Note**: Do not use the ``charms.reactive`` decorators that take flags
  as arguments to wrap functions or methods in the shared files.  Consume
  the shared code from the interface specific files and declare which flags
  to react to there.
