#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

"""Test Identity api_discovery module"""

from openstack.identity import api_discovery
from openstack.tests import test_api_discovery


class TestApiDiscovery(test_api_discovery.TestApiDiscovery):

    def setUp(self):
        super(TestApiDiscovery, self).setUp()
        self.id_class = api_discovery.IdentityVersion
        self.strict = True


class TestApiDiscoveryNotStrict(test_api_discovery.TestApiDiscovery):
    """Handle the v2-specific strict=False hack with legacy-format auth URLs

    If you have this auth_url: http://keystone:5000/v2.0
    This is what gets queried with strict=False: http://keystone:5000

    """

    def setUp(self):
        super(TestApiDiscoveryNotStrict, self).setUp()
        self.id_class = api_discovery.IdentityVersion
        self.strict = False

    def test_request_v2_url(self):
        vlist = self.check_versions(
            'http://keystone:5000/v2.0',
            200,
            {"version": test_api_discovery.FAPI_v2},
            expected_url='http://keystone:5000',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '2.0')
        self.assertEqual(vlist.server_version.id, '2.0')

        vlist = self.check_versions(
            'http://keystone:5000/v2.0',
            200,
            {"version": test_api_discovery.FAPI_v2},
            requested_version='2',
            expected_url='http://keystone:5000',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '2')
        self.assertEqual(vlist.server_version.id, '2.0')

        vlist = self.check_versions(
            'http://keystone:5000/v2.0',
            200,
            {"version": test_api_discovery.FAPI_v2},
            requested_version='3',
            expected_url='http://keystone:5000',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version, None)
        self.assertEqual(vlist.server_version, None)
