import re
import sys
import xbmc
import xbmcgui
import xbmcaddon
import urllib
import urlparse
import xbmcplugin
from datetime import datetime
import urllib2
import os
from BeautifulSoup import BeautifulSoup

series_list = []
_plugId = 'plugin.video.animebaka'
ADDON = xbmcaddon.Addon(id=_plugId)
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode',None)


class Episode(object):

	def __init__(sekf,episode,link):
		self.episode = episode
		self.link = link

class Series(object):

	video_url = ''
	thumbnail = ''
	next_page = ''
	def __init__(self,title,sub,thumb,link):
		self.title = title
		self.sub = sub
		self.thumb = thumb
		self.link = link


def get_show_meta(name):
	tvdb = xbmcaddon.Addon('script.module.metahandler')
	__cwd__ = xbmc.translatePath(tvdb.getAddonInfo('path')).decode("utf-8")
	BASE_RESOURCE_PATH = os.path.join(__cwd__, 'lib', 'metahandler')
	sys.path.append(BASE_RESOURCE_PATH)
	from thetvdbapi import TheTVDB
	try:
		tv = TheTVDB(language='jp')
		show_list = tv.get_matching_shows(name)
		print show_list
		if len(show_list) > 0:
			print show_list
			show_id = show_list[0][0]
			images = tv.get_show_image_choices(show_id)
			for im in images:
				if im[1] == 'fanart':
					return im[0]
					break
		#print ('Found TV Show List: %s' % show_list, 0)
	except Exception as e:
		return None
		print e

	return None



def parse_iframe_for_direct_video(src):
	page = urllib2.urlopen(src)
	soup = BeautifulSoup(page.read())
	link = soup.find("source",{"data-res":"720p"})
	#print link['src']

	if link is not None:
		return link['src']

def parse_page_for_link(link):
	page = urllib2.urlopen(link)
	soup = BeautifulSoup(page.read())
	thumb = soup.find("div", {"class": "video-wrapper"}).find("span",{"itemprop":"thumbnailUrl"})
	frame = soup.find("iframe", {"id": "videoFrame"})
	#print frame['data-src']

	aDict = {}
	if thumb.contents[0] is not None:
		aDict['thumb'] = thumb.contents[0]
	if frame is not None:
		aDict['video_url'] = parse_iframe_for_direct_video(frame['data-src'])

	return aDict

def remove_non_ascii_2(text):
	return re.sub(r'[^\x00-\x7F]+',' ', text)

def get_anime_from_page(pages):

	for page in pages:
		print "Loading... "+ page
		try:
			headers = {'Referer' : 'http://animebaka.tv','Host':'animebaka.tv'}
			req = urllib2.Request(page, None, headers)
			page = urllib2.urlopen(req)
		except urllib2.HTTPError as e:
			print e.code
			print e.read()

		soup = BeautifulSoup(page.read())
		episodes = soup.findAll("div", {"itemtype": "http://schema.org/Episode"})
		#next_page = soul.find("ul",{"class":"pager"}).find("li",{"rel":"next"})["href"]
	
		for episode in episodes:
			title = remove_non_ascii_2(episode.find("div",{"itemprop":"partOfSeries"}).contents[0])

			if any(x.title == title for x in list(series_list)) == True:
				break

			thumb = episode.find("img",{"itemprop":"thumbnailUrl"})['src']
			link = episode.find("a",{"class":"cap-wrapper poster"})['href']
			clear = episode.find("div",{"class":"episode-text clearfix"}).contents
			ep_number = clear[1].contents[0]

			published = ''
			if len(clear) == 5:
				published = clear[3].contents[0]
			else:
				published = clear[1].contents[0]
	
			ser = Series(title=title,sub="EP "+""+ep_number+" - "+published,thumb='http:'+thumb,link="http://animebaka.tv"+link)
			#parse_page_for_link(ser)
			series_list.append(ser)

def get_episode_list(link,title):
	headers = {'Referer' : 'http://animebaka.tv','Host':'animebaka.tv'}
	page = urllib2.urlopen(link)
	soup = BeautifulSoup(page.read())
	episodes = soup.findAll("tr", {"itemtype": "http://schema.org/Episode"})
	num_episodes = len(episodes)

	if num_episodes == 1:
		video_path = episodes[0].find("a",{"itemprop":"url"})['href']
		parsed = parse_page_for_link('http://animebaka.tv'+video_path)
		xbmc.executebuiltin("PlayMedia(%s)" % (parsed['video_url']))
	else:
		xbmcplugin.setContent(addon_handle,'episodes')
		for idx, episode in reversed(list(enumerate(episodes))):
			link = episode.find("a",{"itemprop":"url"})['href']
			label = episode.find("span",{"itemprop":"episodeNumber"}).contents[0]
			url = 'plugin://%s/?mode=play&link=%s' % (_plugId,'http://animebaka.tv'+link)
			li = xbmcgui.ListItem(label='%s Episode %s'%(title,label),iconImage=None,thumbnailImage=None,path=url)
			fanart = ADDON.getAddonInfo('path') + '/fanart.jpg'
			li.setProperty('fanart_image',fanart)
			xbmcplugin.addDirectoryItem(handle=addon_handle,url=url,listitem=li)

		xbmcplugin.endOfDirectory(addon_handle)

def main():
	print args
	if mode is None:

		xbmcplugin.setContent(addon_handle,'movies')
		get_anime_from_page(["http://animebaka.tv","http://animebaka.tv/?page=2","http://animebaka.tv/?page=3","http://animebaka.tv/?page=4","http://animebaka.tv/?page=5","http://animebaka.tv/?page=6","http://animebaka.tv/?page=7","http://animebaka.tv/?page=8","http://animebaka.tv/?page=9","http://animebaka.tv/?page=10"])
		
		for series in series_list:
			url = 'plugin://%s/?mode=get_episodes&series=%s&link=%s' % (_plugId,series.title,series.link)
			li = xbmcgui.ListItem(label=series.title+" "+series.sub,iconImage=series.thumb,path=url)
			fanart = get_show_meta(series.title)
			if fanart is not None:
				li.setProperty('fanart_image',fanart)
			else:
				fanart = ADDON.getAddonInfo('path') + '/fanart.jpg'
				li.setProperty('fanart_image',fanart)

			#fanart = ADDON.getAddonInfo('path') + '/fanart.jpg'
			xbmcplugin.addDirectoryItem(handle=addon_handle,url=url,listitem=li,isFolder=True)
		
		
		#if skin_used == 'skin.confluence':
		#	xbmc.executebuiltin('Container.SetViewMode(512)')

		xbmcplugin.endOfDirectory(addon_handle)

	elif mode[0] == 'get_episodes':
		xbmcplugin.setContent(addon_handle,'episodes')
		get_episode_list('http://animebaka.tv/anime/'+args.get('series')[0].lower().replace(" ","_"),args.get('series')[0])
	elif mode[0] == 'play':
		link = args.get('link')[0]
		print 'Play '+link
		parsed = parse_page_for_link(link)
		print parsed
		xbmc.executebuiltin("PlayMedia(%s)" % parsed['video_url'])
