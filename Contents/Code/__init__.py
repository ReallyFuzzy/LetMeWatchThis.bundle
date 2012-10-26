import re
import cerealizer
import urllib
import urllib2
import copy
import sys
import base64

import Parsing

from datetime       import date, datetime
from dateutil       import tz
from htmlentitydefs import name2codepoint as n2cp
from urlparse       import urlparse

from BeautifulSoup  import BeautifulSoup

from MetaProviders  import MediaInfo
from RecentItems    import BrowsedItems, ViewedItems
from Favourites     import FavouriteItems

cerealizer.register(MediaInfo)

VIDEO_PREFIX = "/video/lmwt"
NAME = L('Title')

VERSION = "12.10.26.1"
VERSION_URLS = {
	"12.10.26.1": "http://bit.ly/PUBAWJ",
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

BROWSED_ITEMS_KEY = "RECENT_BROWSED_ITEMS"
WATCHED_ITEMS_KEY = "USER_VIEWING_HISTORY"
FAVOURITE_ITEMS_KEY = "FAVOURITE_ITEMS"

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
		Thread.Create(VersionTracking)
		
	# Check the favourite object and viewing history object are of the right type.
	# This should be a one-off hit as we migrate to new data structure.
	if (type(load_favourite_items()) is not FavouriteItems):
		Log("********** Need to remove favourites as they are old type.")
		Data.Remove(FAVOURITE_ITEMS_KEY)
		
	if (not hasattr(load_watched_items(), "recent_items")):
		Log("********** Need to remove Recently Watched / Viewing History as they are old type.")
		Data.Remove(WATCHED_ITEMS_KEY)	

	Thread.Create(CheckForNewItemsInFavourites)
	
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
		
	
	
	title = str(L("Favourites"))

	if (len([x for x in load_favourite_items().get() if x.new_item]) > 0):
		title += " - New item(s) available"
		
	oc.add(
		DirectoryObject(
			key=Callback(FavouritesMenu,parent_name=oc.title2,),
			title=title,
			tagline=L("FavouritesSubtitle"),
			summary=L("FavouritesSummary"),
			thumb=R("Favorite.png"),
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
	
	items = Parsing.GetItems(type, genre, sort, alpha, num_pages, start_page)
	
	func_name = TVSeasonMenu
	
	hist = None
	
	if (type=="movies"):
		func_name = SourcesMenu
		if (need_watched_indicator(type)):
			hist = load_watched_items()
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
		if (hist is not None):
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
# TV SEASONS MENUS
####################################################################################################
def TVSeasonMenu(mediainfo=None, url=None, item_name=None, path=[], parent_name=None):

	if (item_name is not None):
		mediainfo.show_name = item_name
		
	if (mediainfo.show_name is None and mediainfo.title is not None):
		mediainfo.show_name = mediainfo.title
								
	oc = ObjectContainer(view_group = "InfoList", title1=parent_name, title2=mediainfo.show_name)
	
	path = path + [{'elem':mediainfo.show_name, 'show_url':url}]
	
	# Retrieve the imdb id out as this is what favourites are keyed on and this is the
	# first level where an item can be added to favourites.
	mediainfo.id = Parsing.GetMediaInfo(url, mediainfo.type).id
	
	#Log(mediainfo)
	
	oc.add(
		PopupDirectoryObject(
			key=Callback(TVSeasonActionMenu, mediainfo=mediainfo, path=path),
			title=L("TVSeasonActionTitle"),
		)
	)
	
	items = Parsing.GetTVSeasons("/" + url)
	
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

def TVSeasonActionMenu(mediainfo, path):

	oc = ObjectContainer(view_group="InfoList", title1="", title2="")
	
	if (Prefs['watched_indicator'] != 'Disabled'):
		oc.add(
			DirectoryObject(
				key=Callback(TVSeasonActionWatch, item_name=path[-1]['elem'], mediainfo=mediainfo, path=path, action="watch"),
				title="Mark Show as Watched",
			)
		)
	
		oc.add(
			DirectoryObject(
				key=Callback(TVSeasonActionWatch, item_name=path[-1]['elem'], mediainfo=mediainfo, path=path, action="unwatch"),
				title="Mark Show as Unwatched",
			)
		)
	
	# These won't get used and are keyed to a specific episode, so reset them.
	mediainfo.url = None
	mediainfo.summary = None
	mediainfo.season = None
	
	# Come up with a nice easy title for later.
	mediainfo.title = mediainfo.show_name
	
	fav_path = [item for item in path if ('show_url' in item)]
	
	oc.add(
		DirectoryObject(
			key=Callback(HistoryAddToFavouritesMenu, mediainfo=mediainfo, path=[fav_path[0]], parent_name=oc.title2),
			title="Add Show to Favourites",
		)
	)
	
	return oc
	
####################################################################################################

def TVSeasonActionWatch(item_name=None, mediainfo=None, path=None, action="watch"):

	items = []
	base_path = [item for item in path if ('show_url' in item)]
	show_url = base_path[0]['show_url']
	
	# Get a list of all seasons for this show.
	for item in Parsing.GetTVSeasons("/" + show_url):
	
		item_path = copy.copy(base_path)
		item_mediainfo = copy.copy(mediainfo)
		item_mediainfo.season = item[0]
		item_path.append({ 'elem': item[0], 'season_url': item[1] })
		items.append([item_mediainfo, item_path])
		
	# Mark them as watched / unwatched.
	return TVSeasonShowsActionWatch(item_name=item_name, items=items, action=action)


####################################################################################################
# TV SEASON SHOWS MENUS
####################################################################################################
def TVSeasonShowsMenu(mediainfo=None, season_url=None,item_name=None, path=[], parent_name=None):

	path = path + [{'elem':item_name,'season_url':season_url}]
	
	if (item_name is not None):
		mediainfo.season = item_name

	need_indicator = need_watched_indicator('tv')
	
	# Is this in the user's favourites
	
	oc = ObjectContainer(no_cache=need_indicator, view_group="InfoList", title1=parent_name, title2=item_name)
	
	# Get Viewing history if we need an indicator.
	hist = None
	if (need_indicator):
		hist = load_watched_items()
		
	indicator = ""
	if (hist is not None):
		indicator = "    "
	
	oc.add(
		PopupDirectoryObject(
			key=Callback(TVSeasonShowsActionMenu, mediainfo=mediainfo, path=path),
			title=indicator + str(L("TVSeasonShowsActionTitle")),
		)
	)
	
	for item in Parsing.GetTVSeasonShows("/" + season_url):
	
		indicator = ''
		
		if (hist is not None):
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

def TVSeasonShowsActionMenu(mediainfo, path):

	oc = ObjectContainer(view_group="InfoList", title1="", title2="Season Actions")
	
	if (Prefs['watched_indicator'] != 'Disabled'):
		oc.add(
			DirectoryObject(
				key=Callback(TVSeasonShowsActionWatch, item_name=path[-1]['elem'], items=[[mediainfo, path]], action="watch"),
				title="Mark All Episodes as Watched",
			)
		)
	
		oc.add(
			DirectoryObject(
				key=Callback(TVSeasonShowsActionWatch, item_name=path[-1]['elem'], items=[[mediainfo, path]], action="unwatch"),
				title="Mark All Episodes as Unwatched",
			)
		)
	
	# These won't get used and are keyed to a specific episode, so reset them.
	mediainfo.url = None
	mediainfo.summary = None

	# Come up with a nice easy title for later.
	mediainfo.title = mediainfo.show_name + " - " + mediainfo.season

	fav_path = [item for item in path if ('season_url' in item or 'show_url' in item)]
	oc.add(
		DirectoryObject(
			key=Callback(HistoryAddToFavouritesMenu, mediainfo=mediainfo, path=fav_path, parent_name=oc.title2),
			title="Add Season to Favourites"
		)
	)
	
	return oc

####################################################################################################

def TVSeasonShowsActionWatch(item_name=None, items=None, action="watch"):

	episode_items = []
	
	for item in items:
	
		mediainfo = item[0]
		path = item[1]

		base_path = [item for item in path if ('season_url' in item or 'show_url' in item)]
		season_url = [item for item in path if ('season_url' in item)][0]['season_url']
		
		episode_paths = []
		
		# Get a list of all the episodes for this season.
		for item in Parsing.GetTVSeasonShows("/" + season_url):
		
			item_path = copy.copy(base_path)
			item_path.append({ 'elem': item[0], 'url': item[1] })
			episode_paths.append(item_path)
		
		episode_items.append([mediainfo, episode_paths])
		
	# Mark them as watched / unwatched.
	return SourcesActionWatch(item_name=item_name, items=episode_items, action=action)


####################################################################################################
# SOURCES MENUS
####################################################################################################
def SourcesMenu(mediainfo=None, url=None, item_name=None, path=[], parent_name=None):
	
	if (item_name is None):
		item_name = mediainfo.title
	
	path = path + [ { 'elem': item_name, 'url': url } ]
	
	oc = ObjectContainer(view_group="List", title1=parent_name, title2=item_name)
	
	# Get as much meta data as possible about this item.
	mediainfo2 = Parsing.GetMediaInfo(url, mediainfo.type)
	
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
		
	oc.add(
		PopupDirectoryObject(
			key=Callback(SourcesActionMenu, mediainfo=mediainfo, path=path),
			title=L("ItemSourceActionTitle"),
			tagline=None,
			summary=None,
			thumb=None,

		)
	)
	
	providerURLs = []
	for item in Parsing.GetSources(url):
	
		if (item['quality'] == "sponsored"):
			continue
					
		mediaItem = GetItemForSource(mediainfo=mediainfo2, item=item)
		
		if mediaItem is not None:
			oc.add(mediaItem)
			if (hasattr(mediaItem, 'url')):
				providerURLs.append(mediaItem.url)
					
	if len(oc.objects) == 1:
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

def SourcesActionMenu(mediainfo, path):

	oc = ObjectContainer(view_group="InfoList", title1="", title2="")
	
	if (
		Prefs['watched_indicator'] == 'All' 
		or ( mediainfo.type == 'tv' and Prefs['watched_indicator'] != 'Disabled')
	):
		title = "Mark as Watched"
		action = "watch"
		hist = load_watched_items()
		
		if (hist.has_been_watched(path[-1]['url'])):
			title = "Mark as Unwatched"
			action = "unwatch"
			
		oc.add(
			DirectoryObject(
				key=Callback(SourcesActionWatch, item_name=path[-1]['elem'], items=[[mediainfo, [path]]], action=action),
				title=title,
			)
		)
	
	if (mediainfo.type == "movies"):
		oc.add(
			DirectoryObject(
				key=Callback(HistoryAddToFavouritesMenu, item_name=path[-1]['elem'], mediainfo=mediainfo, path=[path[-1]], parent_name=oc.title2),
				title="Add to Favourites",
			)
		)

	if (len(oc.objects) == 0):
		oc.add(
			DirectoryObject(
				key=Callback(NoOpMenu),
				title="No Options Available",
			)
		)

		oc.header="No Options Available"
		oc.message="No options currently available for this item. Enable Watched indicators to get options."
		
	return oc

####################################################################################################

def SourcesActionWatch(item_name=None, items=None, action="watch"):

	oc = ObjectContainer(title1="", title2="")
	
	watched_favs = []
	hist = load_watched_items()

	for item in items:
	
		mediainfo = item[0]
		paths = item[1]
		
		for path in paths:
			if (action == "watch"):
				hist.mark_watched(path)
			else:
				hist.mark_unwatched(path[-1]['url'])
				
	save_watched_items(hist)
	
	# Deal with Favourites.
	if (action == "watch"):
		
		# Favourites keep their own list of what shows they consider to have been watched
		Thread.AcquireLock(FAVOURITE_ITEMS_KEY)
		
		try:
			favs = load_favourite_items()
			for item in items:
				mediainfo = item[0]
				paths = item[1]
				for path in paths:
					watched_favs.extend(favs.watch(mediainfo, path[-1]['url']))
			save_favourite_items(favs)
		except Exception, ex:
			Log(ex)
			pass		
		finally:
			Thread.ReleaseLock(FAVOURITE_ITEMS_KEY)
		
		for fav in set(watched_favs):
			Thread.Create(CheckForNewItemsInFavourite, favourite=fav, force=True)


	# Normal processing.
	if (action == "watch"):
		oc.header = L("ItemSourceActionMarkAsWatchedHeader")
		oc.message = str(L("ItemSourceActionMarkAsWatchedMessage")) % item_name	
	else:
		oc.header = L("ItemSourceActionMarkAsUnwatchedHeader")
		oc.message = str(L("ItemSourceActionMarkAsUnwatchedMessage")) % item_name

	return oc
	
####################################################################################################

def SearchResultsMenu(query, type, parent_name=None):

	oc = ObjectContainer(no_cache=True, view_group = "InfoList", title1=parent_name, title2="Search (" + query + ")")

	path = [ { 'elem':'Search (' + query + ')', 'query': query }]
	
	func_name = TVSeasonMenu
	if (type=="movies"):
		func_name = SourcesMenu
		
	for item in Parsing.GetSearchResults(query=query, type=type):
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
# HISTORY MENU
####################################################################################################
def HistoryMenu(parent_name=None):

	oc = ObjectContainer(no_cache=True, view_group="InfoList", title1=parent_name, title2=L("HistoryTitle"))
	
	history = load_watched_items().get_recent(Prefs['watched_grouping'], int(Prefs['watched_amount']))
	
	# For each viewed video. 
	for item in history:
		
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
		PopupDirectoryObject(
			key=Callback(HistoryClearMenu, parent_name=parent_name),
			title=L("HistoryClearTitle"),
			summary=L("HistoryClearSummary"),
		)
	)
	
	return oc

####################################################################################################

def HistoryClearMenu(parent_name=None):

	oc = ObjectContainer(no_cache=True, title1="", title2="")
	
	oc.add(
		DirectoryObject(
			key=Callback(HistoryClearRecent, parent_name=parent_name),
			title=L("HistoryClearRecentTitle"),
			summary=L("HistoryClearRecentSummary"),
		)
	)
	
	oc.add(
		DirectoryObject(
			key=Callback(HistoryClearAll, parent_name=parent_name),
			title=L("HistoryClearAllTitle"),
			summary=L("HistoryClearAllSummary"),
		)
	)
	
	return oc
	
####################################################################################################

def HistoryClearRecent(parent_name=None):

	hist = load_watched_items()
	hist.clear_recent()
	save_watched_items(hist)
	
	oc = HistoryMenu(parent_name=parent_name)
	oc.replace_parent = True
	return oc
	
####################################################################################################

def HistoryClearAll(parent_name=None):

	Data.Remove(WATCHED_ITEMS_KEY)
	Data.Remove(BROWSED_ITEMS_KEY)
	
	oc = HistoryMenu(parent_name=parent_name)
	oc.replace_parent = True
	return oc

####################################################################################################

def HistoryNavPathMenu(mediainfo, navpath, parent_name):

	oc = ObjectContainer(title1=parent_name, title2=L("HistoryTitle"))
	
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
			key=Callback(NoOpMenu),
			title='----------------------'
		)
	)
	
	# Remove from recently watched list.
	oc.add(
		DirectoryObject(
			key=Callback(HistoryRemoveFromRecent, mediainfo=mediainfo, path=path, parent_name=oc.title2),
			title="Remove from Recently Watched"
		)
	)
			
	
	# Add to Favourites menu options.
	# Deal with the fact that the path to be added to favourites is different
	# based on type of item this is.
	if (mediainfo.type == 'tv'):
	
		# These won't get used and are keyed to a specific episode, so reset them.
		mediainfo.url = None
		mediainfo.summary = None
				
		# Come up with a nice easy title for later.
	
		if (Prefs['watched_grouping'] != 'Show'):
		
			mediainfo_season = copy.copy(mediainfo)
			mediainfo_season.title = mediainfo.show_name + ' - ' + mediainfo.season
			path = [item for item in navpath if ('season_url' in item or 'show_url' in item)]
			oc.add(
				DirectoryObject(
					key=Callback(HistoryAddToFavouritesMenu, mediainfo=mediainfo_season, path=path, parent_name=oc.title2),
					title=str(L("HistoryAddToFavouritesItem")) % path[-1]['elem']
				)
			)
			
		mediainfo.title = mediainfo.show_name
		mediainfo.season = None
		path = [item for item in navpath if ('show_url' in item)]
		
		if (Prefs['watched_grouping'] == 'Show'):
			title = L("HistoryAddToFavourites")
		else:
			title=str(L("HistoryAddToFavouritesItem")) % path[0]['elem']
			
		oc.add(
			DirectoryObject(
				key=Callback(HistoryAddToFavouritesMenu, mediainfo=mediainfo, path=[path[0]], parent_name=oc.title2),
				title=title
			)
		)
		
	else:
		oc.add(
			DirectoryObject(
				key=Callback(HistoryAddToFavouritesMenu, mediainfo=mediainfo, path=[navpath[-1]], parent_name=oc.title2),
				title=L("HistoryAddToFavourites")
			)
		)
		
	return oc

