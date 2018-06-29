# Copyright 2018 Canonical Ltd
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

# this is just for the reactive handlers and calls into the charm.
from __future__ import absolute_import

import charms.reactive as reactive
import charmhelpers.core.hookenv as hookenv

import charms_openstack.charm as charm

from charms.reactive.relations import (
    endpoint_from_flag,
)

from charms.reactive.flags import (
    is_flag_set,
    set_flag,
    clear_flag,
)

# This charm's library contains all of the handler code associated with
# nova_cell_controller -- we need to import it to get the definitions for the
# charm.
import charm.openstack.nova_cell_controller as nova_cell_controller  # noqa


# Use the charms.openstack defaults for common states and hooks
charm.use_defaults(
    'charm.installed',
    'amqp.connected',
    'shared-db.connected',
    'config.changed',
    'update-status')


# Note that because of the way reactive.when works, (which is to 'find' the
# __code__ segment of the decorated function, it's very, very difficult to add
# other kinds of decorators here.  This rules out adding other things into the
# charm args list.  It is also CPython dependent.
@reactive.when('shared-db.available')
@reactive.when('amqp.available')
def render_stuff(*args):
    """Render the configuration for Nova cell controller when all the interfaces
    are available.

    """
    hookenv.log("about to call the render_configs with {}".format(args))
    with charm.provide_charm_instance() as nova_cell_controller_charm:
        nova_cell_controller_charm.render_with_interfaces(args)
        nova_cell_controller_charm.assess_status()
        set_flag('config.rendered')


@reactive.when_not('shared-db.synced')
@reactive.when('config.rendered')
def db_setup(*args):
    with charm.provide_charm_instance() as cell_charm:
        cell_charm.db_sync()
        cell_charm.restart_all()
        set_flag('shared-db.synced')


@reactive.when('endpoint.nova-cell-compute.changed')
@reactive.when('endpoint.cloud-compute.joined')
def send_compute_data():
    nc = endpoint_from_flag('endpoint.cloud-compute.joined')
    ncc_ep = endpoint_from_flag('endpoint.nova-cell-compute.changed')
    ncc_console_data = ncc_ep.get_console_data()
    ncc_network_data = ncc_ep.get_network_data()
    nc.set_network_data(
        ncc_network_data['quantum_url'],
        neutron_plugin=ncc_network_data['quantum_plugin'],
        network_manager=ncc_network_data['network_manager'],
        enable_security_groups=ncc_network_data['quantum_security_groups'])
    nc.set_console_data(
        serial_console_base_url=ncc_console_data['serial_console_base_url'],
        enable_serial_console=ncc_console_data['enable_serial_console'])
    nc.set_region(ncc_ep.get_region()['region'])
    nc.set_volume_data(ncc_ep.get_volume_data()['volume_service'])
    nc.set_ec2_data(ncc_ep.get_ec2_data()['ec2_host'])
    nc.trigger_remote_restart(
        restart_key=ncc_ep.get_restart_trigger()['restart_trigger'])


@reactive.when('shared-db.available')
@reactive.when('amqp.available')
@reactive.when('endpoint.nova-cell-compute.joined')
def send_cell_data():
    ncc_ep = endpoint_from_flag('endpoint.nova-cell-compute.joined')
    amqp_conv = endpoint_from_flag('amqp.available').conversation()
    # Push this calculation of service names down into the interfaces
    amqp_service_names = [u.split('/')[0] for u in amqp_conv.units if u]
    db_conv = endpoint_from_flag('shared-db.available').conversation()
    db_service_names = [u.split('/')[0] for u in db_conv.units if u]
    ncc_ep.send_cell_data(
        hookenv.config('cell-name'),
        amqp_service_names[0],
        db_service_names[0])
