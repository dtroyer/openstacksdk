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

import requests


class ApiVersion(object):
    """Represent an API version

    :param name: API type name, i.e. 'identity', 'compute', etc.
    :param id: API version, i.e. '2.0', '3', etc.
    :param status: API status, i.e. 'stable', 'deprecated', etc
    :param class_name: The name of the client class for this version
    """
    def __init__(self, length=3, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._data = kwargs
        self.length = length
        self.id = self._normal(self.id)

    def __repr__(self):
        if hasattr(self, 'class_name'):
            return "<%s %s %s %s=%s>" % (
                self.__class__.__name__,
                self.name,
                self.id,
                self.status,
                self.class_name,
            )
        else:
            return "<%s %s %s %s>" % (
                self.__class__.__name__,
                self.name,
                self.id,
                self.status,
            )

    def __eq__(self, other):
        if self and other:
            return self.key == other.key and self.status == other.status
        else:
            return (not self and not other)

    def _normal(self, version):
        # Dump the leading 'v'
        try:
            version = version.lstrip('v')
        except AttributeError:
            pass
        return version

    def version_list(self):
        """Return the version as a list of N integers

        Allow only digits and '.' in a version
        """

        s = ''.join(i for i in self.id if i.isdigit() or i == '.')
        v = [int(i) for i in s.split('.')]
        while len(v) < self.length:
            v.append(0)
        return v[:self.length]

    @property
    def key(self):
        s = ""
        for v in self.version_list():
            s += "%03u" % v
        return s


class BaseVersion(object):
    """Negotiate an API version with a server

    Set strict=False to allow the following transformations to the URL in
    an attempt to find a usable version:
    - strip off the last path component; This handles the old-style auth
      url that ends with a version.
    - strip off the entire path; When the Identity API has not been
      relocated to a non-root URL this will get the entire list of
      supported versions.

    Set workaround_url_bug to False to build the actual API URL from
    the scheme, host and port of the API URL and the rest from the
    returned version URL.  This works around broken defaults in all
    of the OpenStack servers where the default for the API version
    URLs (links.href) is http://localhost:<port>/.

    :param session: a request.Session to use for the API requests
    :param clients: a list of available client version strings
    :param requested_version: if set, specifically look for this version
    :param api_url: the URL to query, usually <scheme>://<host>:<port>/
    :param strict: set False to allow munging on the api_url to find
                   a suitable version (default True)
    :param workaround_url_bug: set False to hack the returned server
                               version's 'links.href' URL to use the
                               scheme, host and port from api_url
                               (default True)
    :param **kwargs: all additional kw args are passes to session.Session
                     to initialize the default session created here
    :rtype: a XxxVersion object instance with client_version and
            server_version set to the negotiated versions; if either one
            of these is None, negotiation failed

    """

    api_name = "base"

    def __init__(
            self,
            session=None,
            clients=[],
            requested_version=None,
            api_url=None,
            strict=True,
            workaround_url_bug=True,
            **kwargs):

        if not session:
            self.session = session.Session(**kwargs)
        else:
            self.session = session
        self._api_url = api_url
        self._strict = strict
        self._workaround_url_bug = workaround_url_bug

        server_versions = self.query_server_versions()

        client_versions = self.client_versions(
            api_versions=clients,
            requested_version=requested_version,
        )

        (self.server_version, self.client_version) = self.match_versions(
            server_versions,
            client_versions,
        )

    def client_versions(self, api_versions=[], requested_version=None):
        """Process the available client versions...override
        """
        #raise NotImplementedError()
        """Return a list of client versions

        :param api_name: the name of the API, e.g. 'compute', 'image', etc
        :param api_versions: a list of supported client versions
        :param requested_version: the requested API version
        :rtype: a list of ApiVersion resources available for use
        """
        if requested_version:
            client_versions = [ApiVersion(
                name=self.api_name,
                id=requested_version,
                status=None,
            )]
        else:
            client_versions = []
            for v in api_versions:
                client_versions.append(ApiVersion(
                    name=self.api_name,
                    id=v,
                    status=None,
                ))
        return client_versions

    def query_server(self):
        """Perform the version string retrieval

        Override this to make API-specific adjustments such
        as stripping version strings out of URLs, etc
        """
        try:
            resp = self.session.get(self._api_url).json()
        except requests.ConnectionError:
            resp = {}

        if 'version' in resp:
            # We only got one, make it a list
            versions = [resp['version']]
        else:
            if 'versions' in resp:
                versions = resp['versions']
            else:
                # Handle bad server response
                versions = []

        return versions

    def query_server_versions(self, root_url=None):
        """Query REST server for supported API versions

        The passed in URL is stripped to host:port to query the root
        of the REST server to get available API versions.

        Identity /:
        {"versions": {"values": [ {}, {}, ] } }

        Identity /v2.0 /v3:
        {"version": {} }

        Compute /:
        {"versions": [ {}, {}, ] }

        :param api_name: the name of the API, e.g. 'compute', 'image', etc
        :param root_url: the URL to query, usually <scheme>://<host>:<port>/
        :param strict: allows munging on the url to find a version when False
        :rtype: a list of ApiVersion resources available on the server
        """

        # See what we can find
        if root_url:
            self._api_url = root_url
        version_list = self.query_server()

        server_versions = []
        for v in version_list:
            # Find the URL for this version
            ver_url = None
            for link in v['links']:
                if link['rel'] == 'self':
                    ver_url = link['href']
            if self._workaround_url_bug and ver_url:
                # break down api_url
                v_u = urlparse.urlparse(ver_url)
                a_u = urlparse.urlparse(self._api_url)
                # from url: scheme, netloc
                # from api_url: path, query (basically, the rest)
                if v_u.netloc.startswith('localhost'):
                    # Only hack this if it is the default setting
                    ver_url = urlparse.urlunparse((
                        a_u.scheme,
                        a_u.netloc,
                        v_u.path,
                        v_u.params,
                        v_u.query,
                        v_u.fragment,
                    ))
            server_versions.append(ApiVersion(
                name=self.api_name,
                url=ver_url,
                **v
            ))
        return server_versions

    def match_versions(self, server_list, client_list):
        """Match the highest client and server versions available

        Returns the matching server and client ApiVersion objects

        :param server_list: list of server ApiVersion objects
        :param client_list: list of client ApiVersion objects
        :rtype: a tuple of matching server and client ApiVersion objects,
                (None, None) if no match
        """
        # Build some dicts with normalized version strings for key
        # NOTE(dtroyer) py26-ism here...
        slist = dict((s.key, s) for s in server_list)
        clist = dict((c.key, c) for c in client_list)

        # Loop through client and server versions highest first
        for ckey in sorted(clist.keys(), reverse=True):
            cver = clist[ckey].version_list()
            for skey in sorted(slist.keys(), reverse=True):
                sver = slist[skey].version_list()
                # Check for major version match
                if cver[0] == sver[0]:
                    # Check that client minor is <= server minor
                    if cver[1] <= sver[1]:
                        return (slist[skey], clist[ckey])

        # No match, sad panda
        return (None, None)
