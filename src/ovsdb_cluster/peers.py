# Copyright 2018 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import charmhelpers.core as ch_core

import charms.reactive as reactive

# the reactive framework unfortunately does not grok `import as` in conjunction
# with decorators on class instance methods, so we have to revert to `from ...`
# imports
from charms.reactive import (
    when,
)

from .lib import ovsdb as ovsdb


class OVSDBClusterPeer(ovsdb.OVSDB):
    DB_NB_CLUSTER_PORT = 6643
    DB_SB_CLUSTER_PORT = 6644

    @property
    def db_nb_cluster_port(self):
        return self.DB_NB_CLUSTER_PORT

    @property
    def db_sb_cluster_port(self):
        return self.DB_SB_CLUSTER_PORT

    def expected_peers_available(self):
        if len(self.all_joined_units) == len(
                list(ch_core.hookenv.expected_peer_units())):
            for relation in self.relations:
                for unit in relation.units:
                    if not unit.received.get('bound-address'):
                        return False
            return True
        return False

    @when('endpoint.{endpoint_name}.joined')
    def joined(self):
        super().joined()
        if reactive.is_flag_set('leadership.set.ready'):
            self.publish_cluster_local_addr()
        if self.expected_peers_available():
            reactive.set_flag(self.expand_name('{endpoint_name}.available'))

    @when('endpoint.{endpoint_name}.broken')
    def broken(self):
        super().broken()
