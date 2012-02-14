import re
import time
import datetime
import random
import string
import urllib2
import urllib
import urlparse
import Queue

from urllib import quote_plus

import copy
import cerealizer
from BeautifulSoup import BeautifulSoup

from htmlentitydefs import name2codepoint as n2cp

VIDEO_PREFIX = "/video/lmwt"
NAME = L('Title')

VERSION = "1.2"
VERSION_URLS = {
	"1.2" : "http://bit.ly/wCczFy",
	"1.1" : "http://bit.ly/Acjmo5",
	"1.0" : "http://bit.ly/ypSj0G"
}

# make sure to replace artwork with what you want
# these filenames reference the example files in
# the Contents/Resources/ folder in the bundle
ART	 = 'art-default.jpg'
APP_ICON = 'icon-default.png'

PREFS_ICON = 'icon-prefs.png'
SEARCH_ICON='icon-search.png'
MOVIE_ICON='icon-movie.png'
MOVIE_HD_ICON='icon-movie-hd.png'
TV_ICON='icon-tv.png'
AZ_ICON='icon-az.png'
STANDUP_ICON='icon-standup.png'
GENRE_BASE='icon-genre'
GENRE_ICON=GENRE_BASE + '.png'

LMWT_URL = "http://www.1channel.ch"
LMWT_SEARCH_URL= "http://www.1channel.ch/index.php"

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/534.51.22 (KHTML, like Gecko) Version/5.1.1 Safari/534.51.22'
	
####################################################################################################

def Start():

	## make this plugin show up in the 'Video' section
	## in Plex. The L() function pulls the string out of the strings
	## file in the Contents/Strings/ folder in the bundle
	## see also:
	##  http://dev.plexapp.com/docs/mod_Plugin.html
	##  http://dev.plexapp.com/docs/Bundle.html#the-strings-directory
	Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, APP_ICON, ART)

	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	Plugin.AddViewGroup('PanelStream', viewMode='PanelStream', mediaType='items')
	Plugin.AddViewGroup('MediaPreview', viewMode='MediaPreview', mediaType='items')

	## set some defaults so that you don't have to
	## pass these parameters to these object types
	## every single time
	## see also:
	##  http://dev.plexapp.com/docs/Objects.html
	MediaContainer.title1 = NAME
	MediaContainer.viewGroup = "InfoList"
	MediaContainer.art = R(ART)
	MediaContainer.userAgent = USER_AGENT
	
	DirectoryItem.thumb = R(APP_ICON)
	VideoItem.thumb = R(APP_ICON)
	
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-agent'] = USER_AGENT
	HTTP.Headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
	HTTP.Headers['Accept-Encoding'] = '*gzip, deflate'
	#HTTP.Headers['TE'] = 'trailers'
	HTTP.Headers['Connection'] = 'keep-alive'
	
	Network.Timeout = 40
	
	if (Prefs['versiontracking'] == True):
		request = urllib2.Request(VERSION_URLS[VERSION])
		request.add_header('User-agent', '-')
		try:
			response = urllib2.urlopen(request)
		except:
			pass

####################################################################################################
# see:
#  http://dev.plexapp.com/docs/Functions.html#ValidatePrefs

def ValidatePrefs():

	pass

####################################################################################################
# Main navigtion menu

def VideoMainMenu():
	
	dir = MediaContainer(noCache=True, title1=L("Video Channels"), title2=NAME, viewGroup="InfoList")
	
	dir.Append(
		Function(
			DirectoryItem(
				TypeMenu,
				L('MoviesTitle'),
				subtitle = L('MoviesSubtitle'),
				summary= L('MoviesSummary'),
				thumb = R(MOVIE_ICON),
				art = R(ART)
			),
			type = "movies",
		)
	)

	dir.Append(
		Function(
			DirectoryItem(
				TypeMenu,
				L("TVTitle"),
				subtitle=L("TVSubtitle"),
				summary=L("TVSummary"),
				thumb=R(TV_ICON),
				art=R(ART)
			),
			type="tv",
		)
	)
	
	dir.Append(
		PrefsItem(
			title=L("PrefsTitle"),
			subtile=L("PrefsSubtitle"),
			summary=L("PrefsSummary"),
			thumb=R(PREFS_ICON)
		)
	)

	return dir

####################################################################################################
# Menu users seen when they select TV shows in Main menu

