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

import mock

from lib import ovsdb

import charms_openstack.test_utils as test_utils


_hook_args = {}


class TestNeutronLoadBalancerRequires(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.target = ovsdb.OVSDB('some-relation', [])
        self._patches = {}
        self._patches_start = {}

    def tearDown(self):
        self.target = None
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def patch_target(self, attr, return_value=None):
        mocked = mock.patch.object(self.target, attr)
        self._patches[attr] = mocked
        started = mocked.start()
        started.return_value = return_value
        self._patches_start[attr] = started
        setattr(self, attr, started)

    def patch_topublish(self):
        self.patch_target('_relations')
        relation = mock.MagicMock()
        to_publish = mock.PropertyMock()
        type(relation).to_publish = to_publish
        self._relations.__iter__.return_value = [relation]
        return relation.to_publish

    def test_cluster_local_addr(self):
        relation = mock.MagicMock()
        relation.relation_id = 'some-endpoint:42'
        self.patch_target('_relations')
        self._relations.__iter__.return_value = [relation]
        self.patch_target('expand_name')
        self.expand_name.return_value = 'some-relation'
        self.patch_object(ovsdb.ch_core.hookenv, 'network_get')
        self.network_get.return_value = {
            'bind-addresses': [
                {
                    'macaddress': '',
                    'interfacename': '',
                    'addresses': [
                        {
                            'hostname': '',
                            'address': '42.42.42.42',
                            'cidr': ''
                        },
                    ],
                },
            ],
            'egress-subnets': ['42.42.42.42/32'],
            'ingress-addresses': ['42.42.42.42'],
        }
        self.assertEquals(self.target.cluster_local_addr, '42.42.42.42')
        self.network_get.assert_called_once_with(
            'some-relation', relation_id='some-endpoint:42')

    def test_cluster_addrs(self):

        def _assert_generator(iterable, expect):
            for value in iterable:
                self.assertEquals(value, expect)

        relation = mock.MagicMock()
        relation.relation_id = 'some-endpoint:42'
        unit = mock.MagicMock()
        relation.units.__iter__.return_value = [unit]
        self.patch_target('_relations')
        self._relations.__iter__.return_value = [relation]
        unit.received.get.return_value = '127.0.0.1'
        _assert_generator(self.target.cluster_addrs, '127.0.0.1')
        unit.received.get.assert_called_once_with('bound-address', '')
        unit.received.get.return_value = '::1'
        _assert_generator(self.target.cluster_addrs, '[::1]')

    def test_expected_peers_available(self):
        # self.patch_target('_all_joined_units')
        self.patch_object(ovsdb.ch_core.hookenv, 'expected_peer_units')
        self.patch_target('_relations')
        self.target._all_joined_units = ['aFakeUnit']
        self.expected_peer_units.return_value = ['aFakeUnit']
        relation = mock.MagicMock()
        unit = mock.MagicMock()
        relation.units.__iter__.return_value = [unit]
        self._relations.__iter__.return_value = [relation]
        unit.received.get.return_value = '127.0.0.1'
        self.assertTrue(self.target.expected_peers_available())
        unit.received.get.assert_called_once_with('bound-address')
        unit.received.get.return_value = ''
        self.assertFalse(self.target.expected_peers_available())
        self.expected_peer_units.return_value = ['firstFakeUnit',
                                                 'secondFakeUnit']
        unit.received.get.return_value = '127.0.0.1'
        self.assertFalse(self.target.expected_peers_available())

    def test_publish_cluster_local_addr(self):
        to_publish = self.patch_topublish()
        self.target.publish_cluster_local_addr()
        to_publish.__setitem__.assert_called_once_with('bound-address', None)

    def test_joined(self):
        self.patch_object(ovsdb.reactive, 'set_flag')
        self.patch_target('publish_cluster_local_addr')
        self.patch_target('expected_peers_available')
        self.expected_peers_available.__bool__.return_value = False
        self.target.joined()
        self.expected_peers_available.__bool__.assert_called_once_with()
        self.set_flag.assert_called_once_with('some-relation.connected')
        self.publish_cluster_local_addr.assert_called_once_with()
        self.set_flag.reset_mock()
        self.expected_peers_available.__bool__.return_value = True
        self.target.joined()
        self.set_flag.assert_has_calls([
            mock.call('some-relation.connected'),
            mock.call('some-relation.available'),
        ])

    def test_broken(self):
        self.patch_object(ovsdb.reactive, 'clear_flag')
        self.target.broken()
        self.clear_flag.assert_has_calls([
            mock.call('some-relation.available'),
            mock.call('some-relation.connected'),
        ])
