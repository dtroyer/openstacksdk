#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from six.moves.urllib import parse as urlparse

from openstack.restapi import api_discovery


class IdentityVersion(api_discovery.BaseVersion):
    """Handle Identity^H^H^H^H^HKeystone anomalies"""

    def query_server(self, url):
        # Hack off '/v2.0' to do proper discovery with old auth URLs
        u = urlparse.urlparse(url)
        if u.path.endswith('/'):
            # Dump any trailing seperator
            path = u.path[:-1]
        else:
            path = u.path
        if (not self.strict):
            # Hack out the old v2_0
            if (path.endswith('v2.0')):
                # Strip off the last path component
                path = '/'.join(path.split('/')[:-1])

        versions = super(IdentityVersion, self).query_server(
            "%s://%s%s" % (u.scheme, u.netloc, path),
        )

        # Adjust the returned dict to match the rest of the world
        if 'values' in versions:
            versions = versions['values']
        return versions
