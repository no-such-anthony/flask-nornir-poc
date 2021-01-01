# Custom Inventory - Reads dicts as arguments to build inventory
# copied from 
# https://github.com/nornir-automation/nornir/blob/develop/nornir/plugins/inventory/simple.py
# and modified for dict input
#
# Other custom inventory examples
# https://github.com/nornir-automation/nornir3_demo/blob/master/nornir3_demo/plugins/inventory/acme.py
#
#


import logging
from typing import Any, Dict, Type

from nornir.core.inventory import (
    Inventory,
    Group,
    Groups,
    Host,
    Hosts,
    Defaults,
    ConnectionOptions,
    HostOrGroup,
    ParentGroups,
)


logger = logging.getLogger(__name__)


def _get_connection_options(data: Dict[str, Any]) -> Dict[str, ConnectionOptions]:
    cp = {}
    for cn, c in data.items():
        cp[cn] = ConnectionOptions(
            hostname=c.get("hostname"),
            port=c.get("port"),
            username=c.get("username"),
            password=c.get("password"),
            platform=c.get("platform"),
            extras=c.get("extras"),
        )
    return cp


def _get_defaults(data: Dict[str, Any]) -> Defaults:
    return Defaults(
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        connection_options=_get_connection_options(data.get("connection_options", {})),
    )


def _get_inventory_element(
    typ: Type[HostOrGroup], data: Dict[str, Any], name: str, defaults: Defaults
) -> HostOrGroup:
    return typ(
        name=name,
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        groups=data.get(
            "groups"
        ),  # this is a hack, we will convert it later to the correct type
        defaults=defaults,
        connection_options=_get_connection_options(data.get("connection_options", {})),
    )


class DictInventory:
    def __init__(
        self,
        hosts: dict = {},
        groups: dict = {},
        defaults: dict = {},
    ) -> None:
        """
        DictInventory is an inventory plugin that loads data from python dictionaries.
        The dicts follow the same structure as the native objects

        Args:

          host: dict with hosts definition
          group: dict with groups definition.
          defaults: dict with defaults definition.
        """

        self.defaults = defaults
        self.hosts = hosts
        self.groups = groups


    def load(self) -> Inventory:

        defaults = _get_defaults(self.defaults)

        hosts = Hosts()

        for n, h in self.hosts.items():
            hosts[n] = _get_inventory_element(Host, h, n, defaults)

        groups = Groups()

        for n, g in self.groups.items():
            groups[n] = _get_inventory_element(Group, g, n, defaults)

        for h in hosts.values():
            h.groups = ParentGroups([groups[g] for g in h.groups])

        for g in groups.values():
            g.groups = ParentGroups([groups[g] for g in g.groups])

        return Inventory(hosts=hosts, groups=groups, defaults=defaults)