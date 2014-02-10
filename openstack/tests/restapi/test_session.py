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

import copy
import json
import mock
import requests
import six

from openstack.restapi.auth import base as auth_base
from openstack.restapi import exceptions
from openstack.restapi import session as client_session
from openstack.tests import base


fake_response = 'response'
fake_headers = {'User-Agent': client_session.USER_AGENT}


class FakeResponse(requests.Response):
    def __init__(self, headers={}, status_code=None, data=None, encoding=None):
        super(FakeResponse, self).__init__()

        self.status_code = status_code

        self.headers.update(headers)
        #self._content = json.dumps(data)
        self._content = data


def make_fake_response(status_code=200, data=fake_response):
    fake_resp = FakeResponse(status_code=status_code, data=data)
    return mock.MagicMock(
        request=mock.MagicMock(return_value=fake_resp),
    )


@mock.patch('openstack.restapi.session.requests.Session')
class SessionTests(base.TestCase):

    TEST_URL = 'http://127.0.0.1:5000/'

    def assertResponse(self, resp):
        self.assertTrue(resp.ok)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, 'response')

    def test_delete(self, session_mock):
        session_mock.return_value = make_fake_response()
        session = client_session.Session()
        resp = session.delete(self.TEST_URL)

        session_mock.return_value.request.assert_called_with(
            'DELETE',
            self.TEST_URL,
            headers=fake_headers,
            allow_redirects=False,
            verify=True,
        )

        self.assertResponse(resp)

    def test_get(self, session_mock):
        session_mock.return_value = make_fake_response()
        session = client_session.Session()
        resp = session.get(self.TEST_URL)

        session_mock.return_value.request.assert_called_with(
            'GET',
            self.TEST_URL,
            headers=fake_headers,
            allow_redirects=False,
            verify=True,
        )

        self.assertResponse(resp)

    def test_head(self, session_mock):
        session_mock.return_value = make_fake_response()
        session = client_session.Session()
        resp = session.head(self.TEST_URL)

        session_mock.return_value.request.assert_called_with(
            'HEAD',
            self.TEST_URL,
            headers=fake_headers,
            allow_redirects=False,
            verify=True,
        )

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)

    def test_patch(self, session_mock):
        session_mock.return_value = make_fake_response()
        session = client_session.Session()
        resp = session.patch(self.TEST_URL, json={'hello': 'world'})

        session_mock.return_value.request.assert_called_with(
            'PATCH',
            self.TEST_URL,
            headers={
                'User-Agent': client_session.USER_AGENT,
                'Content-Type': 'application/json',
            },
            allow_redirects=False,
            verify=True,
            data=json.dumps({'hello': 'world'}),
        )

        self.assertResponse(resp)

    def test_post(self, session_mock):
        session_mock.return_value = make_fake_response()
        session = client_session.Session()
        resp = session.post(self.TEST_URL, json={'hello': 'world'})

        session_mock.return_value.request.assert_called_with(
            'POST',
            self.TEST_URL,
            headers={
                'User-Agent': client_session.USER_AGENT,
                'Content-Type': 'application/json',
            },
            allow_redirects=False,
            verify=True,
            data=json.dumps({'hello': 'world'}),
        )

        self.assertResponse(resp)

    def test_put(self, session_mock):
        session_mock.return_value = make_fake_response()
        session = client_session.Session()
        resp = session.put(self.TEST_URL, json={'hello': 'world'})

        session_mock.return_value.request.assert_called_with(
            'PUT',
            self.TEST_URL,
            headers={
                'User-Agent': client_session.USER_AGENT,
                'Content-Type': 'application/json',
            },
            allow_redirects=False,
            verify=True,
            data=json.dumps({'hello': 'world'}),
        )

        self.assertResponse(resp)

    def test_user_agent(self, session_mock):
        session_mock.return_value = make_fake_response()
        session = client_session.Session(user_agent='test-agent')
        resp = session.get(self.TEST_URL)

        session_mock.return_value.request.assert_called_with(
            'GET',
            self.TEST_URL,
            headers={
                'User-Agent': 'test-agent',
            },
            allow_redirects=False,
            verify=True,
        )

        self.assertResponse(resp)

        resp = session.get(self.TEST_URL, headers={'User-Agent': 'new-agent'})
        session_mock.return_value.request.assert_called_with(
            'GET',
            self.TEST_URL,
            headers={
                'User-Agent': 'new-agent',
            },
            allow_redirects=False,
            verify=True,
        )
        self.assertTrue(resp.ok)

        resp = session.get(self.TEST_URL, headers={'User-Agent': 'new-agent'},
                           user_agent='overrides-agent')
        session_mock.return_value.request.assert_called_with(
            'GET',
            self.TEST_URL,
            headers={
                'User-Agent': 'overrides-agent',
            },
            allow_redirects=False,
            verify=True,
        )
        self.assertTrue(resp.ok)

    def test_http_session_opts(self, session_mock):
        session_mock.return_value = make_fake_response()
        session = client_session.Session(cert='cert.pem', timeout=5,
                                         verify='certs')
        session.post(self.TEST_URL, data='value')

        session_mock.return_value.request.assert_called_with(
            'POST',
            self.TEST_URL,
            headers={
                'User-Agent': client_session.USER_AGENT,
            },
            allow_redirects=False,
            cert='cert.pem',
            verify='certs',
            timeout=5.0,
            data='value',
        )

    def test_not_found(self, session_mock):
        session_mock.return_value = make_fake_response(status_code=404)
        session = client_session.Session()
        self.assertRaises(exceptions.NotFound, session.get, self.TEST_URL)

    def test_server_error(self, session_mock):
        session_mock.return_value = make_fake_response(status_code=500)
        session = client_session.Session()
        self.assertRaises(exceptions.InternalServerError,
                          session.get, self.TEST_URL)

    @httpretty.activate
    def test_session_debug_output(self):
        session = client_session.Session(verify=False)
        headers = {'HEADERA': 'HEADERVALB'}
        body = 'BODYRESPONSE'
        data = 'BODYDATA'
        self.stub_url(httpretty.POST, body=body)
        session.post(self.TEST_URL, headers=headers, data=data)

        self.assertIn('curl', self.logger.output)
        self.assertIn('POST', self.logger.output)
        self.assertIn('--insecure', self.logger.output)
        self.assertIn(body, self.logger.output)
        self.assertIn("'%s'" % data, self.logger.output)

        for k, v in six.iteritems(headers):
            self.assertIn(k, self.logger.output)
            self.assertIn(v, self.logger.output)