####################################################################################################

def HistoryRemoveFromRecent(mediainfo, path, parent_name):

	hist = load_watched_items()
	hist.remove_from_recent(mediainfo, Prefs['watched_grouping'])
	save_watched_items(hist)			
	
####################################################################################################

def HistoryAddToFavouritesMenu(mediainfo, path, parent_name):

	oc = ObjectContainer(title1=parent_name, title2=L("HistoryAddToFavourites"))
	
	# Keep it simple. Add given item and path to favourites.
	Thread.AcquireLock(FAVOURITE_ITEMS_KEY)
	try:
		favs = load_favourite_items()
		favs.add(mediainfo, path)
		save_favourite_items(favs)
	except Exception, ex:
		Log(ex)
		pass		
	finally:
		Thread.ReleaseLock(FAVOURITE_ITEMS_KEY)
		
	oc.header = L("HistoryFavouriteAddedTitle")
	oc.message = str(L("HistoryFavouriteAddedMsg")) % path[-1]['elem']
	
	return oc


####################################################################################################
# FAVOURITES MENUS
####################################################################################################
def FavouritesMenu(parent_name=None):

	oc = ObjectContainer(no_cache=True, view_group="InfoList", title1=parent_name, title2=L("FavouritesTitle"))
	
	sort_order = FavouriteItems.SORT_DEFAULT
	if (Prefs['favourite_sort'] == 'Alphabetical'):
		sort_order = FavouriteItems.SORT_ALPHABETICAL
	elif (Prefs['favourite_sort'] == 'Most Recently Used'):
		sort_order = FavouriteItems.SORT_MRU
		
	favs = load_favourite_items().get(sort=sort_order)
	
	# For each favourite item....
	for item in favs:
		
		mediainfo = item.mediainfo
		navpath = item.path
		
		title = mediainfo.title
		if (item.new_item):
			title = title + " - New Item(s)"
				
		# If the item is a TV show, come up with sensible display name.
		summary = ""
		if (mediainfo.type == 'movies'):
			summary = mediainfo.summary
		else:
			if (item.new_item_check):
				local = item.date_last_item_check.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
				if (item.new_item):
					summary += str(L("FavouritesNewItemNotifySummaryNew")) % local.strftime("%Y-%m-%d %H:%M")
				else:
					summary += str(L("FavouritesNewItemNotifySummaryNoNew")) % local.strftime("%Y-%m-%d %H:%M")
		
		oc.add(
			PopupDirectoryObject(
				key=Callback(
					FavouritesNavPathMenu,
					mediainfo=item.mediainfo,
					path=item.path,
					new_item_check=item.new_item_check,
					parent_name=oc.title2
				),
				title= title,
				summary=summary,
				art=mediainfo.background,
				thumb= mediainfo.poster,
				duration=mediainfo.duration,
				
			)
		)
			
	oc.add(
		DirectoryObject(
			key=Callback(FavouritesClearMenu),
			title=L("FavouritesClearTitle"),
			summary=L("FavouritesClearSummary"),
		)
	)
		
	return oc

