from flask import Flask, render_template, request, Markup, session, jsonify
from flask_wtf.csrf import CSRFProtect
from nornir_control import nornir_inv, nornir_run
import yaml
import traceback
import ydata
from os import urandom
from uuid import uuid4
from queue import Queue


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = urandom(32)

csrf = CSRFProtect(app)

app.config.update(dict(
    WTF_CSRF_SECRET_KEY=urandom(32),
))


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
        s.data['updater'] = updater_poll
        s.data['updates'] = Queue()
        s.data['progress'] = ''
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

    s.data['hosts'] = request.form['hosts']
    s.data['groups'] = request.form['groups']
    s.data['defaults'] = request.form['defaults']
    s.data['option'] = request.form['today']

    s.data['progress'] = ''
    s.data['updates'] = Queue()

    try:
        hosts = yaml.safe_load(s.data['hosts'])
        groups = yaml.safe_load(s.data['groups'])
        defaults = yaml.safe_load(s.data['defaults'])
        updater = s.data['updater']

    except Exception as e:
            norn = f'<pre>{traceback.format_exc()}</pre>'

    else:

        hosts = {} if hosts is None else hosts
        groups = {} if groups is None else groups
        defaults = {} if defaults is None else defaults

        if s.data['option'] == 'inv':
            norn = nornir_inv(hosts, groups, defaults)
        elif s.data['option'] == "task":
            norn = nornir_run(hosts, groups, defaults, updater)

    return jsonify({'output': norn})


def updater_poll(msg, msg_type):
    s = st.sessions[session['id']]

    if msg_type == 'update':
        s.data['updates'].put(msg)

    elif msg_type == 'progress':
        s.data['progress'] = msg

    
@app.route('/nornir/poll')
def poll():
    progress = ''
    updates = ''
    if 'id' in session:
        s = st.sessions[session['id']]
        while s.data['updates'].qsize()!=0:
            update = s.data['updates'].get()
            updates += f'<li>{update}</li>\n'
        progress = s.data['progress']
    else:
        pass

    return jsonify({'updates': updates,
                    'progress': progress })
        
