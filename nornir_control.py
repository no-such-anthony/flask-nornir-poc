from nornir import InitNornir
from nornir_netmiko import netmiko_send_command
import yaml
import json
import traceback
from copy import deepcopy
from pprint import pformat
from collections import OrderedDict


# Import and register custom inventory
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir_plugins.inventory import DictInventory
InventoryPluginRegister.register("dictInventory", DictInventory)


# Custom runner with queue for client update polling
from nornir.core.plugins.runners import RunnersPluginRegister
from nornir_plugins.runner import UpdateRunner
RunnersPluginRegister.register("a_runner", UpdateRunner)


def nornir_inv(hosts, groups, defaults):
    try:
        with InitNornir(inventory={ "plugin": "dictInventory",
                                    "options": {
                                        "hosts" : hosts,
                                        "groups": groups,
                                        "defaults": defaults
                        }}) as nr:
            norn = inv2yaml(nr)

    except Exception as e:
        norn = f'<pre>{traceback.format_exc()}</pre>'

    return norn


def nornir_run(hosts, groups, defaults, updater):


    try:
        with InitNornir(runner = { 'plugin': "a_runner",
                                    'options': {
                                        "num_workers": 10,
                                        "updater": updater
                                    },
                        },
                        inventory={ "plugin": "dictInventory",
                                    "options": {
                                        "hosts" : hosts,
                                        "groups": groups,
                                        "defaults": defaults
                        }}) as nr:
            results = nr.run(task=custom_task, name="Custom Task")
            norn = results2html(results)

    except Exception as e:
        norn = f'<pre>{traceback.format_exc()}</pre>'

    return norn


def custom_task(task):
    cmd = 'show version'
    result = task.run(task=netmiko_send_command, name=cmd, command_string=cmd)


def results2html(results):
    norn = ''
    for device_name, multi_result in sorted(results.items()):
        norn += f'<h2>{device_name}</h2>\n'
        for result in multi_result:
            norn += f'<h3>{result.name}</h3>\n'
            x = result.result
            if not isinstance(x, type(None)):
                norn += '<pre>'
                if not isinstance(x, str):
                    if isinstance(x, OrderedDict):
                        norn += f'{json.dumps(x, indent=2)}\n'
                    else:
                        norn += f'{pformat(x, indent=2)}\n'
                else:
                    norn += x
                norn += '</pre>'
                
    return norn


def inv2yaml(nr):
    norn = {}
    for name, host in nr.inventory.hosts.items():
        norn[name] = {}
        norn[name]['hostname'] = host.hostname
        norn[name]['platform'] = host.platform
        norn[name]['username'] = host.username
        norn[name]['password'] = host.password
        norn[name]['port'] = host.port
        try:
            #hot off nornir development press #fix_621
            norn[name]['groups'] = [ str(group) for group in host.extended_groups() ]
        except AttributeError:
            #fall back to host.groups
            norn[name]['groups'] = [ str(group) for group in host.groups ]
        norn[name]['data'] = deepcopy(dict(host.items()))
        norn[name]['connection_options'] = {}
        for conn_type in ['netmiko','napalm']:
            norn[name]['connection_options'][conn_type] = tidyIt(host,
                deepcopy(host.get_connection_parameters(conn_type).dict()))

    norn2yaml = yaml.safe_dump(norn, sort_keys=False)
    norn = "<pre>\n"
    norn += norn2yaml
    norn += "</pre>\n"
    return norn   


def tidyIt(host, options):
    # helper function for inv2yaml
    # removes duplicate host connection information
    newDict = {}
    for k,v in options.items():
        if k=='extras' and v!={}:
            newDict[k] = v
            continue
        if k!='extras' and host.__getattribute__(k) != v:
            newDict[k] = v
            continue
    return newDict 




