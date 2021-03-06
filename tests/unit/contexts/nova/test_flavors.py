# Copyright 2014: Mirantis Inc.
# All Rights Reserved.
#
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

import mock
from novaclient import exceptions as nova_exceptions

from rally_openstack.contexts.nova import flavors
from tests.unit import test

CTX = "rally_openstack.contexts.nova"


class FlavorsGeneratorTestCase(test.TestCase):

    def setUp(self):
        super(FlavorsGeneratorTestCase, self).setUp()
        self.context = {
            "config": {
                "flavors": [{
                    "name": "flavor_name",
                    "ram": 2048,
                    "disk": 10,
                    "vcpus": 3,
                    "ephemeral": 3,
                    "swap": 5,
                    "extra_specs": {
                        "key": "value"
                    }
                }]
            },
            "admin": {
                "credential": mock.MagicMock()
            },
            "task": mock.MagicMock(),
        }

    @mock.patch("%s.flavors.osclients.Clients" % CTX)
    def test_setup(self, mock_clients):
        # Setup and mock
        mock_create = mock_clients().nova().flavors.create
        mock_create().to_dict.return_value = {"flavor_key": "flavor_value"}

        # Run
        flavors_ctx = flavors.FlavorsGenerator(self.context)
        flavors_ctx.setup()

        # Assertions
        self.assertEqual({"flavor_name": {"flavor_key": "flavor_value"}},
                         flavors_ctx.context["flavors"])

        mock_clients.assert_called_with(self.context["admin"]["credential"])

        mock_create.assert_called_with(
            name="flavor_name", ram=2048, vcpus=3,
            disk=10, ephemeral=3, swap=5)
        mock_create().set_keys.assert_called_with({"key": "value"})
        mock_create().to_dict.assert_called_with()

    @mock.patch("%s.flavors.osclients.Clients" % CTX)
    def test_setup_failexists(self, mock_clients):
        # Setup and mock
        new_context = copy.deepcopy(self.context)
        new_context["flavors"] = {}

        mock_flavor_create = mock_clients().nova().flavors.create

        exception = nova_exceptions.Conflict("conflict")
        mock_flavor_create.side_effect = exception

        # Run
        flavors_ctx = flavors.FlavorsGenerator(self.context)
        flavors_ctx.setup()

        # Assertions
        self.assertEqual(new_context, flavors_ctx.context)

        mock_clients.assert_called_with(self.context["admin"]["credential"])

        mock_flavor_create.assert_called_once_with(
            name="flavor_name", ram=2048, vcpus=3,
            disk=10, ephemeral=3, swap=5)

    @mock.patch("%s.flavors.rutils.make_name_matcher" % CTX)
    @mock.patch("%s.flavors.resource_manager.cleanup" % CTX)
    def test_cleanup(self, mock_cleanup, mock_make_name_matcher):
        # Setup and mock
        real_context = {
            "config": {
                "flavors": [
                    {"name": "flavor_name"},
                ]
            },
            "admin": {
                "credential": mock.MagicMock()
            },
            "task": mock.MagicMock(),
        }

        # Run
        flavors_ctx = flavors.FlavorsGenerator(real_context)
        flavors_ctx.cleanup()

        mock_cleanup.assert_called_once_with(
            names=["nova.flavors"],
            admin=real_context["admin"],
            superclass=mock_make_name_matcher.return_value,
            task_id=flavors_ctx.get_owner_id())

        mock_make_name_matcher.assert_called_once_with("flavor_name")
