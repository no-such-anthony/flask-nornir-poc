from flask import Flask, render_template, request, Markup, session, jsonify
from flask_wtf.csrf import CSRFProtect
import yaml
import json
import traceback
import ydata
from os import urandom
from pprint import pformat
from uuid import uuid4
from copy import deepcopy


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = urandom(32)

csrf = CSRFProtect(app)

app.config.update(dict(
    WTF_CSRF_SECRET_KEY=urandom(32),
))

from nornir import InitNornir
from nornir_netmiko import netmiko_send_command

# Import and register custom inventory
from nornir.core.plugins.inventory import InventoryPluginRegister
from inventory_plugin import DictInventory
InventoryPluginRegister.register("dictInventory", DictInventory)


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


def tidyIt(host, options):
    newDict = {}
    for k,v in options.items():
        if k=='extras' and v!={}:
            newDict[k] = v
            continue
        if k!='extras' and host.__getattribute__(k) != v:
            newDict[k] = v
            continue
    return newDict


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

    #norn = pformat(norn, indent=2)
    norn2yaml = yaml.safe_dump(norn, sort_keys=False)
    norn = "<pre>\n"
    norn += norn2yaml
    norn += "</pre>\n"
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
            norn = inv2yaml(nr)

    except Exception as e:
        norn = f'<pre>{traceback.format_exc()}</pre>'

    return norn


def nornir_run(hosts, groups, defaults):

    try:
        with InitNornir(runner = { 'plugin': "threaded",
                                    'options': {
                                        "num_workers": 10,
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


# We don't want to use Flask session to store app data in the client cookie.
# We could use Flask-Session with maybe SQLAlchemy/sqlite to store data 
# on the server, but lets start with something simple that is non-persistent between
# reloads of the app.
# Flask session will be used to just store the session_id
class SessionTable(object):
    def __init__(self):
        self.sessions = {}

    def add_session(self,fns):
        session_id = uuid4().hex
        self.sessions[session_id] = fns
        return session_id


class FlaskNornirSession(object):
    def __init__(self):
        self.data = {}


st = SessionTable()


@app.route('/')
def main():

    if "id" not in session:
        session['id'] = st.add_session(FlaskNornirSession())
        s = st.sessions[session['id']]
        s.data['hosts'] = ydata.yhosts
        s.data['groups'] = ydata.ygroups
        s.data['defaults'] = ydata.ydefaults
        s.data['option'] = 'inv'
        s.data['updater'] = None

    else:
        s = st.sessions[session['id']]

    return render_template('main.html',  
                           hosts=s.data['hosts'], groups=s.data['groups'], 
                           defaults=s.data['defaults'], option=s.data['option']
                           )


@app.route('/nornir', methods= ['POST'])
def nornir():

    if "id" not in session:
        norn = "Try refreshing the page.  Application must have restarted."
        return jsonify({'output': norn})

    s = st.sessions[session['id']]

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

    s.data['hosts'] = yhosts
    s.data['groups'] = ygroups
    s.data['defaults'] = ydefaults
    s.data['option'] = option

    return jsonify({'output': norn})

