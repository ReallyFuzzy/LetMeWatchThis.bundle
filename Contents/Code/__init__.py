import re
import cerealizer
import urllib
import urllib2
import copy
import sys
import base64

from datetime import date, datetime
from htmlentitydefs import name2codepoint as n2cp
from urlparse import urlparse

from BeautifulSoup import BeautifulSoup
from MetaProviders import DBProvider, MediaInfo
from RecentItems import BrowsedItems, ViewedItems

cerealizer.register(MediaInfo)
cerealizer.register(BrowsedItems)
cerealizer.register(ViewedItems)

VIDEO_PREFIX = "/video/lmwt"
NAME = L('Title')

VERSION = "12.10.22.1"
VERSION_URLS = {
	"12.10.22.1": "http://bit.ly/R7ZieU",
	"12.10.16.2": "http://bit.ly/R7ZieU",
	"12.10.16.1": "http://bit.ly/R7ZieU",
	"12.08.01.1": "http://bit.ly/NUNueE",
	"12.07.25.1": "http://bit.ly/OZBBRR",
	"12.07.19.1": "http://bit.ly/MxCuqr",
	"12.05.28.1": "http://bit.ly/JJvDZO",
	"12.05.01.1": "http://bit.ly/IpYhy9",
	"12.04.18.1": "http://bit.ly/JajQNI",
	"12.02.28.1": "http://bit.ly/yzepjl",
	"12.02.18.1": "http://bit.ly/y3LvHD",
	"1.2" : "http://bit.ly/wCczFy",
	"1.1" : "http://bit.ly/Acjmo5",
	"1.0" : "http://bit.ly/ypSj0G"
}

LATEST_VERSION_URL = 'https://bit.ly/xoGzzQ'

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
FEATURED_ICON='icon-featured.png'
STANDUP_ICON='icon-standup.png'
GENRE_BASE='icon-genre'
GENRE_ICON=GENRE_BASE + '.png'

LMWT_URL = "http://www.1channel.ch/"
LMWT_SEARCH_URL= "http://www.1channel.ch/index.php"

VIEW_HIST_KEY = "USER_VIEWING_HISTORY"
BROWSED_ITEMS_KEY = "RECENT_BROWSED_ITEMS"

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
	
	ObjectContainer.art=R(ART)

	DirectoryItem.thumb = R(APP_ICON)
	VideoItem.thumb = R(APP_ICON)
	
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-agent'] = USER_AGENT
	HTTP.Headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
	HTTP.Headers['Accept-Encoding'] = '*gzip, deflate'
	HTTP.Headers['Connection'] = 'keep-alive'
	
	if (Prefs['versiontracking'] == True):
		try:
			request = urllib2.Request(VERSION_URLS[VERSION])
			request.add_header('User-agent', '-')	
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
	
	oc = ObjectContainer(no_cache=True, title1=L("Video Channels"), title2=NAME, view_group="InfoList")
	
	oc.add(
		DirectoryObject(
			key=Callback(TypeMenu, type="movies", parent_name=oc.title2),
			title=L('MoviesTitle'),
			tagline=L('MoviesSubtitle'),
			summary= L('MoviesSummary'),
			thumb = R(MOVIE_ICON),
			art = R(ART)	
		)
	)

	oc.add(
		DirectoryObject(
			key=Callback(TypeMenu, type="tv", parent_name=oc.title2),
			title=L("TVTitle"),
			tagline=L("TVSubtitle"),
			summary=L("TVSummary"),
			thumb=R(TV_ICON),
			art=R(ART)
		)
	)
	
	if (Prefs['watched_amount'] != 'Disabled'):
		oc.add(
			DirectoryObject(
				key=Callback(HistoryMenu,parent_name=oc.title2,),
				title=L("HistoryTitle"),
				tagline=L("HistorySubtitle"),
				summary=L("HistorySummary"),
				thumb=R("History.png"),
			)
		)
	
	
	oc.add(
		PrefsObject(
			title=L("PrefsTitle"),
			tagline=L("PrefsSubtitle"),
			summary=L("PrefsSummary"),
			thumb=R(PREFS_ICON)
		)
	)
	
	# Get latest version number of plugin.
	try:
	
		soup = BeautifulSoup(HTTP.Request(LATEST_VERSION_URL, cacheTime=3600).content)
		latest_version = soup.find('div',{'class':'markdown-body'}).p.string
		
		if (latest_version != VERSION):
		
			summary = soup.find('div',{'class':'markdown-body'}).pre.code.string
			summary += "\nClick to be taken to the Unsupported App Store"
			latest_version_summary = summary
			
			oc.add(
				DirectoryObject(
					key=Callback(UpdateMenu),
					title='Update Available',
					tagline="Version " + latest_version + " is now available. You have " + VERSION,
					summary=latest_version_summary,
					thumb=None,
					art=R(ART)
				)
			)
			
	except Exception, ex:
		Log("******** Error retrieving and processing latest version information. Exception is:\n" + str(ex))
		
	return oc

