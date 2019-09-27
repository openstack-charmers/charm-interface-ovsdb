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
    DB_NB_PORT = 6641
    DB_SB_PORT = 6642

    def _format_addr(self, addr):
        """Validate and format IP address

        :param addr: IPv6 or IPv4 address
        :type addr: str
        :returns: Address string, optionally encapsulated in brackets ([])
        :rtype: str
        :raises: ValueError
        """
        ipaddr = ipaddress.ip_address(addr)
        if isinstance(ipaddr, ipaddress.IPv6Address):
            fmt = '[{}]'
        else:
            fmt = '{}'
        return fmt.format(ipaddr)

    @property
    def cluster_local_addr(self):
        for relation in self.relations:
            ng_data = ch_core.hookenv.network_get(
                self.expand_name('{endpoint_name}'),
                relation_id=relation.relation_id)
            for interface in ng_data.get('bind-addresses', []):
                for addr in interface.get('addresses', []):
                    return self._format_addr(addr['address'])

    @property
    def cluster_remote_addrs(self):
        for relation in self.relations:
            for unit in relation.units:
                try:
                    addr = self._format_addr(
                        unit.received.get('bound-address', ''))
                    yield addr
                except ValueError:
                    continue

    @property
    def db_nb_port(self):
        return self.DB_NB_PORT

    @property
    def db_sb_port(self):
        return self.DB_SB_PORT

    def db_connection_strs(self, addrs, port, proto='ssl'):
        """Provide connection strings

        :param port: Port number
        :type port: int
        :param proto: Protocol
        :type proto: str
        :returns: List of connection strings
        :rtype: Generator[str, None, None]
        """
        for addr in addrs:
            yield ':'.join((proto, addr, str(port)))

    @property
    def db_nb_connection_strs(self):
        return self.db_connection_strs(self.cluster_remote_addrs,
                                       self.db_nb_port)

    @property
    def db_sb_connection_strs(self):
        return self.db_connection_strs(self.cluster_remote_addrs,
                                       self.db_sb_port)

    def expected_units_available(self):
        """Whether expected units have joined and published data on a relation

        NOTE: This does not work for the peer relation, see separate method
              for that in the peer relation implementation.
        """
        if len(self.all_joined_units) == len(
                list(ch_core.hookenv.expected_related_units(
                    self.expand_name('{endpoint_name}')))):
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

    def publish_cluster_local_addr(self, addr=None):
        """Announce the address we bound our OVSDB Servers to.

        This will be used by our peers and clients to build a connection
        string to the remote cluster.
        """
        for relation in self.relations:
            relation.to_publish['bound-address'] = (
                addr or self.cluster_local_addr)

    def joined(self):
        ch_core.hookenv.log('{}: {} -> {}'
                            .format(self._endpoint_name,
                                    type(self).__name__,
                                    inspect.currentframe().f_code.co_name),
                            level=ch_core.hookenv.INFO)
        reactive.set_flag(self.expand_name('{endpoint_name}.connected'))

    def broken(self):
        reactive.clear_flag(self.expand_name('{endpoint_name}.available'))
        reactive.clear_flag(self.expand_name('{endpoint_name}.connected'))
