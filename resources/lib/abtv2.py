import re
import sys
import xbmc
import xbmcgui
import xbmcaddon
import urllib
import urlparse
import xbmcplugin
import json
from datetime import datetime
import urllib2
import os
from BeautifulSoup import BeautifulSoup
from models import Show, Episode

series_list = []
_plugId = 'plugin.video.animebaka'
ADDON = xbmcaddon.Addon(id=_plugId)
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode',None)


API_BASE_URL = "http://animebaka.tv/api/v1"
MEDIUM_THUMB_URL_BASE = "http://images.animebaka.tv/a_mth"
LARGE_CROPPED_URL_BASE = "http://images.animebaka.tv/a_lcap"
categories = ["All (A-Z)","Recently Updated","Ongoing","Genres","Completed","Movies","Search"]
shows = []
episodes = []

endpoints = {'All (A-Z)':API_BASE_URL+"/shows"}

#v1 API http://animebaka.tv/api/v1/
#GET /shows
#GET /shows/{id} // Numeric ID of show
#GET /shows/{id}/episode/{float} // Numeric ID of show & episode number (7|22|16.5)
#GET /genres 
#GET /genres/{string} // String name of genre (spaces converted to underscores) (action|shounen_ai|sci-fi)
#GET /type/movies	
#GET /shows/status/{string} // String name of status (ongoing|completed|upcoming)
#Large thumbnail: images.animebaka.tv/a_lth/{id}_lth.jpg
#Medium thumbnail: images.animebaka.tv/a_mth/{id}_mth.jpg
#Small thumbnail: images.animebaka.tv/a_sth/{id}_sth.jpg
#Large cropped: images.animebaka.tv/a_lcap/{id}_lcap.jpg
#Medium cropped: images.animebaka.tv/a_mcap/{id}_mcap.jpg

def get_show_meta(name):
	tvdb = xbmcaddon.Addon('script.module.metahandler')
	__cwd__ = xbmc.translatePath(tvdb.getAddonInfo('path')).decode("utf-8")
	BASE_RESOURCE_PATH = os.path.join(__cwd__, 'lib', 'metahandler')
	sys.path.append(BASE_RESOURCE_PATH)
	from thetvdbapi import TheTVDB
	try:
		tv = TheTVDB(language='en')

		split = name.split(" ")
		if len(split) > 1:
			name = split[0]+" "+split[1]

		show_list = tv.get_matching_shows(name,language='all')
		#print "Searching %s" % (name)
		if len(show_list) > 0:
			show_id = show_list[0][0]
			images = tv.get_show_image_choices(show_id)
			res = {}
			for im in images:
				if 'fanart' in im[1]:
					res['fanart'] = im[0]
				if 'poster' in im[1]:
					res['poster'] = im[0]
			return res
	except Exception as e:
		return None
	return None

def get_shows(endpoint,genre='',return_results=False):
	global shows
	shows = []
	if 'All' in endpoint:
		url = API_BASE_URL+"/shows"
	elif 'Ongoing' in endpoint:
		url = API_BASE_URL+"/shows/status/ongoing"
	elif 'Completed' in endpoint:
		url = API_BASE_URL+"/shows/status/completed"
	elif 'Upcoming' in endpoint:
		url = API_BASE_URL+"/shows/status/upcoming"
	elif 'Movies' in endpoint:
		url = API_BASE_URL+"/type/Movie"
	else:
		url = API_BASE_URL+"/genre/"+genre

	request = urllib2.urlopen(url)
	response = json.loads(request.read())
	for load in response['result']:
		show = Show(load)
		shows.append(show)

	if return_results:
		return shows

	for show in shows:
		label = show.title+"[COLOR red]("+show.views+" views)[/COLOR]"
		url = 'plugin://%s/?mode=episode_list&id=%s' % (_plugId,show.id)
		li = xbmcgui.ListItem(label=show.title+" [COLOR red]("+show.views+" views)[/COLOR]",iconImage=MEDIUM_THUMB_URL_BASE+"/"+show.id+"_mth.jpg",thumbnailImage=MEDIUM_THUMB_URL_BASE+"/"+show.id+"_mth.jpg",path=url)
		fanart = ADDON.getAddonInfo('path') + '/fanart.jpg'
		li.setProperty('fanart_image',fanart)
		xbmcplugin.addDirectoryItem(handle=addon_handle,url=url,listitem=li,isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)


