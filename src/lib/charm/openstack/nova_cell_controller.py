# Copyright 2016 Canonical Ltd
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
# The nova_cell_controller handlers class

# bare functions are provided to the reactive handlers to perform the functions
# needed on the class.
from __future__ import absolute_import

import collections

import charms_openstack.charm
import charms_openstack.adapters

PACKAGES = ['nova-conductor']
NOVA_DIR = '/etc/nova/'
NOVA_CONF = NOVA_DIR + "nova.conf"

OPENSTACK_RELEASE_KEY = 'nova-charm.openstack-release-version'


# select the default release function
charms_openstack.charm.use_defaults('charm.default-select-release')


class NovaCellControllerCharm(charms_openstack.charm.HAOpenStackCharm):
    """NovaCellControllerCharm provides the specialisation of the OpenStackCharm
    functionality to manage a nova_cell_controller unit.
    """

    release = 'mitaka'
    name = 'nova-cell-controller'
    packages = PACKAGES
    service_type = 'nova-cell-controller'
    default_service = 'nova-conductor'
    services = ['nova-conductor']

    # Note that the hsm interface is optional - defined in config.yaml
    required_relations = ['shared-db', 'amqp']

    restart_map = {
        NOVA_CONF: services,
    }

    # Package for release version detection
    release_pkg = 'nova-common'

    # Package codename map for nova-common
    package_codenames = {
        'nova-common': collections.OrderedDict([
            ('13', 'mitaka'),
            ('14', 'newton'),
            ('15', 'ocata'),
            ('16', 'pike'),
            ('17', 'queens'),
            ('18', 'rocky'),
        ]),
    }

    group = 'nova'

    sync_cmd = ['nova-manage', 'db', 'sync', '--local_cell']

    def get_amqp_credentials(self):
        """Provide the default amqp username and vhost as a tuple.

        :returns (username, host): two strings to send to the amqp provider.
        """
        return ('nova', 'openstack')

    def get_database_setup(self):
        """Provide the default database credentials as a list of 3-tuples

        returns a structure of:
        [
            {'database': <database>,
             'username': <username>,
             'hostname': <hostname of this unit>
             'prefix': <the optional prefix for the database>, },
        ]

        :returns [{'database': ...}, ...]: credentials for multiple databases
        """
        return [{'username': 'nova', 'database': 'nova'}]

    def states_to_check(self, required_relations=None):
        """Override the default states_to_check() for the assess_status
        functionality so that, if we have to have an HSM relation, then enforce
        it on the assess_status() call.

        If param required_relations is not None then it overrides the
        instance/class variable self.required_relations.

        :param required_relations: [list of state names]
        :returns: [states{} as per parent method]
        """
        if required_relations is None:
            required_relations = self.required_relations
        return super(NovaCellControllerCharm, self).states_to_check(
            required_relations=required_relations)