@mock.patch('openstack.restapi.session.requests.Session')
class RedirectTests(base.TestCase):

    REDIRECT_CHAIN = ['http://myhost:3445/',
                      'http://anotherhost:6555/',
                      'http://thirdhost/',
                      'http://finaldestination:55/']

    DEFAULT_REDIRECT_BODY = 'Redirect'
    DEFAULT_RESP_BODY = 'Found'

    def assertResponse(self, resp):
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, self.DEFAULT_RESP_BODY)

    def setup_redirects(self, smock, status=305):
        redir_list = []
        for d in self.REDIRECT_CHAIN:
            redir_list.append(FakeResponse(
                status_code=status,
                headers={"location": d},
                data=self.DEFAULT_REDIRECT_BODY,
            ))
        redir_list.append(FakeResponse(
            status_code=200,
            data=self.DEFAULT_RESP_BODY,
        ))
        smock.return_value = mock.MagicMock(
            request=mock.MagicMock(side_effect=redir_list),
        )
        return redir_list

    def test_basic_get(self, session_mock):
        self.setup_redirects(session_mock)
        session = client_session.Session()

        resp = session.get(self.REDIRECT_CHAIN[-2])
        session_mock.return_value.request.assert_called_with(
            'GET',
            self.REDIRECT_CHAIN[-1],
            headers=fake_headers,
            allow_redirects=False,
            verify=True,
        )
        self.assertResponse(resp)

    def test_basic_post_keeps_correct_method(self, session_mock):
        self.setup_redirects(session_mock)
        session = client_session.Session()

        resp = session.post(self.REDIRECT_CHAIN[-2])
        session_mock.return_value.request.assert_called_with(
            'POST',
            self.REDIRECT_CHAIN[-1],
            headers=fake_headers,
            allow_redirects=False,
            verify=True,
        )
        self.assertResponse(resp)

    def test_redirect_forever(self, session_mock):
        self.setup_redirects(session_mock)
        session = client_session.Session(redirect=True)

        resp = session.get(self.REDIRECT_CHAIN[0])
        session_mock.return_value.request.assert_called_with(
            'GET',
            self.REDIRECT_CHAIN[-1],
            headers=fake_headers,
            allow_redirects=False,
            verify=True,
        )

        self.assertResponse(resp)
        self.assertTrue(len(resp.history), len(self.REDIRECT_CHAIN))

    def test_no_redirect(self, session_mock):
        self.setup_redirects(session_mock)
        session = client_session.Session(redirect=False)

        resp = session.get(self.REDIRECT_CHAIN[0])
        session_mock.return_value.request.assert_called_with(
            'GET',
            self.REDIRECT_CHAIN[0],
            headers=fake_headers,
            allow_redirects=False,
            verify=True,
        )

        self.assertEqual(resp.status_code, 305)
        self.assertEqual(resp.text, self.DEFAULT_REDIRECT_BODY)
        #self.assertEqual(resp.url, self.REDIRECT_CHAIN[0])