def parse_page_for_link(link):
	page = urllib2.urlopen(link)
	soup = BeautifulSoup(page.read())
	thumb = soup.find("a", {"id": "download"})
	return thumb['href']


def get_shows_by_status(status):
	request = urllib2.urlopen(API_BASE_URL+"/shows/status/"+status)
	response = json.loads(request.read())
	for load in response['result']:
		show = Show(load)
		shows.append(show)

def get_episode_mirrors(show_id,episode):
	request = urllib2.urlopen(API_BASE_URL+"/shows/"+show_id+"/episode/"+episode)
	response = json.loads(request.read())
	ep = response['result']
	print ep
	label = "[COLOR red]"+ep['title']+"[/COLOR] Episode "+episode
	li = xbmcgui.ListItem(label=label,iconImage=MEDIUM_THUMB_URL_BASE+"/"+ep['id']+"_lcap.jpg",thumbnailImage=LARGE_CROPPED_URL_BASE+"/"+ep['id']+"_lcap.jpg",path=None)
	xbmcplugin.addDirectoryItem(handle=addon_handle,url=None,listitem=li,isFolder=False)

	for mirror in ep['mirrors']:
		url = 'plugin://%s/?mode=play&link=%s&service=%s' % (_plugId,mirror['video_url'],mirror['service'])
		li = xbmcgui.ListItem(label="[COLOR red]["+mirror['quality']+"][/COLOR] - "+mirror['service'],iconImage=LARGE_CROPPED_URL_BASE+"/"+ep['id']+"_lcap.jpg",thumbnailImage=LARGE_CROPPED_URL_BASE+"/"+ep['id']+"_lcap.jpg",path=None)
		xbmcplugin.addDirectoryItem(handle=addon_handle,url=url,listitem=li,isFolder=False)

	xbmcplugin.endOfDirectory(addon_handle)

def get_show_episodes(show_id):

	request = urllib2.urlopen(API_BASE_URL+"/shows/"+show_id)
	response = json.loads(request.read())
	episodes = response['result']

	label = "[COLOR red]"+episodes['title']+"[/COLOR]"
	li = xbmcgui.ListItem(label=label,iconImage=LARGE_CROPPED_URL_BASE+"/"+episodes['id']+"_lcap.jpg",thumbnailImage=LARGE_CROPPED_URL_BASE+"/"+episodes['id']+"_lcap.jpg",path=None)
	xbmcplugin.addDirectoryItem(handle=addon_handle,url=None,listitem=li,isFolder=False)

	for i in range(len(episodes['episodes']), 0, -1):
		url = 'plugin://%s/?mode=episode_mirror&episode=%s&show=%s' % (_plugId,i,episodes['id'])
		li = xbmcgui.ListItem(label=str(i),iconImage=LARGE_CROPPED_URL_BASE+"/"+episodes['id']+"_lcap.jpg",thumbnailImage=LARGE_CROPPED_URL_BASE+"/"+episodes['id']+"_lcap.jpg",path=None)
		xbmcplugin.addDirectoryItem(handle=addon_handle,url=url,listitem=li,isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)

def get_recently_updated():
	global episodes
	request = urllib2.urlopen(API_BASE_URL+"/recent/episodes?start=0&limit=48")
	response = json.loads(request.read())
	for load in response['result']:
		ep = Episode(load)
		episodes.append(ep)

	for episode in episodes:
		url = 'plugin://%s/?mode=episode_mirror&episode=%s&show=%s' % (_plugId,episode.episode_number,episode.show_id)
		li = list_item(title="[COLOR red]"+episode.title+"[/COLOR] Ep "+episode.episode_number+" - [COLOR yellow]"+episode.get_relative_time()+"[/COLOR]",icon=MEDIUM_THUMB_URL_BASE+"/"+episode.show_id+"_mth.jpg",url=None)
		li.setProperty("summary",episode.synopsis)
		fanart = get_show_meta(episode.title)

		if fanart is None:
			li.setProperty('fanart_image',ADDON.getAddonInfo('path') + '/fanart.jpg')
		else:
			if fanart['fanart']:
				li.setProperty('fanart_image',fanart['fanart'])
			if fanart['poster']:
				li.setThumbnailImage (fanart['poster'])

		add_directory_item(url=url,li=li,isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)

