#!/usr/bin/python
# coding: utf-8 -*-

import six
from ansible.module_utils.basic import AnsibleModule
from vdsm.network import api
from vdsm.network.nm import networkmanager
from vdsm.network.canonicalize import canonicalize_bondings
from vdsm.network.canonicalize import canonicalize_networks
from vdsm.network.netconfpersistence import RunningConfig


DOCUMENTATION = """
---
module: vdsm_networks
author: "Petr Horacek (@phoracek)"
short_description: Manage VDSM networks
requirements: [vdsm, vdsm-client]
description:
    - Manage VDSM networks
options:
    networks:
        required: false
        default: {}
        description: >
            Dictionary in format `{name: attrs}`, where `attrs` has the same
            values and `state: present|absent`.
    bondings:
        required: false
        default: {}
        description: >
            Dictionary in format `{name: attrs}`, where `attrs` has the same
            values and `state: present|absent`.
    options:
        required: false
        default: {'connectivity_check': False,
                  'connectivity_timeout': 10}
        description:
              - 'connectivity_check' and 'connectivity_timeout' are mapped
                 VDSM setupNetworks's options 'connectivityCheck' and
                 'connectivityTimeout'.
"""

_EXAMPLES = """
- vdsm_networks:
    networks:
        net1:
            bonding: bond1
            status: present
        net2:
            status: absent
    bondings:
        bond1:
            nics:
                - eth0
                - eth1
            status: present
    options:
        connectivity_check: true
"""


def _translate(entries):
    for attrs in six.itervalues(entries):
        status = attrs.pop('status', 'present')
        if status == 'absent':
            if attrs != {}:
                raise AttributeError('With status=absent, attrs cannot '
                                     'contain any other values.')
            attrs['remove'] = True
        elif status != 'present':
            raise AttributeError('Invalid status "{}".'.format(status))
    return entries


# TODO: drop when VDSM canonicalizes bond options
def _canonicalize_bondings_modes(bondings):
    for attrs in six.itervalues(bondings):
        if 'options' not in attrs:
            attrs['options'] = 'mode=0'


# TODO: support source routing without service running
def _setup(networks, bondings, options):
    networkmanager.init()
    api.setupNetworks(networks, bondings, options)


class Config(object):

    def __init__(self, module):
        try:
            self._module = module
            self._networks = _translate(module.params['networks'])
            self._bondings = _translate(module.params['bondings'])
            self._options = module.params['options']
            canonicalize_networks(self._networks)
            canonicalize_bondings(self._bondings)
            _canonicalize_bondings_modes(self._bondings)
        except AttributeError as e:
            self._module.fail_json(msg=str(e))

    def run(self):
        running_config = RunningConfig()

        networks = {}
        for network, attrs in six.viewitems(self._networks):
            if 'remove' in attrs and network not in running_config.networks:
                if network in running_config.networks:
                    networks[network] = attrs
            else:
                if running_config.networks.get(network) != attrs:
                    networks[network] = attrs

        bondings = {}
        for bonding, attrs in six.iteritems(self._bondings):
            if 'remove' in attrs:
                if bonding in running_config.bonds:
                    bondings[bonding] = attrs
            else:
                if running_config.bonds.get(bonding) != attrs:
                    bondings[bonding] = attrs

        if not networks and not bondings:
            self._module.exit_json(changed=False)

        options = {
            'connectivityCheck': self._options.get(
                'connectivity_check', False),
            'connectivityTimeout': self._options.get(
                'connectivity_timeout', 10)
        }

        try:
            _setup(networks, bondings, options)
        except Exception as e:
            self._module.fail_json(msg=str(e))

        self._module.exit_json(changed=True)

    def check(self):
        running_config = RunningConfig()

        for network, attrs in six.viewitems(self._networks):
            if 'remove' in attrs:
                if network in running_config.networks:
                    self._module.exit_json(changed=True)
            else:
                if running_config.networks.get(network) != attrs:
                    self._module.exit_json(changed=True)

        for bonding, attrs in six.iteritems(self._bondings):
            if 'remove' in attrs:
                if bonding in running_config.bonds:
                    self._module.exit_json(changed=True)
            else:
                if running_config.bonds.get(bonding) != attrs:
                    self._module.exit_json(changed=True)
        self._module.exit_json(changed=False)


def main():
    module = AnsibleModule(
        argument_spec={
            'networks': {'default': {}, 'type': 'dict'},
            'bondings': {'default': {}, 'type': 'dict'},
            'options': {
                'default': {
                    'connectivity_check': False,
                    'connectivity_timeout': 10
                },
                'type': 'dict'
            }
        },
        supports_check_mode=True
    )
    config = Config(module)
    if module.check_mode:
        config.check()
    else:
        config.run()


if __name__ == '__main__':
    main()
