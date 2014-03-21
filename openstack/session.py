# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Wrapper class for requests.Session adds some common OpenStack functionality

- log all requests and responses at debug level
- json-encode request body passed in to request() as json=
- set default user_agent at Session creation; set to None to skip the header
- set default verify at Session creation

"""

import json
import logging
from six.moves.urllib import parse as urlencode

import requests


DEFAULT_USER_AGENT = 'python-OpenStackSDK'

_logger = logging.getLogger(__name__)


class Session(requests.Session):

    _user_agent = DEFAULT_USER_AGENT

    REDIRECT_STATUSES = (301, 302, 303, 305, 307)
    DEFAULT_REDIRECT_LIMIT = 30

    def __init__(
            self,
            redirect=DEFAULT_REDIRECT_LIMIT,
            user_agent=None,
            verify=True,
    ):
        """Wraps requests.Session to add some OpenStack-specific features

        :param int/bool redirect: the maximum number of redirections that
                                  can be followed by a request. Either an
                                  integer for a specific count or True/False
                                  for forever/never. (optional)
        :param string user_agent: Set the User-Agent header in the requests
        :param boolean/string verify: If ``True``, the SSL cert will be
                                      verified. A CA_BUNDLE path can also be
                                      provided.
        """

        super(Session, self).__init__()
        self._redirect = redirect
        self._user_agent = user_agent

        # Set the requests default
        self.verify = verify

    def request(self, method, url, redirect=None, **kwargs):
        """Send a request

        :param method: Request HTTP method
        :param url: Request URL
        :param int/bool redirect: the maximum number of redirections that
                                  can be followed by a request. Either an
                                  integer for a specific count or True/False
                                  for forever/never. (optional)

        The following additional kw args supported:
        :param json: Request body to be encoded as JSON
                     Overwrites ``data`` argument if present
        :param string user_agent: Set the User-Agent header; overwrites
                                  any value that may be in the headers dict

        Remaining kw args from requests.Session.request() supported

        Sets Session.allow_redirects = False

        """

        headers = kwargs.setdefault('headers', {})

        # JSON-encode the data in json arg if present
        # Overwrites any existing 'data' value
        if 'json' in kwargs and isinstance(kwargs['json'], type({})):
            kwargs['data'] = json.dumps(kwargs.pop('json'))
            headers['Content-Type'] = 'application/json'

        # Forcibly set the User-Agent header if we have a value passed in,
        # otherwise just set the default.  This allows the headers arg to
        # still supply a user-agent header.
        if 'user_agent' in kwargs:
            headers['User-Agent'] = kwargs['user_agent']
        elif self._user_agent:
            headers.setdefault('User-Agent', self._user_agent)

        # Force disable requests redirect handling, we will manage this below
        kwargs['allow_redirects'] = False

        if redirect is None:
            redirect = self._redirect

        self._log_request(method, url, **kwargs)

        resp = self._send_request(method, url, redirect, **kwargs)

        # NOTE(jamielennox): we create a tuple here to be the same as what is
        # returned by the requests library.
        resp.history = tuple(resp.history)

        return resp

    def _send_request(self, method, url, redirect, **kwargs):
        # NOTE(jamielennox): We handle redirection manually because the
        # requests lib follows some browser patterns where it will redirect
        # POSTs as GETs for certain statuses which is not want we want for an
        # API. See: https://en.wikipedia.org/wiki/Post/Redirect/Get

        resp = super(Session, self).request(method, url, **kwargs)

        self._log_response(resp)

        if resp.status_code in self.REDIRECT_STATUSES:
            # Be careful here in python True == 1 and False == 0
            if isinstance(redirect, bool):
                redirect_allowed = redirect
            else:
                redirect -= 1
                redirect_allowed = redirect >= 0

            if not redirect_allowed:
                return resp

            try:
                location = resp.headers['location']
            except KeyError:
                _logger.warn(
                    "Failed to redirect request to %s as new "
                    "location was not provided.",
                    resp.url,
                )
            else:
                new_resp = self._send_request(
                    method,
                    location,
                    redirect,
                    **kwargs
                )

                if not isinstance(new_resp.history, list):
                    new_resp.history = list(new_resp.history)
                new_resp.history.insert(0, resp)
                resp = new_resp

        return resp

    def _log_request(self, method, url, **kwargs):
        if 'params' in kwargs and kwargs['params'] != {}:
            url += '?' + urlencode(kwargs['params'])

        string_parts = [
            "curl -i",
            "-X '%s'" % method,
            "'%s'" % url,
        ]

        # kwargs overrides the default
        if (('verify' in kwargs and kwargs['verify'] is False) or
                not self.verify):
            string_parts.append('--insecure')

        for element in kwargs['headers']:
            header = " -H '%s: %s'" % (element, kwargs['headers'][element])
            string_parts.append(header)

        _logger.debug("REQ: %s" % " ".join(string_parts))
        if 'data' in kwargs:
            _logger.debug("REQ BODY: %r\n" % (kwargs['data']))

    def _log_response(self, response):
        _logger.debug(
            "RESP: [%s] %r" % (
                response.status_code,
                response.headers,
            ),
        )
        if response._content_consumed:
            _logger.debug(
                "RESP BODY: %s",
                response.text,
            )
        _logger.debug(
            "encoding: %s",
            response.encoding,
        )
