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

"""Test api_discovery module"""

import json
import mock
import requests

from openstack import api_discovery
from openstack.tests import base

fake_user_agent = 'test_rapi'

FAPI_v2 = {
    "status": "stable",
    "updated": "2013-03-06T00:00:00Z",
    "media-types": [
        {
            "base": "application/json",
            "type": "application/vnd.openstack.identity-v2.0+json"
        },
        {
            "base": "application/xml",
            "type": "application/vnd.openstack.identity-v2.0+xml"
        }
    ],
    "id": "v2.0",
    "links": [
        {
            "href": "http://10.130.50.11:5000/v2.0/",
            "rel": "self"
        },
        {
            "href": "http://docs.openstack.org/api/openstack-identity-service/2.0/content/",  # noqa
            "type": "text/html",
            "rel": "describedby"
        },
        {
            "href": "http://docs.openstack.org/api/openstack-identity-service/2.0/identity-dev-guide-2.0.pdf",  # noqa
            "type": "application/pdf",
            "rel": "describedby"
        }
    ]
}

# default DevStack install
FAPI_v3 = {
    "status": "stable",
    "updated": "2013-03-06T00:00:00Z",
    "media-types": [
        {
            "base": "application/json",
            "type": "application/vnd.openstack.identity-v3+json"
        },
        {
            "base": "application/xml",
            "type": "application/vnd.openstack.identity-v3+xml"
        }
    ],
    "id": "v3.0",
    "links": [
        {
            "href": "http://10.130.50.11:35357/v3/",
            "rel": "self"
        }
    ]
}

FAPI_All = {
    "versions": [
        FAPI_v2,
        FAPI_v3,
    ]
}

fake_identity_version_single = {
    'versions': {
        'values': [
            {
                "status": "stable",
                "updated": "2013-03-06T00:00:00Z",
                "media-types": [
                    {
                        "base": "application/json",
                        "type": "application/vnd.openstack.identity-v3+json"
                    },
                    {
                        "base": "application/xml",
                        "type": "application/vnd.openstack.identity-v3+xml"
                    }
                ],
                "id": "v3.0",
                "links": [
                    {
                        "href": "http://10.130.50.11:5000/v3/",
                        "rel": "self"
                    }
                ]
            }
        ]
    }
}

FAKE_API_VERSIONS = {
    '2.0': 'fake.identity.client.ClientV2',
    '2.1': 'fake.identity.client.ClientV2_1',
    '3': 'fake.identity.client.ClientV3',
}


class FakeResponse(requests.Response):
    def __init__(self, headers={}, status_code=None, data=None, encoding=None):
        super(FakeResponse, self).__init__()

        self.status_code = status_code
        self.headers.update(headers)
        self._content = json.dumps(data).encode('ascii')

# These tests still need to be generalized away from identity-centric

class TestApiDiscovery(base.TestCase):

    def setUp(self):
        super(TestApiDiscovery, self).setUp()
        self.id_class = api_discovery.BaseVersion
        self.strict = True

    def check_versions(self, url, resp_status, resp_data,
                       expected_url=None, requested_version=None, strict=True):
        if not expected_url:
            expected_url = url

        resp = FakeResponse(
            status_code=resp_status,
            data=resp_data,
        )
        session_mock = mock.MagicMock(
            get=mock.MagicMock(return_value=resp),
        )
        vlist = self.id_class(
            session=session_mock,
            clients=FAKE_API_VERSIONS.keys(),
            requested_version=requested_version,
            api_url=url,
            strict=strict,
        )

        session_mock.get.assert_called_with(expected_url)
        #self.assertNotEqual(vlist.client_version, None)
        #self.assertNotEqual(vlist.server_version, None)
#         print("c: %s" % vlist.client_version.id)
#         print("s: %s" % vlist.server_version.id)
        return vlist

    def test_request_root_url(self):
        vlist = self.check_versions(
            'http://keystone:5000',
            300,
            FAPI_All,
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '3')
        self.assertEqual(vlist.server_version.id, '3.0')

        vlist = self.check_versions(
            'http://keystone:5000',
            300,
            FAPI_All,
            requested_version='2',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '2')
        self.assertEqual(vlist.server_version.id, '2.0')

        vlist = self.check_versions(
            'http://keystone:5000',
            300,
            FAPI_All,
            requested_version='3',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '3')
        self.assertEqual(vlist.server_version.id, '3.0')

    def test_request_v2_url(self):
        """The magic hack should not work here

        If you have this auth_url: http://keystone:5000/v2.0
        This is what gets queried with strict=True: http://keystone:5000/v2.0

        """

        vlist = self.check_versions(
            'http://keystone:5000/v2.0',
            200,
            {"version": FAPI_v2},
            expected_url='http://keystone:5000/v2.0',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '2.0')
        self.assertEqual(vlist.server_version.id, '2.0')

        vlist = self.check_versions(
            'http://keystone:5000/v2.0',
            200,
            {"version": FAPI_v2},
            requested_version='2',
            expected_url='http://keystone:5000/v2.0',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '2')
        self.assertEqual(vlist.server_version.id, '2.0')

        vlist = self.check_versions(
            'http://keystone:5000/v2.0',
            200,
            {"version": FAPI_v2},
            requested_version='3',
            expected_url='http://keystone:5000/v2.0',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version, None)
        self.assertEqual(vlist.server_version, None)

    def test_request_v3_url(self):
        vlist = self.check_versions(
            'http://keystone:5000/v3',
            200,
            {"version": FAPI_v3},
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '3')
        self.assertEqual(vlist.server_version.id, '3.0')

        vlist = self.check_versions(
            'http://keystone:5000/v3',
            200,
            {"version": FAPI_v3},
            requested_version='2',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version, None)
        self.assertEqual(vlist.server_version, None)

        vlist = self.check_versions(
            'http://keystone:5000/v3',
            200,
            {"version": FAPI_v3},
            requested_version='3',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '3')
        self.assertEqual(vlist.server_version.id, '3.0')


class TestApiDiscoveryNotStrict(TestApiDiscovery):

    def setUp(self):
        super(TestApiDiscoveryNotStrict, self).setUp()
        self.id_class = api_discovery.BaseVersion
        self.strict = False

    def test_request_v2_url(self):
        vlist = self.check_versions(
            'http://keystone:5000/v2.0',
            200,
            {"version": FAPI_v2},
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '2.0')
        self.assertEqual(vlist.server_version.id, '2.0')

        vlist = self.check_versions(
            'http://keystone:5000/v2.0',
            200,
            {"version": FAPI_v2},
            requested_version='2',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version.id, '2')
        self.assertEqual(vlist.server_version.id, '2.0')

        vlist = self.check_versions(
            'http://keystone:5000/v2.0',
            200,
            {"version": FAPI_v2},
            requested_version='3',
            strict=self.strict,
        )
        self.assertEqual(vlist.client_version, None)
        self.assertEqual(vlist.server_version, None)
