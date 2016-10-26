# --- --- IMPORTS --- ---

import ConfigParser
import json
import markdown
import logging
from logging.handlers import RotatingFileHandler
from math import ceil
from urllib import urlencode
from os import listdir
from os.path import basename
from flask import Flask, render_template, flash, redirect, url_for, request

# --- --- GLOBAL VARS --- ---

app = Flask(__name__)
app.secret_key="Ic&Ts3IuNS*uAQbc#nur2UUAAme$8xD|"
# app_config: Will be loaded in 'init()'
app_config = { 'graphic': {}, 'data': {}, 'code': {}, 'logging': {} }
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

class NotFoundEx(Exception):
	msg = "Ressource not found."

	def __init__(self, msg=None):
		Exception.__init__(self)
		if msg is not None:
			self.msg=msg

	def __str__(self):
		return self.msg

# --- --- ROUTES --- ---

@app.route('/')
def route_root():
	logRequest()
	flash("Welcome !")
	data = {'config': app_config, 'nav': app_nav, 'active': "/", 'infos': {}}
	data['infos']['nb_universes'] = len(data_cache['universes'])
	data['infos']['nb_characters'] = len(data_cache['characters'])
	return render_template('index.html', data=data)

@app.route('/about')
def route_about():
	logRequest()
	sourcesFile = open("../doc/sources.md", "r")
	sourcesMD = markdown.markdown(sourcesFile.read())
	sourcesFile.close()
	data = {'config': app_config, 'nav': app_nav, 'active': "/about", 'sources': sourcesMD, 'code': app_config['code']}
	return render_template('about.html', data=data)

@app.route('/reload')
def route_reload():
	logRequest()
	loadUniverseList()
	flash("Reloaded "+str(len(data_cache['universes']))+" universes.")
	loadCharacterList()
	flash("Reloaded "+str(len(data_cache['characters']))+" characters.")
	return redirect(url_for('route_root'))

# Universes
@app.route('/universes')
def route_universes():
	logRequest()
	data = {'config': app_config, 'nav': app_nav, 'active': "/universes", 'list': getUniverseList()}
	data['search'] = {}
	if 'tags' in request.args and not request.args['tags'] == "":
		tag_filter = request.args['tags'].split(",")
		app.logger.info("Filtered by tags: "+str(tag_filter))
		data['list'] = filterListByTags(data['list'], tag_filter)
		data['search']['tags'] = set(tag_filter)
	if 'text' in request.args and not request.args['text'] == "":
		text_filter = request.args['text']
		app.logger.info("Filtered by keyword: "+text_filter)
		data['search']['text'] = text_filter
		data['list'] = filterListByKeyword(data['list'], text_filter.lower())
	data = splitListIntoPages(data, request.args)
	data = getLinks(data, request.args)
	return render_template('universes.html', data=data)

@app.route('/universes/<univID>')
def route_universe(univID):
	logRequest()
	fileName = app_config['data']['data_folder']+"/universes/"+univID+".json"
	app.logger.info("LOAD - Loading universe #"+univID+" (from: "+fileName+")")
	try:
		try:
			info_file = open(fileName, "r") # TODO: escape univID
			univ_info = json.load(info_file)
			info_file.close()
			data_cache['universes'][univID] = minUniverseData(univ_info) # Update cache
			univ_info = fillUniverseData(univ_info) # Fill data
			data = {'config': app_config, 'nav': app_nav, 'active': "/universes", 'univ': parseDown(univ_info)}
			return render_template('universe-details.html', data=data)
		except IOError:
			raise NotFoundEx()
			info_file.close()
	except NotFoundEx as e:
		app.logger.error("ERROR - "+str(e)+" / #"+univID)
		raise e

# Characters
@app.route('/characters')
@app.route('/universes/<univID>/characters')
def route_characters(univID=None):
	logRequest()
	data = {'config': app_config, 'nav': app_nav, 'active': "/characters", 'list': getCharacterList()}
	data['search'] = {}
	if 'tags' in request.args and not request.args['tags'] == "":
		tag_filter = request.args['tags'].split(",")
		app.logger.info("Filtered by tags: "+str(tag_filter))
		data['list'] = filterListByTags(data['list'], tag_filter)
		data['search']['tags'] = set(tag_filter)
	if 'text' in request.args and not request.args['text'] == "":
		text_filter = request.args['text']
		app.logger.info("Filtered by keyword: "+text_filter)
		data['search']['text'] = text_filter
		data['list'] = filterListByKeyword(data['list'], text_filter.lower())
	if univID is not None:
		if univID not in data_cache['universes']:
			raise NotFoundEx("No such universe")
		app.logger.info("Filtered by universe: "+univID)
		data['list'] = filterListByUniverse(data['list'], univID)
		data['search']['univ'] = data_cache['universes'][univID]['name']
	data = splitListIntoPages(data, request.args);
	data = getLinks(data, request.args)
	return render_template('characters.html', data=data)

