# flask-nornir-poc
A proof of concept flask app with nornir

Requirements

- pip install flask
- pip install flask-wtf
- pip install nornir
- pip install nornir-netmiko
- pip install pyaml
- pip install Flask-SocketIO
- pip install eventlet

Run

- gunicorn --worker-class eventlet -w 1 flask_nr:app

Requires "pip install gunicorn".  For some reason when starting with "python flask_nr.py" the socketio messages stop working.

ydata.py contains default inventory data in yaml format with a couple of Cisco always-on instances.

Branches

- main - jquery ajax
- socket - jquery ajax with socketio progress updates
- poll - jquery ajax with polling for progress updates

Some helpful flask links

- https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
- https://blog.miguelgrinberg.com/post/how-secure-is-the-flask-user-session
- https://flask-socketio.readthedocs.io/en/latest/
