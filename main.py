import ConfigParser
from flask import Flask, render_template, flash
app = Flask(__name__)
app.secret_key="Ic&Ts3IuNS*uAQbc#nur2UUAAme$8xD|"

# --- --- ROUTES --- ---

@app.route('/')
def route_root():
	flash("Welcome !")
	return render_template('index.html')

# --- --- SETUP --- ---

@app.route('/static/<path:filepath>')
def serveStatic(filepath):
	return send_from_directory('static', filepath)

def init(app):
    config = ConfigParser.ConfigParser ()
    try:
        config_location = "etc/defaults.cfg"
        config.read(config_location)
        app.config['DEBUG'] = config.get("config", "debug")
        app.config['ip_address'] = config.get("config", "ip_address")
        app.config['port'] = config.get("config", "port")
        app.config['url'] = config.get("config", "url")
        app.config['locale'] = config.get("config", "locale")
    except:
        print "Could not read configs from: ", config_location

if __name__ == '__main__':
    init(app)
    app.run(
        host=app.config['ip_address'],
        port=int(app.config['port'])
    )