def get_genre_list():
	xbmcplugin.setContent(addon_handle,'files')
	request = urllib2.urlopen(API_BASE_URL+"/genres")
	response = json.loads(request.read())
	for load in response['result']:
		icon = ADDON.getAddonInfo('path') + '/icon.png'
		url = 'plugin://%s/?mode=load_genre&genre=%s' % (_plugId,load['name'])
		li = list_item(title="[COLOR red]"+load['name']+"[/COLOR]",icon=icon,url=None)
		li.setProperty("summary",load['description'])
		add_directory_item(url=url,li=li,isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)


def on_search(query):
	print query
	shows = get_shows(endpoint='All',genre='',return_results=True)
	search_results = (x for x in shows if query.lower() in str(x.title).lower())

	for show in search_results:
		label = show.title+"[COLOR red]("+show.views+" views)[/COLOR]"
		url = 'plugin://%s/?mode=episode_list&id=%s' % (_plugId,show.id)
		li = xbmcgui.ListItem(label=show.title+" [COLOR red]("+show.views+" views)[/COLOR]",iconImage=MEDIUM_THUMB_URL_BASE+"/"+show.id+"_mth.jpg",thumbnailImage=MEDIUM_THUMB_URL_BASE+"/"+show.id+"_mth.jpg",path=url)
		fanart = ADDON.getAddonInfo('path') + '/fanart.jpg'
		li.setProperty('fanart_image',fanart)
		xbmcplugin.addDirectoryItem(handle=addon_handle,url=url,listitem=li,isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)

def list_item(title,icon,url):
	return xbmcgui.ListItem(label=title,iconImage=icon,path=url)

def add_directory_item(url,li,isFolder):
	xbmcplugin.addDirectoryItem(handle=addon_handle,url=url,listitem=li,isFolder=isFolder)

def main():
	print args
	global categories
	if mode is None:
		xbmcplugin.setContent(addon_handle,'files')
		for category in categories:
			icon = ADDON.getAddonInfo('path') + '/icon.png'
			url = 'plugin://%s/?mode=current_category&category=%s' % (_plugId,category)
			li = list_item(title="[COLOR red]"+category+"[/COLOR]",icon=icon,url=url)
			fanart = ADDON.getAddonInfo('path') + '/fanart.jpg'
			li.setProperty('fanart_image',fanart)
			add_directory_item(url=url,li=li,isFolder=True)
		xbmcplugin.endOfDirectory(addon_handle)
	elif 'current_category' in mode[0]:
		global shows
		xbmcplugin.setContent(addon_handle,'movies')
		if categories[0] in args.get('category')[0]:
			get_shows('All')
		elif categories[1] in args.get('category')[0]:
			get_recently_updated()
		elif categories[2] in args.get('category')[0]:
			get_shows('Ongoing')
		elif categories[3] in args.get('category')[0]:
			get_genre_list()
		elif categories[4] in args.get('category')[0]:
			get_shows('Completed')
		elif categories[5] in args.get('category')[0]:
			get_shows('Movies')
		elif categories[6] in args.get('category')[0]:
			dialog = xbmcgui.Dialog()
			result = dialog.input('SEARCH', '', type=xbmcgui.INPUT_ALPHANUM)
			if result:
				text = result.encode('ascii','ignore')
				on_search(text)
	elif 'load_genre' in mode[0]:
		xbmcplugin.setContent(addon_handle,'movies')
		get_shows(endpoint='',genre=args.get('genre')[0])
	elif 'episode_list' in mode[0]:
		xbmcplugin.setContent(addon_handle,'episodes')
		get_show_episodes(args.get('id')[0])
	elif 'episode_mirror' in mode[0]:
		xbmcplugin.setContent(addon_handle,'mirrors')
		get_episode_mirrors(args.get('show')[0],args.get('episode')[0])
	elif 'play' in mode[0]:
		# handle other mirrors , i,e: OpenLoad https://openload.co/f/NuHzNUQGqGI
		link = parse_page_for_link(args.get('link')[0])
		xbmc.executebuiltin("PlayMedia(%s)" % link)