####################################################################################################
# Menu users seen when they select Update in main menu.

def UpdateMenu():

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

def TypeMenu(type=None, genre=None, path=[], parent_name=None):

	type_desc = "Movies"
	if (type == "tv"):
		type_desc = "TV Shows"
	
	mcTitle2 = type_desc
	if genre is not None:
		mcTitle2 = mcTitle2 + " (" + genre + ")"

	path = path + [{'elem': mcTitle2, 'type': type, 'genre': genre}]

	oc = ObjectContainer(no_cache=True, title1=parent_name, title2=mcTitle2, view_group="InfoList")
	
	oc.add(
		DirectoryObject(
			key=Callback(
				ItemsMenu,type=type,
				genre=genre,
				sort="views",
				section_name="Popular",
				path=path,
				parent_name=oc.title2,
			),
			title="Popular",
			tagline="",
			summary="List of most popular " + type_desc,
			thumb=R("Popular.png"),
			art=R(ART)	
		)
	)

	oc.add(
		DirectoryObject(
			key=Callback(
				ItemsMenu,
				type=type,
				genre=genre,
				sort="featured",
				section_name="Featured",
				path=path,
				parent_name=oc.title2,
			),
			title="Featured",
			tagline="",
			summary="List of featured " + type_desc,
			thumb=R(FEATURED_ICON),
			art=R(ART)	
		)
	)

	oc.add(
		DirectoryObject(
			key=Callback(
				ItemsMenu,
				type=type,
				genre=genre,
				sort="ratings",
				section_name="Highly Rated",
				path=path,
				parent_name=oc.title2,
			),
			title="Highly Rated",
			tagline="",
			summary="List of highly rated " + type_desc,
			thumb=R("Favorite.png"),
			art=R(ART)
		)
	)
	
	oc.add(
		DirectoryObject(
			key=Callback(
				ItemsMenu,
				type=type,
				genre=genre,
				sort='date',
				section_name="Recently Added",
				path=path,
				parent_name=oc.title2,
			),
			title="Recently Added",
			tagline="",
			summary="List of recently added " + type_desc,
			thumb=R("History.png"),
			art=R(ART)
		)
	)
		
	oc.add(
		DirectoryObject(
			key=Callback(
				ItemsMenu,
				type=type,
				genre=genre,
				sort='release',
				section_name="Latest Releases",
				path=path,
				parent_name=oc.title2,
			),
			title="Latest Releases",
			tagline="",
			summary="List of latest releases",
			thumb=R("Recent.png"),
			art=R(ART)
		)
	)
	
	if genre is None:
			
		oc.add(
			DirectoryObject(
				key=Callback(
					GenreMenu,
					type=type,
					path=path,
					parent_name=oc.title2,
				),
				title="Genre",
				tagline=type_desc +" by genre",
				summary="Browse " + type_desc + " by genre.",
				thumb=R(GENRE_ICON),
				art=R(ART),
			)
		)
		
	oc.add(
		DirectoryObject(
			key=Callback(
				AZListMenu,
				type=type,
				genre=genre,
				path=path,
				parent_name=oc.title2,
			),
			title="A-Z List",
			tagline="Complete list of " + type_desc,
			summary="Browse " + type_desc + " in alphabetical order",
			thumb=R(AZ_ICON),
			art=R(ART)
		)
	)
		
	if genre is None:
		
		oc.add(
			InputDirectoryObject(
				key=Callback(
					SearchResultsMenu,
					type=type,
					parent_name=oc.title2,
				),
				title="Search",
				tagline="Search for a title using this feature",
				summary="Search for a title using this feature",
				prompt="Please enter a search term",
				thumb=R(SEARCH_ICON),
				art=R(ART)				
			)
		)
	
	return oc


