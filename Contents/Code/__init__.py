import re
import cerealizer
import urllib
import urllib2
import copy

from BeautifulSoup import BeautifulSoup
from Utils import MediaInfo

cerealizer.register(MediaInfo)

VIDEO_PREFIX = "/video/lmwt"
NAME = L('Title')

VERSION = "12.05.28.1"
VERSION_URLS = {
	"12.05.28.1": "http://bit.ly/JJvDZO",
	"12.05.01.1": "http://bit.ly/IpYhy9",
	"12.04.18.1": "http://bit.ly/JajQNI",
	"12.02.28.1": "http://bit.ly/yzepjl",
	"12.02.18.1": "http://bit.ly/y3LvHD",
	"1.2" : "http://bit.ly/wCczFy",
	"1.1" : "http://bit.ly/Acjmo5",
	"1.0" : "http://bit.ly/ypSj0G"
}

LATEST_VERSION_URL = 'http://bit.ly/xoGzzQ'
LATEST_VERSION = 'LATEST_VERSION'
LATEST_VERSION_SUMMARY = 'LATEST_VERSION_SUMMARY'

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
	HTTP.Headers['Connection'] = 'keep-alive'
	
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
	
	# Get latest version number of plugin.
	soup = BeautifulSoup(HTTP.Request(LATEST_VERSION_URL, cacheTime=3600).content)
	Dict[LATEST_VERSION] = soup.find('div',{'class':'markdown-body'}).p.string
	
	if (Dict[LATEST_VERSION] != VERSION):
	
		summary = soup.find('div',{'class':'markdown-body'}).pre.code.string
		summary += "\nClick to be taken to the Unsupported App Store"
		Dict[LATEST_VERSION_SUMMARY] = summary
		
		dir.autoRefresh = 15
		
		dir.Append(
			Function(
				DirectoryItem(
					UpdateMenu,
					title='Update Available',
					subtitle="Version " + Dict[LATEST_VERSION] + " is now available. You have " + VERSION,
					summary=Dict[LATEST_VERSION_SUMMARY],
					thumb=None,
					art=R(ART)
				),
			),
		)
	
	return dir

####################################################################################################
# Menu users seen when they select Update in main menu.

def UpdateMenu(sender):

	# Force an update to the UAS' version info.
	HTTP.Request(
		"http://" + Request.Headers['Host'] + "/applications/unsupportedappstore/:/function/ApplicationsMainMenu",
		cacheTime=0,
		immediate=True
	)
	
	# Go to the UAS.
	return Redirect('/applications/unsupportedappstore/:/function/InstalledMenu?function_args=Y2VyZWFsMQozCmRpY3QKZGljdApGcmFtZXdvcmsub2JqZWN0cy5JdGVtSW5mb1JlY29yZAoxCnIyCnM2CnNlbmRlcjUKczkKSW5zdGFsbGVkczkKaXRlbVRpdGxlczIwClVuU3VwcG9ydGVkIEFwcFN0b3JlczYKdGl0bGUxczQKTm9uZXM2CnRpdGxlMnM3NAovYXBwbGljYXRpb25zL3Vuc3VwcG9ydGVkYXBwc3RvcmUvOi9yZXNvdXJjZXMvYXJ0LWRlZmF1bHQuanBnP3Q9MTMyOTQzNDEyOHMzCmFydHM3NQovYXBwbGljYXRpb25zL3Vuc3VwcG9ydGVkYXBwc3RvcmUvOi9yZXNvdXJjZXMvaWNvbi1kZWZhdWx0LnBuZz90PTEzMjk0MzQxMjhzNQp0aHVtYnIxCnIwCg__')
	
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
	azList = ['123','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
	
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

	# The description meta header for some shows inserts random double quotes in the
	# content which breaks the parsing of the page. Work around that by simply
	# removing the head section in which the meta elements are contained.
	headMassage = [(re.compile('<head>(.*)</head>', re.S), lambda match: '')]
	soupMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
	soupMassage.extend(headMassage)	
	
	soup = BeautifulSoup(HTTP.Request(LMWT_URL + url).content, markupMassage=soupMassage)
	
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

	# The description meta header for some shows inserts random double quotes in the
	# content which breaks the parsing of the page. Work around that by simply
	# removing the head section in which the meta elements are contained.
	headMassage = [(re.compile('<head>(.*)</head>', re.S), lambda match: '')]
	soupMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
	soupMassage.extend(headMassage)	
	
	soup = BeautifulSoup(HTTP.Request(LMWT_URL + mediainfo.id).content, markupMassage=soupMassage)

	items = []

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
	
	providers_with_service = [
		'putlocker.com', 'sockshare.com',
		'movpod.net', 'movpod.in', 'daclips.com', 'daclips.in', 'gorillavid.com', 'gorillavid.in',
		'youtube.com',
		'zalaa.com',
		'vidbux.com','vidxden.com'
	]
	
	if (item['provider_name'] in providers_with_service):
	
		return VideoClipObject(
			url = LMWT_URL + item['url'],
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