####################################################################################################

def FavouritesClearMenu():

	Data.Remove(FAVOURITE_ITEMS_KEY)
	
	oc = FavouritesMenu()
	oc.replace_parent = True
	return oc

####################################################################################################

def FavouritesNavPathMenu(mediainfo=None, path=None, new_item_check=None, parent_name=None):

	oc = ObjectContainer(title1=parent_name, title2="Favourites")
	
	# Grab a copy of the path we can update as we're iterating through it.
	cur_path = list(path)
	
	# The path as stored in the system is top down. However, we're going to
	# display it in reverse order (bottom up), so match that.
	cur_path.reverse()
		
	for item in reversed(path):
	
		# When the users select this option, the selected option will automatically
		# be re-added to the path by the called menu function. So, remove it now so
		# we don't get duplicates.
		if (len(cur_path) > 0):
			cur_path.pop(0)
			
	
		# The order in which we're processing the path (bottom up) isn't the 
		# same as how it was navigated (top down). So, reverse it to
		# put in the right order to pass on to the normal navigation functions.
		ordered_path = list(cur_path)
		ordered_path.reverse()
	
		# Depending on the types of args present, we may end up calling different methods.
		#
		# If we have an item URL, take user to provider list for that URL
		if ("url" in item):
			callback = Callback(
				SourcesMenu, mediainfo=mediainfo, url=item['url'], item_name=None, path=ordered_path, parent_name=oc.title2)
			
		# If we have a show URL, take user to season listing for that show
		elif ("show_url" in item):
			callback = Callback(TVSeasonMenu, mediainfo=mediainfo, url=item['show_url'], item_name=mediainfo.show_name, path=ordered_path, parent_name=oc.title2)
		
		# If we have a season URL, take user to episode listing for that season.
		elif ("season_url" in item):
			callback = Callback(TVSeasonShowsMenu, mediainfo=mediainfo, season_url=item['season_url'], item_name=mediainfo.season, path=ordered_path, parent_name=oc.title2)
		
		oc.add(
			DirectoryObject(
				key=callback,
				title=item['elem']
			)
		)
		
	oc.add(
		DirectoryObject(
			key=Callback(NoOpMenu),
			title='----------------------'
		)
	)
	
	oc.add(
		DirectoryObject(
			key=Callback(FavouritesRemoveItemMenu, mediainfo=mediainfo),
			title=L("FavouritesRemove"),
		)
	)
	
	if (mediainfo.type == 'tv'):
		title = L("FavouritesNewItemNotifyTurnOn")
		if (new_item_check):
			title = L("FavouritesNewItemNotifyTurnOff")
			
		oc.add(
			DirectoryObject(
				key=Callback(FavouritesNotifyMenu, mediainfo=mediainfo),
				title=title
			)
		)
	
	
	return oc