####################################################################################################

def AZListMenu(type=None, genre=None, path=None, parent_name=None):

	oc = ObjectContainer(view_group="InfoList", title1=parent_name, title2="A-Z")
	azList = ['123','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
	
	for value in azList:
		oc.add(
			DirectoryObject(
				key=Callback(
					ItemsMenu,
					type=type,
					genre=genre,
					sort=None,
					alpha=value,
					section_name=value,
					path=path,
					parent_name=oc.title2,
				),
				title=value,
				tagline="Complete collection arranged alphabetically",
				summary="Browse items starting with " + value,
				thumb=R(AZ_ICON),
				art=R(ART),
			)
		)
		
	return oc

####################################################################################################

def GenreMenu(type=None, path=None, parent_name=None):

	oc = ObjectContainer(no_cache=True, title1=parent_name,title2="Genre", view_group="InfoList")
	
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
			
		oc.add(
			DirectoryObject(
				key=Callback(
					TypeMenu,
					type=type,
					genre=genre,
					path=path,
					parent_name=oc.title2,
				),
				title=genre,
				tagline="",
				summary="Browse all : " + genre + ".",
				thumb=icon,
				art=R(ART),
			)
		)
		
	return oc


####################################################################################################

def ItemsMenu(
	type=None, genre=None, sort=None, alpha=None,
	section_name="", start_page=0, path=[], parent_name=None
):

	num_pages = 5
	replace_parent = False
	title2 = section_name
	
	oc = ObjectContainer(no_cache=False, view_group="InfoList", title1=parent_name, title2=title2, replace_parent=replace_parent)
	
	path = path + [{'elem': title2, 'type':type, 'genre':genre, 'sort':sort, 'alpha':alpha, 'section_name':section_name}]
	
	items = GetItems(type, genre, sort, alpha, num_pages, start_page)
	
	func_name = TVSeasonMenu
	
	hist = None
	
	if (type=="movies"):
		func_name = SourcesMenu
		if (need_watched_indicator(type)):
			hist = get_watched_history()
			# Don't cache ourselves in case the user watches a new item.
			# If that happens, we need to rebuild the whole list.
			oc.no_cache = True
		
	if (start_page > 0):
		oc.add(
			DirectoryObject(
				key=Callback(
					ItemsMenu,
					type=type,
					genre=genre,
					sort=sort,
					alpha=alpha,
					section_name=section_name,
					start_page=start_page - num_pages,
					parent_name=oc.title2,
				),
				title="<< Previous",
				tagline="",
				summary= "",
				thumb= "",
				art="",
			)				
		)
	
	for item in items:
	
		#Log(item)
		indicator = ''
		if (hist):
			if (hist.has_been_watched(item.id)):
				indicator = '    '
			else:
				indicator =  u"\u00F8" + "  "
			
		oc.add(
			DirectoryObject(
				key=Callback(
					func_name,
					mediainfo=item,
					url=item.id,
					path=path,
					parent_name=oc.title2,
				),
				title=indicator + item.title,
				tagline="",
				summary="",
				thumb= item.poster,
				art="",
			)
		)
			
	oc.add(
		DirectoryObject(
			key=Callback(
				ItemsMenu,
				type=type,
				genre=genre,
				sort=sort,
				alpha=alpha,
				section_name=section_name,
				start_page=start_page + num_pages,
				parent_name=oc.title2,
			),
			title="More >>",
			tagline="",
			summary= "",
			thumb= "",
			art="",
		)
	)
	
	return oc
	
####################################################################################################

def TVSeasonMenu(mediainfo=None, url=None, item_name=None, path=[], parent_name=None):

	if (item_name is not None):
		mediainfo.show_name = item_name
		
	if (mediainfo.show_name is None and mediainfo.title is not None):
		mediainfo.show_name = mediainfo.title
								
	oc = ObjectContainer(view_group = "InfoList", title1=parent_name, title2=mediainfo.show_name)
	
	path = path + [{'elem':mediainfo.show_name, 'show_url':url}]
	
	#Log(mediainfo)
	
	items = GetTVSeasons("/" + url)
	
	for item in items:
		oc.add(
			DirectoryObject(
				key=Callback(
					TVSeasonShowsMenu,
					mediainfo=mediainfo,
					item_name=item[0],
					season_url=item[1],
					path=path,
					parent_name=oc.title2,
				),
				title=item[0],
				tagline="",
				summary="",
				thumb=mediainfo.poster,
				art="",
			)
		)

	return oc

####################################################################################################

def TVSeasonShowsMenu(mediainfo=None, season_url=None,item_name=None, path=[], parent_name=None):

	path = path + [{'elem':item_name,'season_url':season_url}]
	
	if (item_name is not None):
		mediainfo.season = item_name

	need_indicator = need_watched_indicator('tv')
	
	oc = ObjectContainer(no_cache=need_indicator, view_group="InfoList", title1=parent_name, title2=item_name)
	
	# Get Viewing history if we need an indicator.
	hist = None
	if (need_indicator):
		hist = get_watched_history()
	
	for item in GetTVSeasonShows("/" + season_url):
	
		indicator = ''
		
		if (hist):
			watched = hist.has_been_watched(item[1])
			if (watched):
				indicator = '    '
			else:
				indicator =  u"\u00F8" + "  "
		
		oc.add(
			DirectoryObject(
				key=Callback(
					SourcesMenu,
					mediainfo=mediainfo,
					url=item[1],
					item_name=item[0],
					path=path,
					parent_name=oc.title2,
				),
				title=indicator + item[0],
				tagline=mediainfo.title,
				summary="",
				thumb= mediainfo.poster,
				art="",		
			)
		)
			
	return oc

####################################################################################################

def SourcesMenu(mediainfo=None, url=None, item_name=None, path=[], parent_name=None):
	
	if (item_name is None):
		item_name = mediainfo.title
	
	path = path + [ { 'elem': item_name, 'url': url } ]
	
	oc = ObjectContainer(view_group="InfoList", title1=parent_name, title2=item_name)
	
	# Get as much meta data as possible about this item.
	mediainfo2 = GetMediaInfo(url, mediainfo.type)
	
	# Did we get get any metadata back from meta data providers?
	if (mediainfo2 is None or mediainfo2.id is None):
		# If not, use the information we've collected along the way.
		mediainfo2 = mediainfo
	else:
		# We did, but do we know more than the meta data provider?
		# Copy some values across from what we've been passed from LMWT / have built up
		# as we're navigating if meta provider couldn't find data.
		if mediainfo2.poster is None:
			mediainfo2.poster = mediainfo.poster
		
		if mediainfo2.show_name is None:
			mediainfo2.show_name = mediainfo.show_name
			
		if mediainfo2.season is None:
			mediainfo2.season = mediainfo.season
			
		if mediainfo2.title is None:
			mediainfo2.title = item_name
	
	providerURLs = []
	for item in GetSources(url):
	
		if (item['quality'] == "sponsored"):
			continue
					
		mediaItem = GetItemForSource(mediainfo=mediainfo2, item=item)
		
		if mediaItem is not None:
			oc.add(mediaItem)
			if (hasattr(mediaItem, 'url')):
				providerURLs.append(mediaItem.url)
					
	if len(oc.objects) == 0:
		oc.header = "No Enabled Sources Found"
		oc.message = ""
	else:
		# Add this to the recent items list so we can cross reference that
		# with any playback events.
		if (Data.Exists(BROWSED_ITEMS_KEY)):
			browsedItems =  cerealizer.loads(Data.Load(BROWSED_ITEMS_KEY))
		else:
			browsedItems = BrowsedItems()

		
		browsedItems.add(mediainfo2, providerURLs, path)
		
		Data.Save(BROWSED_ITEMS_KEY, cerealizer.dumps(browsedItems))
		
		#Log("Browsed items: " + str(browsedItems))
		
	return oc
	
####################################################################################################

def SearchResultsMenu(query, type, parent_name=None):

	oc = ObjectContainer(no_cache=True, view_group = "InfoList", title1=parent_name, title2="Search (" + query + ")")

	path = [ { 'elem':'Search (' + query + ')', 'query': query }]
	
	func_name = TVSeasonMenu
	if (type=="movies"):
		func_name = SourcesMenu
		
	for item in GetSearchResults(query=query, type=type):
		oc.add(
			DirectoryObject(
				key=Callback(func_name, mediainfo=item, url=item.id, path=path, parent_name=oc.title2),
				title=item.title,
				tagline="",
				summary="",
				thumb=item.poster,
				art="",
			)
		)
		
	if (len(oc) <= 0):
		oc.header = "Zero Matches"
		oc.message = "No results found for your query \"" + query + "\""

	return oc

		
####################################################################################################

def HistoryMenu(parent_name=None):

	oc = ObjectContainer(no_cache=True, view_group="InfoList", title1=parent_name, title2="Recently Watched")
	
	history = get_watched_history()
	
	# If, no previously viewing history, abort.
	if (history is None):
		return
		
	# Get viewing history...
	items = history.get(Prefs['watched_grouping'], int(Prefs['watched_amount']))
	
	# For each viewed video. 
	for item in items:
		
		mediainfo = item[0]
		navpath = item[1]
		
		title = '' 
		if (mediainfo.type == 'tv'):
			
			# If the item is a TV show, come up with sensible display info
			# that matches the requested grouping.
			summary = None
			if (mediainfo.show_name is not None):
				title = mediainfo.show_name
				
			if (
				(Prefs['watched_grouping'] == 'Season' or Prefs['watched_grouping'] == 'Episode') and
				mediainfo.season is not None
			):
				title = title + ' - ' + mediainfo.season
				
			if (Prefs['watched_grouping'] == 'Episode'):
				title = title + ' - ' + mediainfo.title
				summary = mediainfo.summary
				
		else:
			title = mediainfo.title
			summary = mediainfo.summary
			
		oc.add(
			PopupDirectoryObject(
				key=Callback(HistoryNavPathMenu,mediainfo=mediainfo,navpath=navpath,parent_name=oc.title1),
				title=title,
				summary=summary,
				art=mediainfo.background,
				thumb= mediainfo.poster,
				duration=mediainfo.duration,
				
			)
		)
			
	oc.add(
		DirectoryObject(
			key=Callback(HistoryClearMenu),
			title=L("HistoryClearTitle"),
			summary=L("HistoryClearSummary"),
		)
	)
		
	return oc

####################################################################################################

def HistoryClearMenu():

	Data.Remove(VIEW_HIST_KEY)
	Data.Remove(BROWSED_ITEMS_KEY)
	
	oc = HistoryMenu()
	oc.replace_parent = True
	return oc
	
def HistoryAddToFavouritesMenu(mediainfo=None, parent_name=None):

	oc = ObjectContainer(title1=parent_name, title2="Recently Watched")
	oc.header = "-- FIXME --"
	oc.message = "Implement me!"
	
	return oc
	
####################################################################################################

def HistoryNavPathMenu(mediainfo, navpath, parent_name):

	oc = ObjectContainer(title1=parent_name, title2="Recently Watched")
	
	Log(navpath)
	# Grab a copy of the path we can update as we're iterating through it.
	path = list(navpath)
	
	# The path as stored in the system is top down. However, we're going to
	# display it in reverse order (bottom up), so match that.
	path.reverse()
		
	for item in reversed(navpath):
	
		# When the users select this option, the selected option will automatically
		# be re-added to the path by the called menu function. So, remove it now so
		# we don't get duplicates.
		if (len(path) > 0):
			path.pop(0)
			
	
		# The order in which we're processing the path (bottom up) isn't the 
		# same as how it was navigated (top down). So, reverse it to
		# put in the right order to pass on to the normal navigation functions.
		ordered_path = list(path)
		ordered_path.reverse()
	
		# Depending on the types of args present, we may end up calling different methods.
		#
		
		# If we have a query term, take user to search results.
		if ("query" in item):
			callback = Callback(
				SearchResultsMenu, query=item['query'], type=mediainfo.type, parent_name=oc.title2
			)
		# If we have an item URL, take user to provider list for that URL
		elif ("url" in item):
			if (mediainfo.type == 'tv' and Prefs['watched_grouping'] != 'Episode'):
				continue
			else:
				callback = Callback(
					SourcesMenu, mediainfo=mediainfo, url=item['url'], item_name=None, path=ordered_path, parent_name=oc.title2)
			
		# If we have a show URL, take user to season listing for that show
		elif ("show_url" in item):
			callback = Callback(TVSeasonMenu, mediainfo=mediainfo, url=item['show_url'], item_name=mediainfo.show_name, path=ordered_path, parent_name=oc.title2)
		
		# If we have a season URL, take user to episode listing for that season.
		elif ("season_url" in item):
			if (Prefs['watched_grouping'] == 'Season' or Prefs['watched_grouping'] == 'Episode'):
				Log(path)
				callback = Callback(TVSeasonShowsMenu, mediainfo=mediainfo, season_url=item['season_url'], item_name=mediainfo.season, path=ordered_path, parent_name=oc.title2)
			else:
				continue
		
		# If we have a type but no sort, this is first level menu
		elif ("type" in item and "sort" not in item):
			callback = Callback(TypeMenu, type=item['type'], genre=item['genre'], path=ordered_path, parent_name=oc.title2)

		# Must be item list.
		else:
			callback = Callback(ItemsMenu, type=item['type'], genre=item['genre'], sort=item['sort'], alpha=item['alpha'], section_name=item['section_name'], start_page=0, path=ordered_path, parent_name=oc.title2)
		
		oc.add(
			DirectoryObject(
				key=callback,
				title=item['elem']
			)
		)
		
		
	oc.add(
		DirectoryObject(
			key=Callback(HistoryAddToFavouritesMenu),
			title="Add to Favourites"
		)
	)
	
	return oc
	
####################################################################################################
# PAGE PARSING
####################################################################################################

def GetMediaInfo(url, type):

	# The description meta header for some shows inserts random double quotes in the
	# content which breaks the parsing of the page. Work around that by simply
	# removing the head section in which the meta elements are contained.
	headMassage = [(re.compile('<head>(.*)</head>', re.S), lambda match: '')]
	soupMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
	soupMassage.extend(headMassage)
	
	soup = BeautifulSoup(HTTP.Request(LMWT_URL + url).content, markupMassage=soupMassage)

	try:
		imdb_link = soup.find('div','mlink_imdb').a['href']
		imdb_id = re.search("(tt\d+)", str(imdb_link)).group()
		
		mediainfo = DBProvider().GetProvider(type).RetrieveItemFromProvider(imdb_id)
		
		# Also parse the LMWT page and extract out any info not set by the meta provider.
		info_div = soup.find('div', 'movie_info')
		
		# First, extract out description...
		info = {}
		info['Description:'] = info_div.find('td', { 'colspan': '2' }).text
		
		# Then, ratings....
		info['Rating:'] = info_div.find('li', 'current-rating').text
		
		# Extract out any other info.
		for row in info_div.findAll('tr'):
			row_items = row.findAll('td')
			if len(row_items) <> 2 or "colspan" in str(row_items[0]):
				continue
			info[row_items[0].text] = row_items[1].text
		
		# Map available extracted info back to the media info object.
		# First, define the mapping between LMWT items and media info and an additional function
		# to extract out sane info out of the LMWT data.
		item_map = {
			'Description:' : ['summary', lambda x: decode_htmlentities(x)], 
			'Air Date:' : ['releasedate', lambda x: datetime.strptime(x, '%B %d, %Y')],
			'Runtime:' : ['duration', lambda x: int(re.search("(\d*)", x).group(0)) * 60 * 1000 if int(re.search("(\d*)", x).group(0)) * 60 * 1000 < sys.maxint else 0],
			'Rating:' : ['rating', lambda x: float(re.search("([\d\.]+)", x).group(0)) * 2],
			'Title:': ['title', lambda x: decode_htmlentities(x)],
		}
		
		# For each extracted item from LMWT...
		for lmwt_item in info.keys():
		
			#Log("Processing: " + lmwt_item)
			
			# Look for matching entry in map...
			if lmwt_item not in item_map.keys():
				continue
				
			mi_item = item_map[lmwt_item]
			
			if (mi_item is None):
				#Log("Couldn't find a mi attr!")
				continue
				
			try:
				# And see if it's already set in the mediaInfo object.
				mi_val = getattr(mediainfo, mi_item[0], None)
				
				# And set it if it's not already.
				if (mi_val is None):
					setattr(mediainfo, mi_item[0],  mi_item[1](info[lmwt_item]))
						
			except Exception, ex:
				pass
				
		return mediainfo

	except Exception, ex:
		return None

####################################################################################################

def GetSources(url):

	# The description meta header for some shows inserts random double quotes in the
	# content which breaks the parsing of the page. Work around that by simply
	# removing the head section in which the meta elements are contained.
	headMassage = [(re.compile('<head>(.*)</head>', re.S), lambda match: '')]
	soupMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
	soupMassage.extend(headMassage)	
	
	soup = BeautifulSoup(HTTP.Request(LMWT_URL + url).content, markupMassage=soupMassage)

	sources = []
	
	for item in soup.find('div', { 'id': 'first' }).findAll('table', { 'class' : re.compile('movie_version.*') }):

		source = {}
		
		# Extract out source URL
		source['url'] = str(item.find('span', { 'class' : 'movie_version_link' }).a['href'][1:])
		
		# Extract out source name.
		source['name'] = str(item.find('span', { 'class' : 'movie_version_link' }).a.string)
		if (source['name'].lower().find('trailer') >= 0):
			continue
		
		# Extract out source quality.
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
		
		#Log(source)
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
		show.append(item.a['href'][1:])
		
		shows.append(show)
		
	return shows


####################################################################################################

def GetTVSeasons(url):

	# The description meta header for some shows inserts random double quotes in the
	# content which breaks the parsing of the page. Work around that by simply
	# removing the head section in which the meta elements are contained.
	headMassage = [(re.compile('<head>(.*)</head>', re.S), lambda match: '')]
	soupMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
	soupMassage.extend(headMassage)	
	
	soup = BeautifulSoup(HTTP.Request(LMWT_URL + url).content, markupMassage=soupMassage)

	items = []

	for item in soup.find("div", { 'id': 'first' }).findAll('h2'):
	
		items.append([str(item.a.string), item.a['href'][1:]])
		
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
			
			res.type = type

			# Extract out title
			title_alt = item.find('a')['title']
			res.title = re.search("Watch (.*)", title_alt).group(1)
			
			
			# Extract out URL
			res.id = item.a['href'][1:]
			
			# Extract out thumb
			res.poster = item.find('img')['src']
			
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

	url = LMWT_URL + "?" + type + "="
	
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
	
		#Log('Found item: ' + str(item))
		res = MediaInfo()
		
		res.type = type
		
		# Extract out title
		title_alt = item.find('a')['title']
		res.title = re.search("Watch (.*)", title_alt).group(1)
		
		# Extract out URL
		res.id = item.a['href'][1:]
		
		# Extract out thumb
		res.poster = item.find('img')['src']
		
		# Extract out rating
		rating_style = item.find('li')['style']
		res.rating = re.search("width:\s(\d)*px;", rating_style).group(1);
		
		# Add to item list.
		#Log("Adding item: " + str(res))
		items.append(res)
	
	#Log(items)
	return items

	
####################################################################################################
# PROVIDER SPECIFIC CODE
####################################################################################################

# Params:
#   mediainfo: A MediaInfo item for the current LMWT item being viewed (either a movie or single episode).
#   item:  A dictionary containing information for the selected source for the LMWT item being viewed.
def GetItemForSource(mediainfo, item):
	
	# See if provider is supported.
	providerURL = URLService.NormalizeURL(LMWT_URL + item['url'])
	providerSupported = URLService.ServiceIdentifierForURL(providerURL) is not None
	
	if (providerSupported):
	
		# See if we need to hide provider....
		providerInfoURL = "http://providerinfo." + item['provider_name'] + "/?plugin=lmwt"
		providerVisible =  'visible=true' in URLService.NormalizeURL(providerInfoURL)
		
		if (providerVisible):
		
			return VideoClipObject(
				url=providerURL,
				title=item['name'] + " - " + item['provider_name'],
				summary=mediainfo.summary,
				art=mediainfo.background,
				thumb= mediainfo.poster,
				rating = float(mediainfo.rating),
				duration=mediainfo.duration,
				source_title = item['provider_name'] ,
				year=mediainfo.year,
				originally_available_at=mediainfo.releasedate,
				genres=mediainfo.genres
			)
		
	# The only way we can get down here is if the provider wasn't supported or
	# the provider was supported but not visible. Maybe user still wants to see them?
	if (Prefs['show_unsupported']):
		return DirectoryObject(
			key = Callback(PlayVideoNotSupported, mediainfo = mediainfo, url = item['url']),
			title = item['name'] + " - " + item['provider_name'] + " (Not playable)",
			summary= mediainfo.summary,
			art=mediainfo.background,
			thumb= mediainfo.poster,
		)
	else:
		return

	
####################################################################################################
	
def PlayVideoNotSupported(mediainfo, url):

	return ObjectContainer(
		header='Provider is either not currently supported or has been disabled in preferences...',
		message='',
	)
	

@route('/video/lmwt/playback/{url}')
def PlaybackStarted(url):

	# If user doesn't want to save recently watched items, abort.
	if (Prefs['watched_amount'] == 'Disabled'):
		return ""
		
	# If we don't have a list of items user has recently browsed, abort.
	if (not Data.Exists(BROWSED_ITEMS_KEY)):
		return ""
	
	# Get list of items user has recently looked at.
	browsedItems =  cerealizer.loads(Data.Load(BROWSED_ITEMS_KEY))
	
	# Get clean copy of URL user has played.
	decoded_url = String.Decode(str(url))
	
	# See if the URL being played is on our recently browsed list.
	info = browsedItems.get(decoded_url)
	
	if (info is None):
		Log("****** ERROR: Watching Item which hasn't been browsed to")
		return ""
		
	# Get the bits of info out of the recently browsed item.
	mediainfo = info[0]
	path = info[1]
	
	# Load up viewing history, and add item to it.
	hist = get_watched_history()
		
	hist.add(mediainfo, path, int(Prefs['watched_amount']))
	
	Data.Save(VIEW_HIST_KEY, cerealizer.dumps(hist))
	
	#Log("Playback started on item:" + str(mediainfo))
	#Log("Viewing history: " + str(hist))
	
	return ""
	
###############################################################################
# UTIL METHODS
###############################################################################
# Substitute single HTML entity with match real character.

def substitute_entity(match):
	ent = match.group(3)
	
	if match.group(1) == "#":
		if match.group(2) == '':
			return unichr(int(ent))
		elif match.group(2) == 'x':
			return unichr(int('0x'+ent, 16))
	else:
		cp = n2cp.get(ent)

		if cp:
			return unichr(cp)
		else:
			return match.group()

###############################################################################
# Replace encoded HTML entities with matching real character.

def decode_htmlentities(string):
	entity_re = re.compile(r'&(#?)(x?)(\d{1,5}|\w{1,8});')
	return entity_re.subn(substitute_entity, string)[0]

###############################################################################
# 
def need_watched_indicator(type):

	if (type == 'tv' and Prefs['watched_indicator'] != 'Disabled'):
		return True
		
	if (type == 'movies' and Prefs['watched_indicator'] == 'All'):
		return True
	
	return False

###############################################################################
#
def get_watched_history():

	if (Data.Exists(VIEW_HIST_KEY)):
		hist = cerealizer.loads(Data.Load(VIEW_HIST_KEY))
	else:
		hist = ViewedItems()
		
	return hist
