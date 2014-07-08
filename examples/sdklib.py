#!/usr/bin/env python
# sdklib.py - Sample calling the sdk lib modules

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

"""Example usage of low-level SDK API"""

import sys

from examples import authenticate as ex_authenticate
from examples import common as ex_common
from examples import transport as ex_transport
from openstack.auth import service_filter
from openstack.sdk.compute import flavor
from openstack.sdk.objectstore import container
from openstack.sdk.objectstore import object
from openstack.sdk import session


def do_flavor(opts, sess):
    """Run compute flavor examples"""

    region = opts.os_region
    compute_filter = service_filter.ServiceFilter(
        region=region,
        service_type='compute',
    )
    print "compute filter: %s" % compute_filter

    # List flavors
    f_list = flavor.list_flavors(sess, compute_filter)
    print("flavors: %s" % f_list)

    # Get first flavor name & id
    f_id = f_list[0]['id']
    f_name = f_list[0]['name']
    print("flavor %s - %s" % (f_id, f_name))

    # Show flavor
    f_show = flavor.show_flavor(sess, compute_filter, f_id)
    print("flavor: %s: %s" % (f_id, f_show))


def do_objectstore(opts, sess):
    """Run object-store examples"""

    region = opts.os_region
    objstore_filter = service_filter.ServiceFilter(
        region=region,
        service_type='object-store',
    )
    print "objstore filter: %s" % objstore_filter

    # List containers
    c_list = container.list_containers(sess, objstore_filter)
    print("containers: %s" % c_list)

    # get first container name
    c_name = c_list[0]['name']
    print "container: %s" % c_name

    # Show container
    c_show = container.show_container(sess, objstore_filter, c_name)
    print "container: %s: %s" % (c_name, c_show)

    # List contents of container
    o_list = object.list_objects(sess, objstore_filter, c_name)
    print "objects: %s" % o_list

    # get first container name
    o_name = o_list[0]['name']
    print "object: %s" % o_name

    # Show object
    o_show = object.show_object(sess, objstore_filter, c_name, o_name)
    print "object: %s: %s" % (o_name, o_show)

def run(opts):
    """Run several examples"""

    # Build our foundation and authenticate
    xport = ex_transport.make_transport(opts)
    auth = ex_authenticate.make_authenticate(opts)
    sess = session.Session(xport, auth)

#     do_objectstore(opts, sess)

    do_flavor(opts, sess)


if __name__ == "__main__":
    parser = ex_common.option_parser()
    # add more args here
    opts = parser.parse_args()
    ex_common.configure_logging(opts)
    sys.exit(run(opts))
