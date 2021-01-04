from flask import Flask, render_template, request, Markup, session, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
from flask_socketio import send, emit
import yaml
import json
import traceback
import ydata
from os import urandom
from pprint import pformat
from uuid import uuid4


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = urandom(32)

socketio = SocketIO(app, cors_allowed_origins='*')
#socketio = SocketIO(app, cors_allowed_origins='*',logger=True, engineio_logger=True)

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

# Custom runner to update client via websocket
from nornir.core.plugins.runners import RunnersPluginRegister
from runner_plugin import UpdateRunner
RunnersPluginRegister.register("a_runner", UpdateRunner)


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

    s = st.sessions[session['id']]

    try:
        with InitNornir(runner = { 'plugin': "a_runner",
                                    'options': {
                                        "num_workers": 10,
                                        "updater": s.data['updater']
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
        s.data['updater'] = emitter

    else:
        s = st.sessions[session['id']]

    return render_template('main.html',  
                           hosts=s.data['hosts'], groups=s.data['groups'], 
                           defaults=s.data['defaults'], option=s.data['option']
                           )

@socketio.on('update')
def emitter(msg, msg_type):

    if "id" in session:
        s = st.sessions[session['id']]
        socket_id = s.data.get('socket_id', None)
        if socket_id is not None:        
            if msg_type == 'update':
                emit('update',msg,namespace='/',to=socket_id)

            elif msg_type == 'progress':
                emit('progress',msg,namespace='/',to=socket_id)


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

    s.data['socket_id'] = request.form['socket_id']
    
    s.data['hosts'] = yhosts
    s.data['groups'] = ygroups
    s.data['defaults'] = ydefaults
    s.data['option'] = option

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

    return jsonify({'output': norn})

