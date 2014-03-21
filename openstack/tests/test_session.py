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

# from __future__ import unicode_literals

import httpretty
import json

from openstack import session
from openstack.tests import base


fake_url = 'http://www.root.url'
fake_response = 'random text'

fake_record1 = {
    'key1': {
        'id': '123',
        'name': 'OneTwoThree',
        'random': 'qwertyuiop',
    },
}


class TestSession(base.TestCase):

    def stub_url(self, method, parts=None, base_url=None, **kwargs):
        if not base_url:
            base_url = fake_url

        if 'json' in kwargs and isinstance(kwargs['json'], type({})):
            kwargs['body'] = json.dumps(kwargs.pop('json'))
            kwargs['content_type'] = 'application/json'

        if parts:
            url = '/'.join([p.strip('/') for p in [base_url] + parts])
        else:
            url = base_url

        httpretty.register_uri(method, url, **kwargs)

    @httpretty.activate
    def test_request(self):
        self.stub_url(httpretty.GET, body=fake_response)
        sess = session.Session()
        resp = sess.request('GET', fake_url)
        self.assertEqual(httpretty.GET, httpretty.last_request().method)
        self.assertEqual(resp.text, fake_response)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)

    @httpretty.activate
    def test_request_json(self):
        self.stub_url(httpretty.GET, json=fake_record1)
        sess = session.Session()
        resp = sess.request('GET', fake_url)
        self.assertEqual(httpretty.GET, httpretty.last_request().method)
        self.assertEqual(resp.text, json.dumps(fake_record1))
        self.assertEqual(resp.json(), fake_record1)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)

    @httpretty.activate
    def test_delete(self):
        self.stub_url(httpretty.DELETE, body=fake_response)
        sess = session.Session()
        resp = sess.delete(fake_url)
        self.assertEqual(httpretty.DELETE, httpretty.last_request().method)
        self.assertEqual(resp.text, fake_response)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)

    @httpretty.activate
    def test_get(self):
        self.stub_url(httpretty.GET, body=fake_response)
        sess = session.Session()
        resp = sess.get(fake_url)
        self.assertEqual(httpretty.GET, httpretty.last_request().method)
        self.assertEqual(resp.text, fake_response)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)

    @httpretty.activate
    def test_head(self):
        self.stub_url(httpretty.HEAD, body=fake_response)
        sess = session.Session()
        resp = sess.head(fake_url)
        self.assertEqual(httpretty.HEAD, httpretty.last_request().method)
        self.assertEqual(resp.text, '')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)

    @httpretty.activate
    def test_options(self):
        self.stub_url(httpretty.OPTIONS, body=fake_response)
        sess = session.Session()
        resp = sess.options(fake_url)
        self.assertEqual(httpretty.OPTIONS, httpretty.last_request().method)
        self.assertEqual(resp.text, fake_response)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)

    @httpretty.activate
    def test_patch(self):
        self.stub_url(httpretty.PATCH, body=fake_response)
        sess = session.Session()
        resp = sess.patch(fake_url, json={'hello': 'world'})
        self.assertEqual(httpretty.PATCH, httpretty.last_request().method)
        self.assertEqual(
            httpretty.last_request().body.decode('utf-8'),
            json.dumps({'hello': 'world'}),
        )
        self.assertEqual(resp.text, fake_response)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)

    @httpretty.activate
    def test_post(self):
        self.stub_url(httpretty.POST, body=fake_response)
        sess = session.Session()
        resp = sess.post(fake_url, json={'hello': 'world'})
        self.assertEqual(httpretty.POST, httpretty.last_request().method)
        self.assertEqual(
            httpretty.last_request().body.decode('utf-8'),
            json.dumps({'hello': 'world'}),
        )
        self.assertEqual(resp.text, fake_response)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)

    @httpretty.activate
    def test_put(self):
        self.stub_url(httpretty.PUT, body=fake_response)
        sess = session.Session()
        resp = sess.put(fake_url, json={'hello': 'world'})
        self.assertEqual(httpretty.PUT, httpretty.last_request().method)
        self.assertEqual(
            httpretty.last_request().body.decode('utf-8'),
            json.dumps({'hello': 'world'}),
        )
        self.assertEqual(resp.text, fake_response)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.ok)