####################################################################################################

def FavouritesRemoveItemMenu(mediainfo):

	# Keep it simple. Remove item from favourites.
	Thread.AcquireLock(FAVOURITE_ITEMS_KEY)
	try:
		favs = load_favourite_items()
		favs.remove(mediainfo)
		save_favourite_items(favs)
	except Exception, ex:
		Log(ex)
		pass		
	finally:
		Thread.ReleaseLock(FAVOURITE_ITEMS_KEY)

	
	oc = FavouritesMenu()
	oc.replace_parent = True
	return oc

####################################################################################################

def FavouritesNotifyMenu(mediainfo=None):

	oc = ObjectContainer(title1="", title2="")
	
	# Load up favourites and get reference to stored favourite rather than
	# dissociated favourite that's been passed in.
	
	Thread.AcquireLock(FAVOURITE_ITEMS_KEY)
	try:
		favs = load_favourite_items(lock=True)
		fav = favs.get(mediainfo=mediainfo)[0]
		
		# Are we turning it on or off?
		if (fav.new_item_check):
		
			
			# Turning it off.
			fav.new_item_check = False
			fav.new_item = None
			fav.items = None
			fav.date_last_item_check = None
			oc.message = "Plugin will no longer check for new items."
		
		else:
		
			# Turning it on.
			fav.new_item_check = True
			fav.new_item = False
			
			# Get page URL
			url = [v for k,v in fav.path[-1].items() if (k == 'show_url' or k == 'season_url')][0]
			
			# Get URLs of all the shows for the current favourite.
			fav.items = [show[1] for show in Parsing.GetTVSeasonShows(url)]
			
			fav.date_last_item_check = datetime.utcnow()
			oc.message = "Plugin will check for new items and notify you when one is available.\nNote that this may slow down the plugin at startup."
			
		save_favourite_items(favs)
		
	finally:
		Thread.ReleaseLock(FAVOURITE_ITEMS_KEY)
		
	oc.header = "New Item Notification"
	
	return oc
	
	
