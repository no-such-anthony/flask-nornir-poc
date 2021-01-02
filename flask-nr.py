from flask import Flask, render_template, request, Markup, session, jsonify
from flask_socketio import SocketIO
from flask_socketio import send, emit
import yaml
import json
import traceback
import ydata
from os import urandom
from pprint import pformat


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = urandom(32)
socketio = SocketIO(app, cors_allowed_origins='*')
#socketio = SocketIO(app, cors_allowed_origins='*',logger=True, engineio_logger=True)


from nornir import InitNornir
from nornir_netmiko import netmiko_send_command


# Import and register custom inventory
from nornir.core.plugins.inventory import InventoryPluginRegister
from inventory_plugin import DictInventory
InventoryPluginRegister.register("dictInventory", DictInventory)

# Custom runner to update client via websocket
from nornir.core.plugins.runners import RunnersPluginRegister
from runner_plugin import EmitRunner
RunnersPluginRegister.register("a_runner", EmitRunner)


def dict2html(d):
    h = f'<ul>\n'
    if isinstance(d, dict):
        for k,v in d.items():        
            if isinstance(v, (list,dict)):
                h += f'<li>{k}</li>\n'
                h += dict2html(v)
            else:            
                h += f'<li>{k}: {v}</li>\n'
    if isinstance(d,list):
        for v in d:
            h += f'<li>{v}</li>\n'
    h += f'</ul>\n'
    return h


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


def inv2html(nr):
    norn = ''
    for name, host in nr.inventory.hosts.items():
        norn += f'<p>{name}</p>\n'
        norn += f'<ul>\n'
        norn += f'<li>hostname: {host.hostname}</li>\n'
        norn += f'<li>platform: {host.platform}</li>\n'
        norn += f'<li>hostname: {host.username}</li>\n'
        norn += f'<li>platform: {host.password}</li>\n'
        norn += f'<li>port: {host.port}</li>\n'
        norn += f'<li>groups:</li>\n'
        try:
            #hot off nornir development press #fix_621
            norn += dict2html(host.extended_groups())  
        except AttributeError:
            #fall back to host.groups
            norn += dict2html(host.groups)
        norn += f'<li>data:</li>\n'
        norn += dict2html(dict(host.items()))
        norn += f'<li>connection_options:</li>\n'
        norn += f'<ul>\n'
        for conn_type in ['netmiko','napalm']:
            norn += f'<li>{conn_type}</li>'
            norn += dict2html(host.get_connection_parameters(conn_type).dict())
        norn += f'</ul>\n'
        norn += f'</ul>\n'
    return norn
    

def custom_task(task):
    cmd = 'show version'
    result = task.run(task=netmiko_send_command, name=cmd, command_string=cmd)


def nornir_inv(hosts, groups, defaults):
    try:
        with InitNornir(inventory={ "plugin": "dictInventory",
                                    "options": {
                                        "hosts" : hosts,
                                        "groups": groups,
                                        "defaults": defaults
                        }}) as nr:
            norn = inv2html(nr)

    except Exception as e:
        norn = f'<pre>{traceback.format_exc()}</pre>'

    return norn


def nornir_run(hosts, groups, defaults):

    try:
        with InitNornir(runner = { 'plugin': "a_runner",
                                    'options': {
                                        "num_workers": 10,
                                        "emitter": emitter
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


@app.route('/')
def main():

    if "hosts" not in session:
        session['hosts'] = ydata.yhosts
        session['groups'] = ydata.ygroups
        session['defaults'] = ydata.ydefaults
        session['option'] = 'inv'

    return render_template('main.html',  
                           hosts=session['hosts'], groups=session['groups'], 
                           defaults=session['defaults'], option=session['option']
                           )

def emitter(msg, msg_type):
    if msg_type == 'update':
        socketio.emit('update',msg,namespace='/')

    elif msg_type == 'progress':
        socketio.emit('progress',msg,namespace='/')

@app.route('/nornir', methods= ['POST'])
def inv():

    yhosts = request.form['hosts']
    ygroups = request.form['groups']
    ydefaults = request.form['defaults']
    option = request.form['today']

    try:
        hosts = yaml.safe_load(yhosts)
        groups = yaml.safe_load(ygroups)
        defaults = yaml.safe_load(ydefaults)

    except Exception as e:
            norn = f'<pre>{traceback.format_exc()}</pre>'

    else:

        hosts = {} if hosts is None else hosts
        groups = {} if groups is None else groups
        defaults = {} if defaults is None else defaults

        if option == 'inv':
            norn = nornir_inv(hosts,groups,defaults)
        elif option == "task":
            norn = nornir_run(hosts,groups,defaults)

    session['hosts'] = yhosts
    session['groups'] = ygroups
    session['defaults'] = ydefaults
    session['option'] = option

    return jsonify({'output': norn})


if __name__ == '__main__':
   socketio.run(app)