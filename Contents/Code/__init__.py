import re
import cerealizer
import urllib
import urllib2
import copy
import sys
import base64

from datetime       import date, datetime
from dateutil       import tz

from BeautifulSoup  import BeautifulSoup

# Non-standard imports.
import Parsing

import demjson

from MetaProviders  import DBProvider, MediaInfo
from RecentItems    import BrowsedItems, ViewedItems
from Favourites     import FavouriteItems

cerealizer.register(MediaInfo)

VIDEO_PREFIX = "/video/lmwt"
NAME = L('Title')

VERSION = "12.11.06.2"
VERSION_URLS = {
	"12.11.06.2": "http://bit.ly/Vy4Wfb",
	"12.11.06.1": "http://bit.ly/Vy4Wfb",
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

	# Make this plugin show up in the 'Video' section
	Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, APP_ICON, ART)

	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	Plugin.AddViewGroup('PanelStream', viewMode='PanelStream', mediaType='items')
	Plugin.AddViewGroup('MediaPreview', viewMode='MediaPreview', mediaType='items')

	# Set some defaults
	MediaContainer.title1 = NAME
	MediaContainer.viewGroup = "InfoList"
	MediaContainer.art = R(ART)
	MediaContainer.userAgent = USER_AGENT
	
	ObjectContainer.art=R(ART)
	ObjectContainer.user_agent = USER_AGENT

	DirectoryItem.thumb = R(APP_ICON)
	VideoItem.thumb = R(APP_ICON)
	
	DirectoryObject.thumb = R(APP_ICON)
	VideoClipObject.thumb = R(APP_ICON)
	
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-agent'] = USER_AGENT
	HTTP.Headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
	HTTP.Headers['Accept-Encoding'] = '*gzip, deflate'
	HTTP.Headers['Connection'] = 'keep-alive'
	
	if (Prefs['versiontracking'] == True):
		Thread.Create(VersionTrack)
		
	# Check the favourite object and viewing history object are of the right type.
	# This should be a one-off hit as we migrate to new data structure.
	try: 
		if (type(load_favourite_items()) is not FavouriteItems):
			Log("********** Need to remove favourites as they are old type.")
			Data.Remove(FAVOURITE_ITEMS_KEY)
	except:
		# Let's be aggressive about this. Something went wrong, let's assume it's do
		# with the stored data being wrong somehow.
		Log("********** Need to remove favourites as they are old type.")
		Data.Remove(FAVOURITE_ITEMS_KEY)
		pass
		
	try:
		if (not hasattr(load_watched_items(), "recent_items")):
			Log("********** Need to remove Recently Watched / Viewing History as they are old type.")
			Data.Remove(WATCHED_ITEMS_KEY)
	except:
		Log("********** Need to remove Recently Watched / Viewing History as they are old type.")
		Data.Remove(WATCHED_ITEMS_KEY)
		
	# We need to do a one off migration from storing season names to storing season numbers.
	# Can remove once we have no users left on v.12.10.26.1 or below.
	if ("FAVS_MIGRATION_1211" not in Dict):
	
		try:
			favs = load_favourite_items()
		
			for fav in favs.get():
		
				if (
					fav is not None and
					fav.mediainfo.type == 'tv' and
					hasattr(fav.mediainfo, "season") and
					isinstance(fav.mediainfo.season, str)
				):
					match = re.search("(\d+)", fav.mediainfo.season)
					if (match):
						Log("SETTING SEASON TO " + match.group(1))
						fav.mediainfo.season = int(match.group(1))
					else:
						fav.mediainfo.season = None
					
			save_favourite_items(favs)
			
			recents = load_watched_items()
			
			for recent in recents.get_recent():
		
				if (
					recent is not None and
					recent[0].type == 'tv' and
					hasattr(recent[0], "season") and
					isinstance(recent[0].season, str)
				):
					match = re.search("(\d+)", recent[0].season)
					if (match):
						Log("SETTING SEASON TO " + match.group(1))
						recent[0].season = int(match.group(1))
					else:
						recent[0].season = None
						
			save_watched_items(recents)
			
			Dict['FAVS_MIGRATION_1211'] = True
			
		except Exception, ex:
			Log(str(ex))
		
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

	# Clean up mediainfo that's been passed in from favourites as it will be
	# keyed for a specifc ep and not a show.
	mediainfo.season = None
	mediainfo.ep_num = None
	
	if (item_name is not None):
		mediainfo.show_name = item_name
		
	if (mediainfo.show_name is None and mediainfo.title is not None):
		mediainfo.show_name = mediainfo.title
								
	oc = ObjectContainer(view_group = "InfoList", title1=parent_name, title2=mediainfo.show_name)
	
	path = path + [{'elem':mediainfo.show_name, 'show_url':url}]
	
	# Retrieve the imdb id out as this is what favourites are keyed on and this is the
	# first level where an item can be added to favourites.
	mediainfo_meta = Parsing.GetMediaInfo(url, mediainfo, need_meta_retrieve(mediainfo.type))
	
	mediainfo.id = mediainfo_meta.id
	mediainfo.background = mediainfo_meta.background
	mediainfo.summary = mediainfo_meta.summary
	mediainfo.show_name = mediainfo_meta.show_name
	
	# When the passed in from favourites or Recently Watched, the mediainfo is for
	# the episode actually watched. So, the poster will be for the ep, not the show.
	# However, show info may have previously been retrieved. So use that if available.
	if hasattr(mediainfo,'show_poster'):
		mediainfo.poster = mediainfo.show_poster
	else:
		mediainfo.poster = mediainfo_meta.poster
			
	oc.add(
		PopupDirectoryObject(
			key=Callback(TVSeasonActionMenu, mediainfo=mediainfo, path=path),
			title=L("TVSeasonActionTitle"),
			art=mediainfo.background,
			thumb=mediainfo.poster,
			summary=mediainfo.summary,
		)
	)
	
	items = Parsing.GetTVSeasons("/" + url)
	
	for item in items:
	
		# Look for a real season number from the LMWT Season name.
		season = int(re.match("Season (\d*)", item[0]).group(1))
		
		# Grab a copy of the current mediainfo and customise it to the current
		# season, ready to be passed through to season show list.
		mediainfo_season = copy.copy(mediainfo)
		mediainfo_season.season = season
		
		# Does the meta provider have a poster for this season?
		if (hasattr(mediainfo_meta,"season_posters") and season in mediainfo_meta.season_posters):
			# Yup. Use that.
			mediainfo_season.poster = mediainfo_meta.season_posters[season]
		
		oc.add(
			DirectoryObject(
				key=Callback(
					TVSeasonShowsMenu,
					mediainfo=mediainfo_season,
					item_name=item[0],
					season_url=item[1],
					path=path,
					parent_name=oc.title2,
				),
				title=item[0],
				tagline="",
				summary="",
				thumb=mediainfo_season.poster,
				art=mediainfo_season.background,
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

	# Clean up media info that's been passed in from favourites / recently watched.
	mediainfo.ep_num = None
	
	path = path + [{'elem':item_name,'season_url':season_url}]

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
		
	if (need_meta_retrieve(mediainfo.type)):
	
		# Construct kwargs.
		kwargs = {}
		kwargs['imdb_id'] = mediainfo.id
		kwargs['season'] = mediainfo.season
	
		mediainfo_meta = DBProvider().GetProvider(mediainfo.type).RetrieveItemFromProvider(**kwargs)
	else:
		mediainfo_meta = None
		
	# When the passed in from favourites or Recently Watched, the mediainfo is for
	# the episode actually watched. So, the poster will be for the ep, not the season.
	# Since, we've retrieved info about the season, use that as our opportunity to use
	# the correct poster.
	if hasattr(mediainfo,'season_poster'):
		mediainfo.poster = mediainfo.season_poster
	elif mediainfo_meta and mediainfo_meta.poster:
		mediainfo.poster = mediainfo_meta.poster
		
	if (mediainfo_meta and not mediainfo.background and mediainfo_meta.background):
		mediainfo.background = mediainfo_meta.background
	
	oc.add(
		PopupDirectoryObject(
			key=Callback(TVSeasonShowsActionMenu, mediainfo=mediainfo, path=path),
			title=indicator + str(L("TVSeasonShowsActionTitle")),
			thumb=mediainfo.poster,
			art=mediainfo.background,
		)
	)

	for item in Parsing.GetTVSeasonShows("/" + season_url):
	
		ep_num = int(re.match("Episode (\d*)", item[0]).group(1))
		
		mediainfo_ep = copy.copy(mediainfo)
		mediainfo_ep.ep_num = ep_num
				
		# Does this LMWT episode actually exist according to meta provider?
		if (
			mediainfo_meta and
			hasattr(mediainfo_meta,'season_episodes') and 
			ep_num in mediainfo_meta.season_episodes
		):
			mediainfo_ep.summary = mediainfo_meta.season_episodes[ep_num]['summary']
			mediainfo_ep.title = "Episode " + str(ep_num) + " - " + mediainfo_meta.season_episodes[ep_num]['title']
			if mediainfo_meta.season_episodes[ep_num]['poster']:
				mediainfo_ep.poster = mediainfo_meta.season_episodes[ep_num]['poster']
		else:
			mediainfo_ep.summary = ""
			mediainfo_ep.title = item[0]
		
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
					mediainfo=mediainfo_ep,
					url=item[1],
					item_name=item[0],
					path=path,
					parent_name=oc.title2,
				),
				title=indicator + mediainfo_ep.title,
				tagline=mediainfo_ep.title,
				summary=mediainfo_ep.summary,
				thumb=mediainfo_ep.poster,
				art=mediainfo_ep.background,
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
	mediainfo.title = mediainfo.show_name + " - Season " + str(mediainfo.season)

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
	mediainfo2 = Parsing.GetMediaInfo(url, mediainfo, need_meta_retrieve(mediainfo.type))
		
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
			summary=mediainfo2.summary,
			art=mediainfo2.background,
			thumb= mediainfo2.poster,
			duration=mediainfo2.duration,
		)
	)
	
	providerURLs = []
	for source_item in Parsing.GetSources(url):
	
		if (source_item['quality'] == "sponsored"):
			continue
					
		mediaItem = GetItemForSource(mediainfo=mediainfo2, source_item=source_item)
		
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
				key=Callback(HistoryAddToFavouritesMenu, mediainfo=mediainfo, path=[path[-1]], parent_name=oc.title2),
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
		poster = mediainfo.poster
		
		if (mediainfo.type == 'tv'):
			
			# If the item is a TV show, come up with sensible display info
			# that matches the requested grouping.
			summary = None

			if hasattr(mediainfo,"show_poster"):
				poster = mediainfo.show_poster
			
			if (mediainfo.show_name is not None):
				title = mediainfo.show_name
				
			if (
				(Prefs['watched_grouping'] == 'Season' or Prefs['watched_grouping'] == 'Episode') and
				mediainfo.season is not None
			):
				title += ' - Season ' + str(mediainfo.season)
				
				# If we have a season poster available, use that rather than show's poster.
				#Log("Checking for season poster.....")
				if hasattr(mediainfo,"season_poster") and mediainfo.season_poster:
					poster = mediainfo.season_poster
				
			if (Prefs['watched_grouping'] == 'Episode'):
				title = title + ' - ' + mediainfo.title
				poster = mediainfo.poster
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
				thumb=poster,
				duration=mediainfo.duration,
				
			)
		)
			
	oc.add(
		PopupDirectoryObject(
			key=Callback(HistoryClearMenu, parent_name=parent_name),
			title=L("HistoryClearTitle"),
			summary=L("HistoryClearSummary"),
			thumb=None,
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
				callback = Callback(TVSeasonShowsMenu, mediainfo=mediainfo, season_url=item['season_url'], item_name="Season " + str(mediainfo.season), path=ordered_path, parent_name=oc.title2)
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
			title=L("NoOpTitle")
		)
	)
	
	# Remove from recently watched list.
	oc.add(
		DirectoryObject(
			key=Callback(HistoryRemoveFromRecent, mediainfo=mediainfo, path=path, parent_name=oc.title2),
			title=L("HistoryRemove")
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
			mediainfo_season.title = mediainfo.show_name + ' - Season ' + str(mediainfo.season)
			if hasattr(mediainfo_season,"season_poster") and mediainfo_season.season_poster:
				mediainfo_season.poster = mediainfo_season.season_poster
				
			path = [item for item in navpath if ('season_url' in item or 'show_url' in item)]
			oc.add(
				DirectoryObject(
					key=Callback(HistoryAddToFavouritesMenu, mediainfo=mediainfo_season, path=path, parent_name=oc.title2),
					title=str(L("HistoryAddToFavouritesItem")) % path[-1]['elem']
				)
			)
			
		mediainfo.title = mediainfo.show_name
		mediainfo.season = None
		
		if hasattr(mediainfo,"show_poster") and mediainfo.show_poster:
				mediainfo.poster = mediainfo.show_poster
		
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
def FavouritesMenu(parent_name=None, new_items_only=None):

	oc = ObjectContainer(no_cache=True, view_group="InfoList", title1=parent_name, title2=L("FavouritesTitle"))
	
	oc.replace_parent = new_items_only is not None
	
	if (new_items_only):
		oc.title2 = L("FavouritesTitleNewOnly")
	
	sort_order = FavouriteItems.SORT_DEFAULT
	if (Prefs['favourite_sort'] == 'Alphabetical'):
		sort_order = FavouriteItems.SORT_ALPHABETICAL
	elif (Prefs['favourite_sort'] == 'Most Recently Used'):
		sort_order = FavouriteItems.SORT_MRU
		
	oc.add(
		PopupDirectoryObject(
			key=Callback(FavouritesActionMenu, parent_name=parent_name,new_items_only=new_items_only),
			title=L("FavouritesActionTitle"),
			thumb="",
		)
	)
		
	favs = load_favourite_items().get(sort=sort_order)
	
	# For each favourite item....
	for item in favs:
		
		mediainfo = item.mediainfo
		navpath = item.path
		
		title = mediainfo.title
		if (item.new_item):
			title = title + " - New Item(s)"
		else:
			if (new_items_only):
				continue
				
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
			
	return oc

####################################################################################################

def FavouritesActionMenu(parent_name=None, new_items_only=False):

	oc = ObjectContainer(no_cache=True, view_group="InfoList", title1="", title2="Clear All Your Favourites?")

	if new_items_only:
		oc.add(
			DirectoryObject(
				key=Callback(FavouritesMenu, parent_name=parent_name, new_items_only=False),
				title=L("FavouritesShowAll")
			)
		)
	else:
		oc.add(
			DirectoryObject(
				key=Callback(FavouritesMenu, parent_name=parent_name, new_items_only=True),
				title=L("FavouritesShowNew")
			)
		)

	
	oc.add(
		DirectoryObject(
			key=Callback(NoOpMenu),
			title=L("NoOpTitle")
		)
	)

	oc.add(
		DirectoryObject(
			key=Callback(FavouritesClearMenu, parent_name=parent_name),
			title=L("FavouritesClearTitle")
		)
	)
		
	return oc

####################################################################################################

def FavouritesClearMenu(parent_name=None):
	
	Data.Remove(FAVOURITE_ITEMS_KEY)
	
	oc = FavouritesMenu(parent_name=parent_name)
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
			callback = Callback(TVSeasonShowsMenu, mediainfo=mediainfo, season_url=item['season_url'], item_name="Season " + str(mediainfo.season), path=ordered_path, parent_name=oc.title2)
		
		oc.add(
			DirectoryObject(
				key=callback,
				title=item['elem']
			)
		)
		
	oc.add(
		DirectoryObject(
			key=Callback(NoOpMenu),
			title=L("NoOpTitle")
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
def GetItemForSource(mediainfo, source_item):
	
	media_item = Parsing.GetItemForSource(mediainfo, source_item)
	
	if media_item is not None:
		return media_item
		
	# The only way we can get down here is if the provider wasn't supported or
	# the provider was supported but not visible. Maybe user still wants to see them?
	if (Prefs['show_unsupported']):
		return DirectoryObject(
			key = Callback(PlayVideoNotSupported, mediainfo = mediainfo, url = source_item['url']),
			title = source_item['name'] + " - " + source_item['provider_name'] + " (Not playable)",
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
	

@route('/video/lmwt/mediainfo/{url}')
def MediaInfoLookup(url):

	""" Returns the media info stored in the recently browsed item list
	for the given provider URL or None if the item isn't found in the
	recently browsed item list"""
	
	# Get clean copy of URL user has played.
	decoded_url = String.Decode(str(url))

	# Get list of items user has recently looked at.
	browsedItems =  cerealizer.loads(Data.Load(BROWSED_ITEMS_KEY))
	
	# See if the URL being played is on our recently browsed list.
	info = browsedItems.get(decoded_url)

	if (info is None):
		Log("****** ERROR: Watching Item which hasn't been browsed to")
		return ""
	
	# Return the media info that was stored in the recently browsed item.
	return demjson.encode(info[0])
	
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
def need_meta_retrieve(type):

	"""
	Returns a bool indicating whether the user has set preferences to
	query a 3rd party metadata provider for the given media info type.
	"""
	if (Prefs['meta_retrieve'] == 'Disabled'):
		return False
	elif (Prefs['meta_retrieve'] == 'All'):
		return True
	elif (type == 'tv' and Prefs['meta_retrieve'] == 'TV Shows'):
		return True
	elif (type == 'movies' and Prefs['meta_retrieve'] == 'Movies'):
		return True
	else:
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
		favs = cerealizer.loads(Data.Load(FAVOURITE_ITEMS_KEY))
	else:
		favs = FavouriteItems()
		
	return favs

###############################################################################
#
def save_favourite_items(favs):
	
	Data.Save(FAVOURITE_ITEMS_KEY, cerealizer.dumps(favs))