def TypeMenu(sender, type = None, genre = None):

	type_desc = "Movies"
	if (type == "tv"):
		type_desc = "TV Shows"
	
	mcTitle2 = type_desc
	if genre is not None:
		mcTitle2 = mcTitle2 + " (" + genre + ")"

	dir = MediaContainer(noCache=True,title1=sender.title2, title2=mcTitle2, viewGroup="InfoList")
	
	dir.Append(
		Function(
			DirectoryItem(
				ItemsMenu,
				"Popular",
				subtitle="",
				summary="List of most popular " + type_desc,
				thumb=S("Popular.png"),
				art=R(ART)
			),
			type=type,
			genre=genre,
			sort="views",
			section_name="Popular",
		)
	)

	dir.Append(
		Function(
			DirectoryItem(
				ItemsMenu,
				"Highly Rated",
				subtitle="",
				summary="List of highly rated " + type_desc,
				thumb=S("Favorite.png"),
				art=R(ART)
			),
			type=type,
			genre=genre,
			sort="ratings",
			section_name="Highly Rated",
		)
	)
	
	dir.Append(
		Function(
			DirectoryItem(
				ItemsMenu,
				"Recently Added",
				subtitle="",
				summary="List of recently added " + type_desc,
				thumb=S("History.png"),
				art=R(ART)
			),
			type=type,
			genre=genre,
			sort='date',
			section_name="Recently Added",
		)
	)
		
	dir.Append(
		Function(
			DirectoryItem(
				ItemsMenu,
				"Latest Releases",
				subtitle="",
				summary="List of latest releases",
				thumb=S("Recent.png"),
				art=R(ART)
			),
			type=type,
			genre=genre,
			sort='release',
			section_name="Latest Releases",
		)
	)
	
	
	if genre is None:
			
		dir.Append(
			Function(
				DirectoryItem(
					GenreMenu,
					"Genre",
					subtitle= type_desc +" by genre",
					summary="Browse " + type_desc + " by genre.",
					thumb=R(GENRE_ICON),
					art=R(ART),
				),
				type = type,
			)
		)
		
	dir.Append(
		Function(
			DirectoryItem(
				AZListMenu,
				"A-Z List",
				subtitle="Complete list of " + type_desc,
				summary="Watch High Quality " + type_desc,
				thumb=R(AZ_ICON),
				art=R(ART)
			),
			type=type,
			genre = genre,
		)
	)
		
	if genre is None:
		
		dir.Append(
			Function(
				InputDirectoryItem(
					SearchResultsMenu,
					"Search",
					"",
					summary="Search for a title using this feature",
					thumb=R(SEARCH_ICON),
					art=R(ART)
				),
				type=type,
			)
		)
	
	return dir


####################################################################################################

