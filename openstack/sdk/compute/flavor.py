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

"""Compute Flavor API Library"""

def list_flavors(
    session,
    service,
    detailed=True,
    is_public=True,
):
    """Get available flavors

    :param session: an authenticated session.Session object
    :param service: a ServiceFilter selecting the desired endpoint
    """

    params = {}

    if not is_public:
        params['is_public'] = is_public

    url = "/flavors"
    if detailed:
        url += "/detail"

    return session.get(url, service=service, params=params).json()['flavors']


def show_flavor(
    session,
    service,
    flavor,
):

    return session.get("/flavors/%s" % (flavor), service=service).json()['flavor']
