# --- --- IMPORTS --- ---

import ConfigParser
import json
import markdown
from os import listdir
from os.path import basename
from flask import Flask, render_template, flash, redirect, url_for, request

# --- --- GLOBAL VARS --- ---

app = Flask(__name__)
app.secret_key="Ic&Ts3IuNS*uAQbc#nur2UUAAme$8xD|"
app_config = { 'graphic': {}, 'data': {} } # Will be loaded in 'init()'
app_nav = [
	{'name': "Home", 'path': "/"},
	{'name': "About", 'path': "/about"},
	{'name': "Universes", 'path': "/universes"},
	{'name': "Characters", 'path': "/characters"}
]
data_cache = {
	'universes': {}, 'universe_tags': [],
	'characters': {}, 'character_tags': [],
}

# --- --- ROUTES --- ---

@app.route('/')
def route_root():
	flash("Welcome !")
	data = {'config': app_config, 'nav': app_nav, 'active': "/"}
	return render_template('index.html', data=data)

@app.route('/about')
def route_about():
	loadUniverseList()
	flash("Reloaded "+str(len(data_cache['universes']))+" universes.")
	loadCharacterList()
	flash("Reloaded "+str(len(data_cache['characters']))+" characters.")
	data = {'config': app_config, 'nav': app_nav, 'active': "/about"}
	return render_template('about.html', data=data)

# Universes
@app.route('/universes')
def route_universes():
	data = {'config': app_config, 'nav': app_nav, 'active': "/universes", 'list': getUniverseList()}
	if 'tags' in request.args:
		tag_filter = request.args['tags']
		print "Filtered request:", tag_filter
		data['list'] = filterList(getUniverseList(), tag_filter)
		data['search'] = tag_filter
	return render_template('universes.html', data=data)

@app.route('/universes/<univID>')
def route_universe(univID):
	info_file = open(app_config['data']['data_folder']+"/universes/"+univID+".json", "r") # TODO: escape univID
	univ_info = parseDown(json.load(info_file))
	info_file.close()
	data = {'config': app_config, 'nav': app_nav, 'active': "/universes", 'univ': univ_info}
	return render_template('universe-details.html', data=data)

# Charcaters
@app.route('/characters')
def route_characters():
	data = {'config': app_config, 'nav': app_nav, 'active': "/characters", 'list': getCharacterList()}
	if 'tags' in request.args:
		tag_filter = request.args['tags']
		print "Filtered request:", tag_filter
		data['list'] = filterList(getCharacterList(), tag_filter)
		data['search'] = tag_filter
	return render_template('characters.html', data=data)

@app.route('/characters/<charID>')
def route_character(charID):
	info_file = open(app_config['data']['data_folder']+"/characters/"+charID+".json", "r") # TODO: escape charID
	char_info = parseDown(json.load(info_file))
	info_file.close()
	data = {'config': app_config, 'nav': app_nav, 'active': "/characters", 'char': char_info}
	return render_template('character-details.html', data=data)

# --- --- DATA PROVIDERS --- ---
def parseDown(item):
	item['short_desc'] = markdown.markdown(item['short_desc'])
	item['full_desc'] = markdown.markdown(item['full_desc'])
	return item

def filterList(inList, tag):
	outList = []
	for item in inList:
		if tag in item['tags']:
			outList.append(item)
	return outList

def getUniverseList():
	return data_cache['universes'].values()

def loadUniverseList():
	folderPath = app_config['data']['data_folder']+"/universes/"
	print "Loading universes ( from:", folderPath, ")"
	# Reset
	data_cache['universe_tags'] = {}
	# Walking on each file
	files = listdir(folderPath)
	for info_file in files:
		print "\tFile:", info_file
		# Loading JSON Object from file
		filePtr = open(folderPath+info_file)
		jsonObj = json.load(filePtr)
		filePtr.close()
		# Caching data
		data_cache['universes'][jsonObj['id']] = jsonObj
		# Update tag list
		for t in jsonObj['tags']:
			if t in data_cache['universe_tags']:
				data_cache['universe_tags'][t].append(jsonObj['id'])
			else:
				data_cache['universe_tags'][t] = [jsonObj['id']]
	print "DONE ! Loaded", len(data_cache['universes']), "files."

def getCharacterList():
	return data_cache['characters']

def loadCharacterList():
	folderPath = app_config['data']['data_folder']+"/characters/"
	print "Loading characters ( from:", folderPath, ")"
	files = listdir(folderPath)
	data_cache['characters'] = []
	for info_file in files:
		print "\tLoading file:", info_file
		filePtr = open(folderPath+info_file)
		data_cache['characters'].append(json.load(filePtr))
		filePtr.close()
	print "DONE ! Loaded", len(data_cache['characters']), "files."

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
		# Graphic
		app_config['graphic']['default_universe_pic'] = config.get("graphic", "default_universe_pic")
		app_config['graphic']['default_character_pic'] = config.get("graphic", "default_character_pic")
		# Data
		app_config['data'] = {}
		app_config['data']['data_folder'] = config.get("data", "ressource_folder")
		# Config
		app.config['DEBUG'] = config.get("config", "debug")
		app.config['ip_address'] = config.get("config", "ip_address")
		app.config['port'] = config.get("config", "port")
		app.config['url'] = config.get("config", "url")
		app_config['locale'] = config.get("config", "locale")
	except IOError as e:
		print "ERROR: Could not read configs from", config_location
		print "\t>>", e
	# loading cached data
	loadUniverseList()
	loadCharacterList()

if __name__ == '__main__':
    init(app)
    app.run(
        host=app.config['ip_address'],
        port=int(app.config['port'])
    )
