# Copyright 2019 Canonical Ltd
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

# NOTE: Do not use the ``charms.reactive`` decorators that take flags
#       as arguments to wrap functions or methods in this shared library.
#
#       Consume the shared code from the interface specific files and declare
#       which flags to react to there.

import inspect
import ipaddress

import charmhelpers.core as ch_core

import charms.reactive as reactive


class OVSDB(reactive.Endpoint):

    @property
    def cluster_local_addr(self):
        for relation in self.relations:
            ng_data = ch_core.hookenv.network_get(
                self.expand_name('{endpoint_name}'),
                relation_id=relation.relation_id)
            for interface in ng_data.get('bind-addresses', []):
                for addr in interface.get('addresses', []):
                    return addr['address']

    @property
    def cluster_addrs(self):
        for relation in self.relations:
            for unit in relation.units:
                try:
                    addr = ipaddress.ip_address(
                        unit.received.get('bound-address', ''))
                except ValueError:
                    continue
                if isinstance(addr, ipaddress.IPv6Address):
                    yield '[{}]'.format(addr)
                else:
                    yield '{}'.format(addr)

    def expected_peers_available(self):
        if len(self.all_joined_units) == len(
                list(ch_core.hookenv.expected_peer_units())):
            for relation in self.relations:
                for unit in relation.units:
                    if not unit.received.get('bound-address'):
                        break
                else:
                    continue
                break
            else:
                return True
        return False

    def publish_cluster_local_addr(self):
        """Announce the address we bound our OVSDB Servers to.

        This will be used by our peers and clients to build a connection
        string to the remote cluster.
        """
        for relation in self.relations:
            relation.to_publish['bound-address'] = self.cluster_local_addr

    def joined(self):
        ch_core.hookenv.log('{}: {} -> {}'
                            .format(self._endpoint_name,
                                    type(self).__name__,
                                    inspect.currentframe().f_code.co_name),
                            level=ch_core.hookenv.INFO)
        reactive.set_flag(self.expand_name('{endpoint_name}.connected'))
        self.publish_cluster_local_addr()
        if self.expected_peers_available:
            reactive.set_flag(self.expand_name('{endpoint_name}.available'))

    def broken(self):
        reactive.clear_flag(self.expand_name('{endpoint_name}.available'))
        reactive.clear_flag(self.expand_name('{endpoint_name}.connected'))
