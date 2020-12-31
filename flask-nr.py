from flask import Flask, render_template, request, Markup, session
import yaml
import traceback
import ydata
from os import urandom
from pprint import pformat


app = Flask(__name__, template_folder='', static_folder='')
app.secret_key = urandom(32)


from nornir import InitNornir
from nornir_netmiko import netmiko_send_command
from nornir.core.plugins.inventory import InventoryPluginRegister
from dictInventory import DictInventory
InventoryPluginRegister.register("dictInventory", DictInventory)


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
    norn = "<pre>"
    for device_name, multi_result in results.items():
        norn += "="*30 + f" {device_name} " + "="*30 + "\n"
        for result in multi_result:
            norn += result.name + "\n"
            if not isinstance(result.result, type(None)):
                norn += pformat(result.result) + "\n"
    norn += "</pre>"
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
    

@app.route('/',methods = ['POST', 'GET'])
def main():

    if request.method == 'POST':
        yhosts = request.form['hosts']
        ygroups = request.form['groups']
        ydefaults = request.form['defaults']
        option = request.form['today']

        hosts = yaml.safe_load(yhosts)
        groups = yaml.safe_load(ygroups)
        defaults = yaml.safe_load(ydefaults)

        hosts = {} if hosts is None else hosts
        groups = {} if groups is None else groups
        defaults = {} if defaults is None else defaults

        try:
            with InitNornir(inventory={ "plugin": "dictInventory",
                                        "options": {
                                            "hosts" : hosts,
                                            "groups": groups,
                                            "defaults": defaults
                            }}) as nr:

                if option == 'inv':
                    norn = inv2html(nr)

                if option == "task":
                    results = nr.run(task=netmiko_send_command, name="show version", command_string="show version")
                    norn = results2html(results)

        except Exception as e:
            norn = traceback.format_exc()

        session['hosts'] = yhosts
        session['groups'] = ygroups
        session['defaults'] = ydefaults
        session['norn'] = Markup(norn)
        session['option'] = option

    else:
        if "hosts" not in session:
            session['hosts'] = ydata.yhosts
            session['groups'] = ydata.ygroups
            session['defaults'] = ydata.ydefaults
            session['norn'] = ''
            session['option'] = 'inv'


    return render_template('main.html', norn=session['norn'], 
                           hosts=session['hosts'], groups=session['groups'], 
                           defaults=session['defaults'], option=session['option']
                           )


if __name__ == '__main__':
   app.run()