def NoOpMenu():

	return ""

####################################################################################################
# FAVOURITE UTILS
####################################################################################################

def CheckForNewItemsInFavourites():

	favs = load_favourite_items().get()
		
	for fav in favs:
		CheckForNewItemsInFavourite(fav)
		
	# Re-check in 12 hour.
	Thread.CreateTimer(12 * 60 * 60, CheckForNewItemsInFavourites)

	
def CheckForNewItemsInFavourite(favourite, force=False):
	
	#Log("Processing favourite: " + str(favourite.mediainfo))
	
	# Do we want to check this favourite for updates?
	# If so, only bother if it's not already marked as having updates.
	if (favourite.new_item_check and (favourite.new_item == False or force)):
	
		#Log("Checking for new item in favourite")
		
		# Get page URL
		url = [v for k,v in favourite.path[-1].items() if (k == 'show_url' or k == 'season_url')][0]
	
		# Get up-to-date list of shows available for the current favourite.
		items = [show[1] for show in Parsing.GetTVSeasonShows(url)]
					
		# Are there any items in the current show list which aren't in the fav's show list?
		# Note that all of these should automatically be unwatched since as items are watched,
		# the favourites are updated with the url of the watched item. So, even if the 
		# favourite wasn't aware of the watched item (i.e: new item since last check),
		# it will still have been added to its list of watched items.
		items_set = set(items)
		new_items = items_set.difference(set(favourite.items))
		#Log("Found new items: " + str(new_items))
			
		# Items list is different.
		# Because we may be taking a while to do this
		# processing (we're relying on making a whole lot of HTTP requests to get
		# items list), the favourites list may have changed. We could lock it for
		# the duration of this whole method, but this may be a long lock. Instead,
		# .....
		Thread.AcquireLock(FAVOURITE_ITEMS_KEY)
		try:
			favs_disk = load_favourite_items()
			fav_disk = favs_disk.get(favourite.mediainfo)[0]
		
			fav_disk.new_item = len(new_items) > 0
			fav_disk.date_last_item_check = datetime.utcnow()
		
			save_favourite_items(favs_disk)
		except Exception, ex:
			Log(str(ex))
			pass
		finally:
			Thread.ReleaseLock(FAVOURITE_ITEMS_KEY)

	
