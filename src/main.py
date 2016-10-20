# --- --- IMPORTS --- ---

import ConfigParser
import json
import markdown
from math import ceil
from urllib import urlencode
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
	data['search'] = {}
	if 'tags' in request.args and not request.args['tags'] == "":
		tag_filter = request.args['tags'].split(",")
		print "Filtered by tags:", tag_filter
		data['list'] = filterListByTags(data['list'], tag_filter)
		data['search']['tags'] = tag_filter
	if 'text' in request.args and not request.args['text'] == "":
		text_filter = request.args['text']
		print "Filtered by keyword:", text_filter
		data['list'] = filterListByKeyword(data['list'], text_filter)
		data['search']['text'] = text_filter
	data = splitListIntoPages(data, request.args);
	return render_template('universes.html', data=data)

@app.route('/universes/<univID>')
def route_universe(univID):
	info_file = open(app_config['data']['data_folder']+"/universes/"+univID+".json", "r") # TODO: escape univID
	univ_info = parseDown( fillUniverseData( json.load(info_file) ) )
	info_file.close()
	data = {'config': app_config, 'nav': app_nav, 'active': "/universes", 'univ': univ_info}
	return render_template('universe-details.html', data=data)

# Characters
@app.route('/characters')
def route_characters():
	data = {'config': app_config, 'nav': app_nav, 'active': "/characters", 'list': getCharacterList()}
	data['search'] = {}
	if 'tags' in request.args and not request.args['tags'] == "":
		tag_filter = request.args['tags'].split(",")
		print "Filtered by tags:", tag_filter
		data['list'] = filterListByTags(data['list'], tag_filter)
		data['search']['tags'] = tag_filter
	if 'text' in request.args and not request.args['text'] == "":
		text_filter = request.args['text']
		print "Filtered by keyword:", text_filter
		data['list'] = filterListByKeyword(data['list'], text_filter)
		data['search']['text'] = text_filter
	if 'univ' in request.args and request.args['univ'] in data_cache['universes']:
		univ_filter = request.args['univ']
		print "Filtered by universe:", univ_filter
		data['list'] = filterListByUniverse(data['list'], univ_filter)
		data['search']['univ'] = data_cache['universes'][univ_filter]['name']
	data = splitListIntoPages(data, request.args);
	return render_template('characters.html', data=data)

@app.route('/characters/<charID>')
def route_character(charID):
	info_file = open(app_config['data']['data_folder']+"/characters/"+charID+".json", "r") # TODO: escape charID
	char_info = parseDown( fillCharacterData( json.load(info_file) ) )
	info_file.close()
	data = {'config': app_config, 'nav': app_nav, 'active': "/characters", 'char': char_info}
	return render_template('character-details.html', data=data)

# --- --- ERRORS --- --- #

@app.errorhandler(404)
def error_notFound(error):
	data = {'config': app_config, 'nav': app_nav, 'error': error, 'active': ""}
	return render_template('e404.html', data=data)

# --- --- Processing funcions --- --- #

def splitListIntoPages(data, urlArgs):
	args = urlArgs.to_dict()
	dList = data['list']
	PAGE_LENGTH = app_config['graphic']['items_per_page']
	NB_PAGES = int( ceil( len(dList)/float(PAGE_LENGTH) ) )
	page = int(args.pop('page')) if 'page' in args else 1
	iMin = (page-1)*PAGE_LENGTH
	iMax = (page)*PAGE_LENGTH
	data['list'] = dList[iMin:iMax]
	data['pages'] = {'cur': page, 'list': []}
	if page > 1:
		data['pages']['prev'] = (page-1)
	if page < NB_PAGES:
		data['pages']['next'] = (page+1)
	data['pages']['list'] = range(max(1, page-3), min(NB_PAGES, page+3)+1)
	url_prefix = urlencode(args)
	data['pages']['prefix'] = "?"+url_prefix+( "" if url_prefix == "" else "&" )+"page="
	return data

def parseDown(item):
	item['short_desc'] = markdown.markdown(item['short_desc'])
	if 'full_desc' in item:
		item['full_desc'] = markdown.markdown(item['full_desc'])
	return item

def filterListByTags(inList, tags):
	outList = []
	tag_set = set(tags)
	for item in inList:
		if tag_set.issubset(set(item['tags'])):
			outList.append(item)
	return outList

def filterListByUniverse(inList, univ):
	outList = []
	for item in inList:
		if item['universe']['id'] == univ:
			outList.append(item)
	return outList

def filterListByKeyword(inList, keyword):
	outList = []
	for item in inList:
		if keyword in item['name'] or keyword in item['short_desc']:
			outList.append(item)
	return outList

# Universes
def getUniverseList():
	return data_cache['universes'].values()

def minUniverseData(univ):
	return {
		'id': univ['id'],
		'name': univ['name'],
		'short_desc': univ['short_desc'],
		'pic': univ['pic'],
		'tags': univ['tags']
	}

def fillUniverseData(univ):
	res = univ
	if 'characters' in res['related']:
		rel_char = res['related']['characters']
		res['related']['characters'] = []
		for charID in rel_char:
			res['related']['characters'].append(data_cache['characters'][charID])
	return res

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
		jsonObj = parseDown( minUniverseData( json.load(filePtr) ) )
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

# Characters
def getCharacterList():
	return data_cache['characters'].values()

def minCharacterData(char):
	res_univ = data_cache['universes'][char['universe']]
	univ_info = {'id': res_univ['id'], 'name': res_univ['name']}
	return {
		'id': char['id'],
		'name': char['name'],
		'universe': univ_info,
		'short_desc': char['short_desc'],
		'pic': char['pic'],
		'tags': char['tags']
	}

def fillCharacterData(char):
	res = char
	# Universe
	res['universe'] = data_cache['universes'][res['universe']]
	# Allies
	res_allies = res['allies']
	res['allies'] = []
	for charID in res_allies:
		res['allies'].append(data_cache['characters'][charID])
	# Enemies
	res_enemies = res['enemies']
	res['enemies'] = []
	for charID in res_enemies:
		res['enemies'].append(data_cache['characters'][charID])
	return res

def loadCharacterList():
	folderPath = app_config['data']['data_folder']+"/characters/"
	print "Loading characters ( from:", folderPath, ")"
	# Reset
	data_cache['character_tags'] = {}
	# Walking on each file
	files = listdir(folderPath)
	for info_file in files:
		print "\tFile:", info_file
		# Loading JSON Object from file
		filePtr = open(folderPath+info_file)
		jsonObj = parseDown( minCharacterData( json.load(filePtr) ) )
		filePtr.close()
		# Caching data
		data_cache['characters'][jsonObj['id']] = jsonObj
		# Update tag list
		for t in jsonObj['tags']:
			if t in data_cache['character_tags']:
				data_cache['character_tags'][t].append(jsonObj['id'])
			else:
				data_cache['character_tags'][t] = [jsonObj['id']]
	print "DONE ! Loaded", len(data_cache['characters']), "files."

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
		app_config['graphic']['items_per_page'] = int(config.get("graphic", "items_per_page"))
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
