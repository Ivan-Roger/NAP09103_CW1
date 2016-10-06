import ConfigParser
import json
from flask import Flask, render_template, flash
app = Flask(__name__)
app.secret_key="Ic&Ts3IuNS*uAQbc#nur2UUAAme$8xD|"
app_config = { # Will be loaded in 'init()'
	'graphic': {
		'default_universe_pic': "img/default_universe_pic.jpg"
	},
	'data': {}
}
app_nav = [
	{'name': "Home", 'path': "/"},
	{'name': "About", 'path': "/about"},
	{'name': "Universes", 'path': "/universes"},
	{'name': "Characters", 'path': "/characters"}
]

# --- --- ROUTES --- ---

@app.route('/')
def route_root():
	flash("Welcome !")
	data = {'config': app_config, 'nav': app_nav, 'active': "/"}
	return render_template('index.html', data=data)

@app.route('/about')
def route_about():
	data = {'config': app_config, 'nav': app_nav, 'active': "/about"}
	return render_template('about.html', data=data)

@app.route('/universes')
def route_universes():
	index_file = open(app_config['data']['data_folder']+"/universes/"+app_config['data']['index_file'], "r")
	univ_list = json.load(index_file)
	data = {'config': app_config, 'nav': app_nav, 'active': "/universes", 'list': univ_list}
	return render_template('universes.html', data=data)

@app.route('/universes/<univID>')
def route_universe(univID):
	data = {'config': app_config, 'nav': app_nav, 'active': "/universes", 'univ': {}}
	return render_template('universe-details.html', data=data)

@app.route('/characters')
def route_characters():
	data = {'config': app_config, 'nav': app_nav, 'active': "/characters", 'list': []}
	return render_template('characters.html', data=data)

@app.route('/characters/<charID>')
def route_character(charID):
	data = {'config': app_config, 'nav': app_nav, 'active': "/characters", 'char': {}}
	return render_template('character-details.html', data=data)

# --- --- ERRORS --- ---

@app.errorhandler(404)
def error_notFound(error):
	data = {'config': app_config, 'nav': app_nav, 'error': error, 'active': ""}
	return render_template('e404.html', data=data)

# --- --- SETUP --- ---

def init(app):
	config = ConfigParser.ConfigParser ()
	try:
		config_location = "etc/defaults.cfg"
		config.read(config_location)
		# App
		app_config['app_name'] = config.get("app", "name")
		app_config['app_author'] = config.get("app", "author")
		app_config['app_contact'] = config.get("app", "contact")
		# Data
		app_config['data'] = {}
		app_config['data']['data_folder'] = config.get("data", "ressource_folder")
		app_config['data']['index_file'] = config.get("data", "index_file")
		# Config
		app.config['DEBUG'] = config.get("config", "debug")
		app.config['ip_address'] = config.get("config", "ip_address")
		app.config['port'] = config.get("config", "port")
		app.config['url'] = config.get("config", "url")
		app_config['locale'] = config.get("config", "locale")
	except IOError as e:
		print "ERROR: Could not read configs from", config_location
		print "\t>>", e

if __name__ == '__main__':
    init(app)
    app.run(
        host=app.config['ip_address'],
        port=int(app.config['port'])
    )
