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

from __future__ import absolute_import
from __future__ import print_function

import mock

import reactive.nova_cell_controller_handlers as handlers

import charms_openstack.test_utils as test_utils


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = [
            'charm.installed',
            'amqp.connected',
            'shared-db.connected',
            'config.changed',
            'update-status']
        hook_set = {
            'when': {
                'render_stuff': (
                    'shared-db.available',
                    'amqp.available',),
                'db_setup': ('config.rendered',),
                'send_compute_data': (
                    'endpoint.nova-cell-compute.changed',
                    'endpoint.cloud-compute.joined',),
                'send_cell_data': (
                    'shared-db.available',
                    'endpoint.nova-cell-compute.joined',
                    'amqp.available',),
                'request_credentials': (
                    'identity-credentials.connected',)},
            'when_not': {
                'db_setup': ('shared-db.synced',)}
        }
        # test that the hooks were registered via the
        # reactive.nova_cell_controller_handlers
        self.registered_hooks_test_helper(handlers, hook_set, defaults)


class TestRenderStuff(test_utils.PatchHelper):

    def bob(self, release='mitaka'):
        self.ncc_charm = mock.MagicMock()
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = self.ncc_charm
        self.provide_charm_instance().__exit__.return_value = None

        self.patch_object(handlers, 'set_flag')
        self.patch_object(handlers.hookenv, 'config')
        self.patch_object(handlers.os_utils, 'get_os_codename_install_source')
        self.mock_nc_ep = mock.MagicMock()
        self.mock_ncc_ep = mock.MagicMock()
        self.mock_amqp_ep = mock.MagicMock()
        self.mock_cred_conn_ep = mock.MagicMock()
        self.mock_cred_avail_ep = None
        if release == 'train':
            self.mock_cred_avail_ep = 'arg3'
        self.mock_db_ep = mock.MagicMock()

        def _endpoint_from_flag(ep):
            mocks = {
                'endpoint.cloud-compute.joined': self.mock_nc_ep,
                'endpoint.nova-cell-compute.joined': self.mock_ncc_ep,
                'endpoint.nova-cell-compute.changed': self.mock_ncc_ep,
                'amqp.available': self.mock_amqp_ep,
                'identity-credentials.connected': self.mock_cred_conn_ep,
                'identity-credentials.available.auth': self.mock_cred_avail_ep,
                'shared-db.available': self.mock_db_ep}
            return mocks[ep]
        self.patch_object(handlers, 'endpoint_from_flag',
                          side_effect=_endpoint_from_flag)

    def test_request_credentials(self):
        self.bob()
        handlers.request_credentials()
        self.mock_cred_conn_ep.request_credentials.assert_called_with(
            'nova-cell-controller',
            project='services')

    def test_render_stuff(self):
        self.bob(release='stein')
        self.get_os_codename_install_source.return_value = 'stein'
        handlers.render_stuff('arg1', 'arg2')
        self.ncc_charm.render_with_interfaces.assert_called_once_with(
            ('arg1', 'arg2'))
        self.ncc_charm.assess_status.assert_called_once_with()
        self.set_flag.assert_called_once_with('config.rendered')

        self.bob(release='train')
        self.get_os_codename_install_source.return_value = 'train'
        handlers.render_stuff('arg1', 'arg2')
        self.ncc_charm.render_with_interfaces.assert_called_once_with(
            ('arg1', 'arg2', 'arg3'))
        self.ncc_charm.assess_status.assert_called_once_with()
        self.set_flag.assert_called_once_with('config.rendered')

    def test_db_setup(self):
        self.bob()
        handlers.db_setup('arg1')
        self.ncc_charm.db_sync.assert_called_once_with()
        self.ncc_charm.restart_all.assert_called_once_with()
        self.set_flag.assert_called_once_with('shared-db.synced')

    def test_send_compute_data(self):
        self.bob()
        self.mock_ncc_ep.get_region.return_value = {
            'region': 'Region52'}
        self.mock_ncc_ep.get_volume_data.return_value = {
            'volume_service': 'cinder'}
        self.mock_ncc_ep.get_ec2_data.return_value = {
            'ec2_host': 'http://ec2host'}
        self.mock_ncc_ep.get_restart_trigger.return_value = {
            'restart_trigger': 'a-uuid'}
        self.mock_ncc_ep.get_network_data.return_value = {
            'quantum_url': 'http://neutron:1234/api',
            'quantum_plugin': 'ovs',
            'network_manager': 'neutron',
            'quantum_security_groups': True,
        }
        self.mock_ncc_ep.get_console_data.return_value = {
            'serial_console_base_url': 'http://nova/serial',
            'enable_serial_console': True,
        }

        handlers.send_compute_data()

        self.mock_nc_ep.set_network_data.assert_called_once_with(
            'http://neutron:1234/api',
            neutron_plugin='ovs',
            network_manager='neutron',
            enable_security_groups=True)
        self.mock_nc_ep.set_console_data.assert_called_once_with(
            serial_console_base_url='http://nova/serial',
            enable_serial_console=True,
        )
        self.mock_nc_ep.set_region.assert_called_once_with(
            'Region52')
        self.mock_nc_ep.set_volume_data.assert_called_once_with(
            'cinder')
        self.mock_nc_ep.set_ec2_data.assert_called_once_with(
            'http://ec2host')
        self.mock_nc_ep.trigger_remote_restart.assert_called_once_with(
            restart_key='a-uuid')

    def test_send_cell_data(self):
        self.bob()
        mock_amqp_conv = mock.MagicMock()
        mock_amqp_conv.units = [
            'rabbitmq-server-cell2/0',
            'rabbitmq-server-cell2/1']

        self.mock_amqp_ep.conversation.return_value = mock_amqp_conv

        mock_db_conv = mock.MagicMock()
        mock_db_conv.units = [
            'percona-cluster-cell2/0',
            'percona-clustercell2/1']
        self.mock_db_ep.conversation.return_value = mock_db_conv
        self.config.return_value = 'cell2'

        handlers.send_cell_data()

        self.mock_ncc_ep.send_cell_data.assert_called_once_with(
            'cell2',
            'rabbitmq-server-cell2',
            'percona-cluster-cell2')