@app.route('/universes/<univID>/characters/<charID>')
def route_character(univID,charID):
	logRequest()
	fileName = app_config['data']['data_folder']+"/characters/"+charID+".json" # TODO: escape charID
	app.logger.info("LOAD - Loading character #"+charID+" (from: "+fileName+")")
	try:
		try:
			if univID not in data_cache['universes']:
				raise NotFoundEx("No such universe")
			info_file = open(fileName, "r")
			char_info = json.load(info_file)
			info_file.close()
			if char_info['universe'] != univID:
				raise NotFoundEx("Wrong universe")
			data_cache['characters'][charID] = minCharacterData(char_info) # Update cache
			char_info = fillCharacterData(char_info) # Fill data
			data = {'config': app_config, 'nav': app_nav, 'active': "/characters", 'char': parseDown(char_info)}
			return render_template('character-details.html', data=data)
		except IOError:
			raise NotFoundEx()
			info_file.close()
	except NotFoundEx as e:
		app.logger.error("ERROR - "+str(e)+" / #"+charID)
		raise e


# --- --- ERRORS --- --- #

@app.errorhandler(404)
@app.errorhandler(NotFoundEx)
def error_notFound(error):
	data = {'config': app_config, 'nav': app_nav, 'error': error, 'active': ""}
	app.logger.error("ERROR - "+error)
	return render_template('e404.html', data=data), 404

@app.errorhandler(500)
def error_notFound(error):
	app.logger.error("ERROR - "+str(error))

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

def getLinks(data, urlArgs):
	args = urlArgs.to_dict()
	if args.has_key('page'):
		args.pop('page')
	data['links'] = {}
	# Prefix tags
	args_tags = args.copy()
	tags_val = ""
	if args_tags.has_key('tags'):
		tags_val = args_tags.pop('tags')
	tags_prefix = urlencode(args_tags)
	data['links']['prefix_tags'] = "?"+tags_prefix+( "" if tags_prefix == "" else "&" )+"tags="
	if tags_val!="":
		data['links']['prefix_tags'] += tags_val+","
	# Prefix univ
	if data['active']=="/characters":
		data['links']['suffix_univ'] = "?"+urlencode(args)
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
		if keyword in item['name'].lower() or keyword in item['short_desc'].lower():
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
	# if 'characters' in res['related']:
	# 	rel_char = res['related']['characters']
	# 	res['related']['characters'] = []
	# 	for charID in rel_char:
	# 		res['related']['characters'].append(data_cache['characters'][charID])
	return res

def loadUniverseList():
	folderPath = app_config['data']['data_folder']+"/universes/"
	app.logger.info("LOAD - Loading universes (from: "+folderPath+")")
	# Reset
	data_cache['universe_tags'] = {}
	# Walking on each file
	files = listdir(folderPath)
	for info_file in files:
		app.logger.debug("\tFile: "+info_file)
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
	count = len(data_cache['universes'])
	app.logger.info("DONE! - Loaded "+str(count)+" universes.")

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
	app.logger.info("LOAD - Loading characters (from: "+folderPath+")")
	# Reset
	data_cache['character_tags'] = {}
	# Walking on each file
	files = listdir(folderPath)
	for info_file in files:
		app.logger.debug("\tFile: "+info_file)
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
	count = len(data_cache['characters'])
	app.logger.info("DONE! - Loaded "+str(count)+" characters.")

# --- --- SETUP --- ---

def logRequest():
	app.logger.info(request.method+": "+request.url)

def init(app):
	app.logger.info("INIT - Initializing application ...")
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
		app_config['data']['data_folder'] = config.get("data", "ressource_folder")
		# Code
		app_config['code']['repo_url'] = config.get("code", "repo_url")
		app_config['code']['repo_name'] = config.get("code", "repo_name")
		# Main config
		app.config['DEBUG'] = config.get("config", "debug")
		app.config['ip_address'] = config.get("config", "ip_address")
		app.config['port'] = config.get("config", "port")
		app.config['url'] = config.get("config", "url")
		#app_config['locale'] = config.get("config", "locale")
		# Logging
		app_config['logging']['file'] = config.get("logging", "name")
		app_config['logging']['location'] = config.get("logging", "location")
		app_config['logging']['level'] = config.get("logging", "level")
	except IOError as e:
		app.logger.error("ERROR - Could not read configs from: "+config_location)
		app.logger.error("\t>>"+str(e))
	# loading cached data
	loadUniverseList()
	loadCharacterList()

def logs(app):
	log_pathname = app_config['logging']['location'] + app_config['logging']['file']
	file_handler = RotatingFileHandler(log_pathname, maxBytes=1024*1024*10, backupCount=1024)
	file_handler.setLevel(app_config['logging']['level'])
	formatter = logging.Formatter("%(levelname)s | %(asctime)s | %(module)s | %(funcName)s | %(message)s")
	file_handler.setFormatter(formatter)
	app.logger.setLevel(app_config['logging']['level'])
	app.logger.addHandler(file_handler)

if __name__ == '__main__':
	init(app)
	logs(app)
	app.logger.info("START - Application started !")
	app.run(
	    host=app.config['ip_address'],
	    port=int(app.config['port'])
	)
	app.logger.info("STOP - Application ended !")
