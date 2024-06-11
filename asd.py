from flask import Flask, render_template
from flask_socketio import SocketIO

import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

app.logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True, debug = True)