#     @httpretty.activate
#     def test_redirect_limit(self):
#         self.setup_redirects()
#         for i in (1, 2):
#             session = client_session.Session(redirect=i)
#             resp = session.get(self.REDIRECT_CHAIN[0])
#             self.assertEqual(resp.status_code, 305)
#             self.assertEqual(resp.url, self.REDIRECT_CHAIN[i])
#             self.assertEqual(resp.text, self.DEFAULT_REDIRECT_BODY)
# 
#     @httpretty.activate
#     def test_history_matches_requests(self):
#         self.setup_redirects(status=301)
#         session = client_session.Session(redirect=True)
#         req_resp = requests.get(self.REDIRECT_CHAIN[0],
#                                 allow_redirects=True)
# 
#         ses_resp = session.get(self.REDIRECT_CHAIN[0])
# 
#         self.assertEqual(type(req_resp.history), type(ses_resp.history))
#         self.assertEqual(len(req_resp.history), len(ses_resp.history))
# 
#         for r, s in zip(req_resp.history, ses_resp.history):
#             self.assertEqual(r.url, s.url)
#             self.assertEqual(r.status_code, s.status_code)
# 
# 
# class ConstructSessionFromArgsTests(utils.TestCase):
# 
#     KEY = 'keyfile'
#     CERT = 'certfile'
#     CACERT = 'cacert-path'
# 
#     def _s(self, k=None, **kwargs):
#         k = k or kwargs
#         return client_session.Session.construct(k)
# 
#     def test_verify(self):
#         self.assertFalse(self._s(insecure=True).verify)
#         self.assertTrue(self._s(verify=True, insecure=True).verify)
#         self.assertFalse(self._s(verify=False, insecure=True).verify)
#         self.assertEqual(self._s(cacert=self.CACERT).verify, self.CACERT)
# 
#     def test_cert(self):
#         tup = (self.CERT, self.KEY)
#         self.assertEqual(self._s(cert=tup).cert, tup)
#         self.assertEqual(self._s(cert=self.CERT, key=self.KEY).cert, tup)
#         self.assertIsNone(self._s(key=self.KEY).cert)
# 
#     def test_pass_through(self):
#         value = 42  # only a number because timeout needs to be
#         for key in ['timeout', 'session', 'original_ip', 'user_agent']:
#             args = {key: value}
#             self.assertEqual(getattr(self._s(args), key), value)
#             self.assertNotIn(key, args)


class AuthPlugin(auth_base.BaseAuthPlugin):
    """Very simple debug authentication plugin.

    Takes Parameters such that it can throw exceptions at the right times.
    """

    TEST_TOKEN = 'aToken'

    def __init__(self, token=TEST_TOKEN):
        self.token = token

    def get_token(self, session):
        return self.token


@mock.patch('openstack.restapi.session.requests.Session')
class SessionAuthTests(base.TestCase):

    TEST_URL = 'http://127.0.0.1:5000/'
    TEST_JSON = {'hello': 'world'}

    def test_auth_plugin_default_with_plugin(self, session_mock):
        session_mock.return_value = make_fake_response(
            data=json.dumps(self.TEST_JSON),
        )

        # if there is an auth_plugin then it should default to authenticated
        auth = AuthPlugin()
        sess = client_session.Session(auth=auth)
        resp = sess.get(self.TEST_URL)
        headers = copy.copy(fake_headers)
        headers['X-Auth-Token'] = AuthPlugin.TEST_TOKEN
        session_mock.return_value.request.assert_called_with(
            'GET',
            self.TEST_URL,
            headers=headers,
            allow_redirects=False,
            verify=True,
        )

        self.assertDictEqual(resp.json(), self.TEST_JSON)

    def test_auth_plugin_disable(self, session_mock):
        session_mock.return_value = make_fake_response(
            data=json.dumps(self.TEST_JSON),
        )

        auth = AuthPlugin()
        sess = client_session.Session(auth=auth)
        resp = sess.get(self.TEST_URL, authenticated=False)
        session_mock.return_value.request.assert_called_with(
            'GET',
            self.TEST_URL,
            headers=fake_headers,
            allow_redirects=False,
            verify=True,
        )

        self.assertDictEqual(resp.json(), self.TEST_JSON)