####################################################################################################
# Params:
#   mediainfo: A MediaInfo item for the current LMWT item being viewed (either a movie or single episode).
#   item:  A dictionary containing information for the selected source for the LMWT item being viewed.
def GetItemForSource(mediainfo, item):
	
	item = Parsing.GetItemForSource(mediainfo, item)
	
	if item is not None:
		return item
		
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

	# Nothing to do. User doesn't want any tracking.
	if (Prefs['watched_indicator'] == 'Disabled' and Prefs['watched_amount'] == 'Disabled'):
		return ""
		
	# Get clean copy of URL user has played.
	decoded_url = String.Decode(str(url))

	# Get list of items user has recently looked at.
	browsedItems =  cerealizer.loads(Data.Load(BROWSED_ITEMS_KEY))
	
	# See if the URL being played is on our recently browsed list.
	info = browsedItems.get(decoded_url)
	
	if (info is None):
		Log("****** ERROR: Watching Item which hasn't been browsed to")
		return ""
	
	# Get the bits of info out of the recently browsed item.
	mediainfo = info[0]
	path = info[1]

	# Does user want to keep track of watched items?
	if (Prefs['watched_indicator'] != 'Disabled'):
		# Load up viewing history, and add item to it.
		hist = load_watched_items()
		hist.mark_watched(path)
		save_watched_items(hist)
	
	# Does user also want to keep track of Recently Watched Items?
	if (Prefs['watched_amount'] != 'Disabled' and Data.Exists(BROWSED_ITEMS_KEY)):
						
		# Load up viewing history, and add item to it.
		hist = load_watched_items()
		hist.add_recent(mediainfo, path, Prefs['watched_grouping'], int(Prefs['watched_amount']))
		save_watched_items(hist)
	
	# Favourites keep their own list of what shows they consider to have been watched to make
	# sure their new unwatched show functionality works as expected.
	if (mediainfo.type == 'tv'):
	
		Thread.AcquireLock(FAVOURITE_ITEMS_KEY)
		watched_favs = []
		try:
			favs = load_favourite_items()
			watched_favs = favs.watch(mediainfo, path[-1]['url'])
			save_favourite_items(favs)
		except Exception, ex:
			Log(ex)
			pass
		finally:
			Thread.ReleaseLock(FAVOURITE_ITEMS_KEY)
			
		# Even though this specific item has now been played, we can't just set the favourites
		# new_item to false as there might have been multiple new items. So, check if this
		# favourite still has new items or not.
		for fav in watched_favs:
			#Log(str(fav))
			Thread.Create(CheckForNewItemsInFavourite, favourite=fav, force=True)

	#Log("Playback started on item:" + str(mediainfo))
	#Log("Viewing history: " + str(hist))
	
	return ""
	
def VersionTrack():

	try:
		request = urllib2.Request(VERSION_URLS[VERSION])
		request.add_header('User-agent', '-')	
		response = urllib2.urlopen(request)
	except:
		pass

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
def load_watched_items():

	if (Data.Exists(WATCHED_ITEMS_KEY)):
		hist = cerealizer.loads(Data.Load(WATCHED_ITEMS_KEY))
	else:
		hist = ViewedItems()
		
	return hist

###############################################################################
#	
def save_watched_items(hist):

	Data.Save(WATCHED_ITEMS_KEY, cerealizer.dumps(hist))
	
###############################################################################
#
def load_favourite_items(lock=False):

	if (Data.Exists(FAVOURITE_ITEMS_KEY)):
		try:
			favs = cerealizer.loads(Data.Load(FAVOURITE_ITEMS_KEY))
		except cerealizer.NotCerealizerFileError, ex:
			favs = FavouriteItems()
	else:
		favs = FavouriteItems()
		
	return favs

###############################################################################
#
def save_favourite_items(favs):
	
	Data.Save(FAVOURITE_ITEMS_KEY, cerealizer.dumps(favs))