def AZListMenu(sender,type=None, genre=None, sort=None, alpha=None):

	mc = MediaContainer( viewGroup = "InfoList" , title1=sender.title2, title2 = "A-Z")
	azList = ['#1234','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
	
	for value in azList:
		mc.Append(
			Function(
				DirectoryItem(
					ItemsMenu,
					value,
					subtitle="Complete collection arranged alphabetically",
					summary="Browse High Quality collection",
					thumb=R(AZ_ICON),
					art=R(ART)
				),
				type=type,
				genre=genre,
				sort=sort,
				alpha=value,
				section_name=value,
			)
		)
		
	return mc

####################################################################################################

def GenreMenu(sender, type=None):

	dir = MediaContainer(noCache=True,title1=sender.title2, title2="Genre", viewGroup="InfoList",httpCookies=HTTP.CookiesForURL('http://www.megaupload.com/'))
	
	genres = [
		"Action", "Adventure", "Animation", "Biography", "Comedy", "Crime", "Documentary", "Drama",
		"Family", "Fantasy", "History", "Horror", "Japanese", "Korean", "Music", "Musical", "Mystery",
		"Romance", "Sci-Fi", "Short", "Sport", "Thriller", "War", "Western", "Zombies"
	]
	
	for genre in genres:
	
		icon = R(GENRE_BASE + "-" + genre.lower() + ".png")
		if icon is None:
			("Couldn't find icon for genre: " + genre.lower())
			icon = R(GENRE_ICON)
			
		dir.Append(
			Function(
				DirectoryItem(
					TypeMenu,
					genre,
					subtitle="",
					summary="Browse all : " + genre + ".",
					thumb=icon,
					art=R(ART),
				),
				type = type,
				genre = genre,
			)
		)
		
	return dir


####################################################################################################

def ItemsMenu(sender,type=None,genre=None,sort=None,alpha=None,section_name="", start_page=0):

	num_pages = 5
	replace_parent = sender.title2 == section_name
	title1 = sender.title2
	title2 = section_name
	if (replace_parent):
		title1 = sender.title1
	
	mc = MediaContainer(noCache = True, viewGroup = "ListInfo", title1=title1, title2=title2, replaceParent = replace_parent)
	
	items = GetItems(type, genre, sort, alpha, num_pages, start_page)
	
	func_name = TVSeasonMenu
	
	if (type=="movies"):
		func_name = SourcesMenu
		
	if (start_page > 0):
		mc.Append(
			Function(
				DirectoryItem(
					ItemsMenu,
					"<< Previous",
					subtitle="",
					summary= "",
					thumb= "",
					art="",
				),
				type = type,
				genre = genre,
				sort = sort,
				alpha = alpha,
				section_name = section_name,
				start_page = start_page - num_pages
			)
		)
	
	for item in items:
	
		mc.Append(
			Function(
				DirectoryItem(
					func_name,
					item.title,
					subtitle="",
					summary= "",
					thumb= item.thumb,
					art="",
					rating = item.rating
				),
				mediainfo = item,
			)
		)
		
	mc.Append(
		Function(
			DirectoryItem(
				ItemsMenu,
				"More >>",
				subtitle="",
				summary= "",
				thumb= "",
				art="",
			),
			type = type,
			genre = genre,
			sort = sort,
			alpha = alpha,
			section_name = section_name,
			start_page = start_page + num_pages
		)
	)

	return mc
	
####################################################################################################

def TVSeasonMenu(sender, mediainfo = None):

	mc = MediaContainer(viewGroup = "ListInfo", title1=sender.title2, title2= mediainfo.title)
	
	items = GetTVSeasons(mediainfo)
	
	for item in items:
		mc.Append(
			Function(
				DirectoryItem(
					TVSeasonShowsMenu,
					item[0],
					subtitle="",
					summary= "",
					thumb= mediainfo.thumb,
					art="",
					ratings= mediainfo.rating
				),
				mediainfo = mediainfo,
				season_info = item,
			)
		)

	return mc

####################################################################################################

def TVSeasonShowsMenu(sender, mediainfo = None, season_info = None):

	mc = MediaContainer(viewGroup = "ListInfo", title1=sender.title2, title2= season_info[0])
		
	for item in GetTVSeasonShows(season_info[1]):
	
		mc.Append(
			Function(
				DirectoryItem(
					SourcesMenu,
					item[0],
					subtitle= mediainfo.title,
					summary= "",
					thumb= mediainfo.thumb,
					art="",
					ratings= mediainfo.rating
				),
				mediainfo = mediainfo,
				url = item[1],
				item_name = item[0]
			)
		)
			
	return mc

####################################################################################################

def SourcesMenu(sender, mediainfo = None, url = None, item_name = None):
	
	if (url is None):
		url = mediainfo.id
		
	if (item_name is None):
		item_name = mediainfo.title
	
	mc = ObjectContainer(view_group = "InfoList", title1=sender.title2, title2= item_name)
	
	for item in GetSources(url):
	
		if (item['quality'] == "sponsored"):
			continue
				
		# Log(item)
		mc.add(GetItemForSource(mediainfo = mediainfo, item = item))
		
	return mc
	
####################################################################################################

def SearchResultsMenu(sender, query, type):

	mc = MediaContainer(noCache=True, viewGroup = "ListInfo", title1=sender.title2, title2="Search")

	func_name = TVSeasonMenu
	if (type=="movies"):
		func_name = SourcesMenu
		
	for item in GetSearchResults(query=query, type=type):
		mc.Append(
			Function(
				DirectoryItem(
					func_name,
					item.title,
					subtitle= "",
					summary= "",
					thumb= item.thumb,
					art="",
					ratings= item.rating
				),
				mediainfo = item,
			)
		)
		
	if(len(mc) >0) :
		return mc
	else:
		return MessageContainer(
			"Zero Matches",
			"No results found for your query \"" + query + "\""
		)

####################################################################################################
# PAGE PARSING
####################################################################################################

def GetSources(url):

	soup = BeautifulSoup(HTTP.Request(LMWT_URL + url).content)
	sources = []
	
	for item in soup.find('div', { 'id': 'first' }).findAll('table', { 'class' : re.compile('movie_version.*') }):

		source = {}
		
		# Extract out source URL
		source['url'] = str(item.find('span', { 'class' : 'movie_version_link' }).a['href'])
		
		# Extract out source name.
		source['name'] = str(item.find('span', { 'class' : 'movie_version_link' }).a.string)
		if (source['name'].lower().find('trailer') >= 0):
			continue
		
		#ÊExtract out source quality.
		quality_elem = item.find('span', { 'class': re.compile('quality_.*') })
		quality = re.search("quality_(.*)", quality_elem['class']).group(1)
		source['quality'] = quality
		
		# Extract out source provider name.
		provider_name = None
		prov_name_tag = item.find('span', { 'class': 'version_host' })

		if (prov_name_tag.script is not None):
			provider_name = re.search("writeln\('(.*)'\)", str(prov_name_tag.script)).group(1)
			
		if (provider_name is None and prov_name_tag.string is not None):
			provider_name = prov_name_tag.string
			
		if (provider_name is None and prov_name_tag.img is not None):
			if (prov_name_tag.img['src'].find('host_45') >= 0):
				provider_name = "sockshare.com"
			elif (prov_name_tag.img['src'].find('host_48') >= 0):
				provider_name = "putlocker.com"
			
		source['provider_name'] = provider_name
		
		# Extract out source rating.
		rating_style = item.find('div', { 'class': 'movie_ratings' }).find('li', { 'class': 'current-rating' })['style']
		rating = re.search('([\d\.]*)px', rating_style).group(1)
		if (rating is not None and rating <> ""):
			source['rating'] = int(float(rating))
		
		# Extract out source rating vote numbers.
		rating_count = item.find('div', { 'class' : re.compile('voted') }).string
		source['rating_count'] = re.search("\D*(\d*)", rating_count).group(1)
		
		# Extract out source view count.
		views = item.find('span', { 'class': 'version_veiws' }).string
		source['views'] = re.search("\D*(\d*)", views).group(1)
		
		# Log(source)
		sources.append(source)
	
	return sources


####################################################################################################

def GetTVSeasonShows(url):

	soup = BeautifulSoup(HTTP.Request(LMWT_URL + url).content)
	shows = []
	
	for item in soup.findAll('div', { 'class': 'tv_episode_item' }):
	
		show = []
		
		title = str(item.a.contents[0]).strip()
		
		if (item.a.span is not None):
			title = title + " " + str(item.a.span.string).strip()
		
		show.append(title)
		show.append(item.a['href'])
		
		shows.append(show)
		
	return shows


####################################################################################################

def GetTVSeasons(mediainfo):
	
	items = []
	
	soup = BeautifulSoup(HTTP.Request(LMWT_URL + mediainfo.id).content)
	
	for item in soup.find("div", { 'id': 'first' }).findAll('h2'):
	
		items.append([str(item.a.string), item.a['href']])
		
	return items


####################################################################################################

def GetItems(type, genre = None, sort = None, alpha = None, pages = 5, start_page = 0):

	page_num = 0
	items = []
	
	while (page_num < pages):
	
		page_num = page_num + 1
		url = GetURL(type = type, genre = genre, sort = sort, alpha = alpha, page_num = page_num + start_page)
		soup = BeautifulSoup(HTTP.Request(url).content)
		
		for item in soup.findAll("div", { 'class': 'index_item index_item_ie' }):
		
			#Log('Found item: ' + str(item))
			res = MediaInfo()
			
			# Extract out title
			title_alt = item.find('a')['title']
			res.title = re.search("Watch (.*)", title_alt).group(1)
			
			# Extract out URL
			res.id = item.a['href']
			
			# Extract out thumb
			res.thumb = item.find('img')['src']
			
			# Extract out rating
			rating_style = item.find('li')['style']
			rating = re.search("width:\s([\d\.]*)px;", rating_style).group(1);
			
			if (rating is not None and rating <> ""):
				res.rating = int(int(rating) / 10)
			
			# Add to item list.
			#Log("Adding item: " + str(res))
			items.append(res)
			
	return items


####################################################################################################

def GetURL(type, genre = None, sort = None, page_num = None, alpha = None):

	url = LMWT_URL + "/?" + type + "="
	
	if (sort is not None):
		url = url + "&sort=" + sort
		
	if (genre is not None):
		url = url + "&genre=" + genre
		
	if (page_num is not None):
		url = url + "&page=" + str(page_num)
		
	if (alpha is not None):
		url = url + "&letter=" + alpha
		
		# if no specific sort order has been give, but we've been given
		# a letter, sort alphabetically.
		if (sort is None):
			url = url + "&sort=alphabet"
		
	return url
	
	
####################################################################################################

def GetSearchResults(query=None,type=None,):
	
	items = []
	
	soup = BeautifulSoup(HTTP.Request(LMWT_SEARCH_URL + "?search",cacheTime=0).content)
	key = soup.find('input', { 'type': 'hidden', 'name': 'key' })['value']
	
	section = "1"
	if (type == "tv"):
		section = "2"
	
	url = LMWT_SEARCH_URL + "?search_section=" + section + "&search_keywords=" + urllib.quote_plus(query) + "&key=" + key
	soup = BeautifulSoup(HTTP.Request(url,cacheTime=0).content)
	#Log(soup)
	
	for item in soup.findAll("div", { 'class': 'index_item index_item_ie' }):
	
		# Log('Found item: ' + str(item))
		res = MediaInfo()
		
		# Extract out title
		title_alt = item.find('a')['title']
		res.title = re.search("Watch (.*)", title_alt).group(1)
		
		# Extract out URL
		res.id = item.a['href']
		
		# Extract out thumb
		res.thumb = item.find('img')['src']
		
		# Extract out rating
		rating_style = item.find('li')['style']
		res.rating = re.search("width:\s(\d)*px;", rating_style).group(1);
		
		# Add to item list.
		#Log("Adding item: " + str(res))
		items.append(res)
	
	# Log(items)
	return items

	
####################################################################################################
# PROVIDER SPECIFIC CODE
####################################################################################################

def GetItemForSource(mediainfo, item):

	summary = (
		"Provider: " + item['provider_name'] + "\n" + 
		"Quality: " + item['quality'] + "\n" + 
		"Views: " + str(item['views']) + "\n" +
		"Provider Rating: " + str(item['rating']) + "/100"
	)
	
	if (
		item['provider_name'] == 'putlocker.com' or	
		item['provider_name'] == 'sockshare.com'	
	):
	
		return VideoClipObject(
			key = Callback(PlayVideoPutLocker, mediainfo = mediainfo, url = item['url']),
			title = item['name'],
			rating_key = 'LMWT/' + mediainfo.id,
			summary = summary,
			thumb= mediainfo.thumb,
			rating = float(mediainfo.rating),
		)
			
	elif (
		item['provider_name'] == 'movpod.net' or
		item['provider_name'] == 'movpod.in' or
		item['provider_name'] == 'daclips.com' or
		item['provider_name'] == 'daclips.in'
	):
	
		return VideoClipObject(
			key = Callback(PlayVideoMovPod, mediainfo = mediainfo, url = item['url']),
			rating_key = 'LMWT/' + mediainfo.id,
			title = item['name'],
			summary = summary,
			thumb = mediainfo.thumb,
			rating = float(mediainfo.rating),
		)
		
	elif (item['provider_name'] == 'zalaa.com'):
	
		return MovieObject(
			key = Callback(PlayVideoZalaa, mediainfo = mediainfo, url = item['url']),
			rating_key = 'LMWT/' + mediainfo.id,
			title = item['name'],
			summary = summary,
			thumb = mediainfo.thumb,
			rating = float(mediainfo.rating),
		)
		
	elif (item['provider_name'] == 'youtube.com'):
	
		# Get final URL now so we can simply re-use the existing YouTube service.
		# Note that even though this means "pre-loading" a source with all the
		# associated requests to the LMWT servers, this is not as bad as it seems,
		# as when YouTube is a source, it's usually the only source.
		#Log('Requesting ' + item['url'])
		request = urllib2.Request(LMWT_URL + item['url'])
		request.add_header('User-agent', HTTP.Headers['User-agent'])
		response = urllib2.urlopen(request)
	
		# Collect final url.
		final_url = response.geturl()
		#Log(final_url)
	
		return VideoClipObject(
			title = item['name'],
			summary = summary,
			thumb= mediainfo.thumb,
			rating = float(mediainfo.rating),
			url = final_url
		)
			
	elif (
		# Temporarily disable FileBox as they don't seem to be able to return files
		# within a reasonable time delay which causes Plex to time out.
		#item['provider_name'] == 'filebox.com' or
		item['provider_name'] == 'ufliq.com'
	):
	
		return VideoClipObject(
			key = Callback(PlayVideoFileBox, mediainfo = mediainfo, url = item['url']),
			rating_key = 'LMWT/' + mediainfo.id,
			title = item['name'],
			summary = summary,
			thumb= mediainfo.thumb,
			rating = float(mediainfo.rating),
		)
						
	else:
	
		return DirectoryObject(
			key = Callback(PlayVideoNotSupported, mediainfo = mediainfo, url = item['url']),
			title = item['name'] + " (Not currently playable)",
			summary= summary,
			thumb= mediainfo.thumb,
		)
		
						
####################################################################################################

def PlayVideoNotSupported(mediainfo, url):

	return ObjectContainer(
		header='Provider not currently supported...',
		message=''
	)

####################################################################################################

def PlayVideoZalaa(mediainfo, url):

	# Read in Loc.
	soup = BeautifulSoup(HTTP.Request(LMWT_URL + url, cacheTime=0).content)
	provider_url = soup.noframes.string
	#Log(provider_url)
	
	# Request provider page.
	#Log('Requesting ' + provider_url)
	request = urllib2.Request(provider_url)
	request.add_header('User-agent', HTTP.Headers['User-agent'])
	response = urllib2.urlopen(request)
	
	# Collect final url (in case of 302 or the like) and read in page.
	provider_url = response.geturl()
	#Log(provider_url)
	
	# Collect filename. Will need that for later.
	file_name = urlparse.urlparse(provider_url).path.split("/")[1]
	#Log(file_name)
	
	soup = BeautifulSoup(response.read())
	
	# Extract out these form elements from the provider page...
	formElems = ['op', 'id', 'fname', 'method_free', 'referer', 'usr_login', 'ipcount_val']
	params = {}
	
	for formElem in formElems:
		formElemVal =  soup.find('input', {'name' : formElem })['value']
		params[formElem] = formElemVal
			
	#Log(params)
	
	# Submit the form. This wil give us a page with the flash player.
	headers = { 'Referer': provider_url }
	content = HTTP.Request(provider_url, cacheTime=0, values=params, headers=headers).content
	soup = BeautifulSoup(content)

	final_url = None
	
	# See how we're going to retrieve the file name....
	if (soup.find('span', { 'id' : 'flvplayerid' })) is None:
		
		script = soup.find('div', { 'id': 'player_code' }).script.string
		#Log(script)
		
		# Look for substitution values.
		elems = re.search("\d{2},'([^']*)'.split", script).group(1).split('|')
		#Log(elems)
		
		# Look for url to substitute values into.
		url = re.search("([0-9a-z]*://[0-9a-z]*\.[0-9a-z]*\.[0-9a-z]*\:[0-9a-z]*/[0-9a-z]*/[0-9a-z]*/[0-9a-z.\-_ ()]*)", script)
		#Log(url.group(1))
		
		# Create dict to map url sub keys to sub values.
		alphadict = dict()
		for cnt in range(0, len(string.digits + string.ascii_lowercase)):
			alphadict[(string.digits + string.ascii_lowercase)[cnt]] = cnt
		for cnt in range(10,30):
			alphadict[str(cnt)] = len(alphadict)
	
		def SubElem(matchObj):
			val = elems[alphadict[matchObj.group(0)]]
			if (val == ""):
				val = matchObj.group(0)
			return val

		# Sub values into url.
		final_url = re.sub("[0-9a-z]{1,2}", SubElem, url.group(1)) 
		
	else:
		# Get file URL.
		#Log("Using FLV Player")
		file = re.search("s1.addVariable\('file','([^']*)'\);", content)	
		final_url = file.group(1)
	
	# And done...
	Log(final_url)
	return Redirect(final_url)

####################################################################################################

def PlayVideoMovPod(mediainfo, url):

	# Read in MovPod Loc.
	soup = BeautifulSoup(HTTP.Request(LMWT_URL + url, cacheTime=0).content)
	movpod_url = soup.noframes.string
	#Log(movpod_url)
	
	# Request movpod page.
	#Log('Requesting ' + movpod_url)
	request = urllib2.Request(movpod_url)
	request.add_header('User-agent', HTTP.Headers['User-agent'])
	response = urllib2.urlopen(request)
	
	# Collect final url and read in MovPod page.
	movpod_url = response.geturl()
	#Log(movpod_url)
	soup = BeautifulSoup(response.read())
	
	# Extract out these form elements...
	formElems = ['op', 'id', 'fname', 'method_free', 'referer', 'usr_login']
	params = {}
	
	for formElem in formElems:
		formElemVal =  soup.find('input', {'name' : formElem })['value']
		params[formElem] = formElemVal
			
	#Log(params)
	
	headers = { 'Referer': movpod_url }
	content = HTTP.Request(movpod_url,values=params,headers=headers).content
	#Log(content)
	
	file = re.search('file:\"(.*?)\"', content)
	final_url = file.group(1)

	Log(final_url)
	return Redirect(final_url)

####################################################################################################

def PlayVideoPutLocker(mediainfo, url):

	# Read in hash from form.
	#Log('Requesting ' + LMWT_URL + url)
	request = urllib2.Request(LMWT_URL + url)
	request.add_header('User-agent', HTTP.Headers['User-agent'])
	response = urllib2.urlopen(request)
	
	putlocker_url = response.geturl()
	# Log(putlocker_url)
	
	soup = BeautifulSoup(response.read())
	params = {}
	hash =  soup.find('input', {'name' : 'hash' })['value']
	# Log(hash)
	params['hash'] = hash
	params['confirm'] = "Continue as Free User"
	
	# Log(params)
	
	content = HTTP.Request(putlocker_url,params).content
	playlist = re.search("playlist: \'(.*?)\'", content).group(1)
	# Log(playlist)
	
	putlocker_host = urlparse.urlparse(putlocker_url).netloc
	
	final = HTTP.Request("http://" + putlocker_host + playlist).content
	# Log(final)
	
	final_url = re.search("<media:content url=\"(.*?)\"", final).group(1)
	
	Log(final_url)
	return Redirect(final_url + "?start=0")

################################################################################################

def PlayVideoFileBox(mediainfo, url):

	# Read in file Loc.
	soup = BeautifulSoup(HTTP.Request(LMWT_URL + url, cacheTime=0).content)
	provider_url = soup.noframes.string
	#Log(provider_url)
	
	#Log('Requesting ' + provider_url)
	request = urllib2.Request(provider_url)
	request.add_header('User-agent', HTTP.Headers['User-agent'])
	response = urllib2.urlopen(request)
	
	# Collect final url and read in page.
	provider_url = response.geturl()
	#Log(provider_url)
	soup = BeautifulSoup(response.read())
	
	# Extract out these form elements...
	formElems = ['op', 'id', 'rand', 'method_free', 'method_premium', 'referer', 'down_direct']
	params = {}
	
	for formElem in formElems:
		formElemVal =  soup.find('input', {'name' : formElem })['value']
		params[formElem] = formElemVal
			
	#Log(params)
	
	time.sleep(5)
	headers = { 'Referer': provider_url }
	soup = BeautifulSoup(HTTP.Request(provider_url,values=params,headers=headers).content)
	#Log(soup)
	
	
	final_url = soup.find('div', { 'class' : 'getpremium_heading4' }).a['href']

	Log(final_url)
	return Redirect(final_url)
	
	
####################################################################################################

class MediaInfo(object):

	def __init__(self, id = None, title = None, year = None, background = None, poster = None, summary = None, rating = None, dt = None):
	
		self.id = id
		self.title = title
		self.year = year
		self.background = background
		self.poster = poster
		self.summary = summary
		self.rating = rating
		self.dt = dt

		
	def __str__(self):
	
		return (
			"{ " +
			"id: " + str(self.id) + ", " +
			"title: " + str(self.title) + ", " +
			"year: " + str(self.year) + ", " +
			"background:" + str(self.background) + ", " +
			"poster: " + str(self.poster) + ", " +
			"summary: " + str(self.summary) + ", " +
			"rating:" + str(self.rating) + ", " +
			"}"
		)

cerealizer.register(MediaInfo)
