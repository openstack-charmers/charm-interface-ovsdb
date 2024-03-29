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

# the reactive framework unfortunately does not grok `import as` in conjunction
# with decorators on class instance methods, so we have to revert to `from ...`
# imports

import inspect

import charmhelpers.core as ch_core

import charms.reactive as reactive

from charms.reactive import (
    when,
)

from .lib import ovsdb as ovsdb


class OVSDBRequires(ovsdb.OVSDB):

    @when('endpoint.{endpoint_name}.joined')
    def joined(self):
        ch_core.hookenv.log('{}: {} -> {}'
                            .format(self._endpoint_name,
                                    type(self).__name__,
                                    inspect.currentframe().f_code.co_name),
                            level=ch_core.hookenv.INFO)
        super().joined()
        if self.expected_units_available():
            reactive.set_flag(self.expand_name('{endpoint_name}.available'))

    @when('endpoint.{endpoint_name}.broken')
    def broken(self):
        super().broken()
