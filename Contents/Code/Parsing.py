import re
import urllib
import copy
import sys

from datetime import datetime
from BeautifulSoup import BeautifulSoup, NavigableString

import Utils

from MetaProviders import DBProvider, MediaInfo

LMWT_URL = "http://www.letmewatchthis.ch/"
LMWT_SEARCH_URL= "%sindex.php"


def Init():

	# Check for current provider URL.
	if ('LMWT_URL' not in Dict):
		Dict['LMWT_URL'] = LMWT_URL
		
	try:	
		content = HTML.ElementFromURL("https://github.com/ReallyFuzzy/LetMeWatchThis.bundle/wiki/CurrentURI",cacheTime=0)
		Dict['LMWT_URL'] = str(content.xpath("//div[@class='markdown-body']//a/@href")[0])
	except Exception,ex:
		Log(ex)
		pass
	
	Dict['LMWT_SEARCH_URL'] = LMWT_SEARCH_URL % Dict['LMWT_URL']

####################################################################################################
# LMWT PAGE PARSING
####################################################################################################

def GetMediaInfo(url, mediainfo, query_external=False):

	"""
	Retrieve meta data about the passed in LMWT item from a meta provider.
	Additionally, for any info not returned by the meta provider, try to
	collect the info directly from the LMWT item page.
	"""

	# The description meta header for some shows inserts random double quotes in the
	# content which breaks the parsing of the page. Work around that by simply
	# removing the head section in which the meta elements are contained.
	headMassage = [(re.compile('<head>(.*)</head>', re.S), lambda match: '')]
	soupMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
	soupMassage.extend(headMassage)
	
	soup = BeautifulSoup(HTTP.Request(Dict['LMWT_URL'] + url).content, markupMassage=soupMassage)

	try:
	
		imdb_id = None
		try:
			imdb_link = soup.find('div','mlink_imdb').a['href']
			imdb_id = re.search("(tt\d+)", str(imdb_link)).group()
		except:
			pass
		
		# Construct kwargs.
		kwargs = {}
		
		kwargs['imdb_id'] = imdb_id	
		kwargs['show_name'] = mediainfo.show_name
		kwargs['season'] = mediainfo.season
		
		if hasattr(mediainfo, 'ep_num'):
			kwargs['ep_num'] = mediainfo.ep_num
		
		if (query_external):
			#Log("Query-ing External Provider")
			mediainfo_ret = DBProvider().GetProvider(mediainfo.type).RetrieveItemFromProvider(**kwargs)
			#Log(str(mediainfo))
		else:
			mediainfo_ret = MediaInfo()
			mediainfo_ret.id = imdb_id
		
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
			'Description:' : ['summary', lambda x: Utils.decode_htmlentities(x)], 
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
				#Log("Not processing - no mapping")
				continue
				
			mi_item = item_map[lmwt_item]
			
			if (mi_item is None):
				#Log("Couldn't find a mi attr!")
				continue
				
			try:
				# And see if it's already set in the mediaInfo object.
				mi_val = getattr(mediainfo_ret, mi_item[0], None)
				
				#Log("Current mi value: " + str(mi_val))
				
				# And set it if it's not already.
				if (not mi_val):
					#Log("Setting mi attr " + mi_item[0] + " to: " + str(mi_item[1](info[lmwt_item])))
					setattr(mediainfo_ret, mi_item[0],  mi_item[1](info[lmwt_item]))
						
			except Exception, ex:
				#Log.Exception("Error whilst reading in info from LMWT Page. Field " + lmwt_item)
				pass
				
		return mediainfo_ret

	except Exception, ex:
		#Log.Exception("Error whilst retrieving mediainfo.")
		return None

####################################################################################################

def GetSources(url):

	# The description meta header for some shows inserts random double quotes in the
	# content which breaks the parsing of the page. Work around that by simply
	# removing the head section in which the meta elements are contained.
	headMassage = [(re.compile('<head>(.*)</head>', re.S), lambda match: '')]
	soupMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
	soupMassage.extend(headMassage)	
	
	soup = BeautifulSoup(HTTP.Request(Dict['LMWT_URL'] + url).content, markupMassage=soupMassage)

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
		#quality_elem = item.find('span', { 'class': re.compile('quality_.*') })
		#quality = re.search("quality_(.*)", quality_elem['class']).group(1)
		#source['quality'] = quality
		
		#if (quality == 'sponsored'):
		#	continue
				
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
			
		if ("sponsor" in provider_name.lower()):
			continue
			
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

def GetTVSeasonEps(url, no_cache=False):

	# The description meta header for some shows inserts random double quotes in the
	# content which breaks the parsing of the page. Work around that by simply
	# removing the head section in which the meta elements are contained.
	headMassage = [(re.compile('<head>(.*)</head>', re.S), lambda match: '')]
	soupMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
	soupMassage.extend(headMassage)	
	
	cacheTime = 0 if no_cache else HTTP.CacheTime
	
	soup = BeautifulSoup(HTTP.Request(Dict['LMWT_URL'] + url, cacheTime=cacheTime).content, markupMassage=soupMassage)
	
	eps = []
	
	for item in soup.findAll('div', { 'class': 'tv_episode_item' }):
	
		ep = {}
		
		title = str(item.a.contents[0]).strip()
		
		if (item.a.span is not None):
			title = title + " " + str(item.a.span.string).strip()
		
		ep['ep_name'] = title
		ep['ep_url'] =item.a['href'][1:]
		
		match = re.search("Episode (\d+)", ep['ep_name'])
		
		if match:
			ep['ep_num'] = int(match.group(1))
		
		eps.append(ep)
		
	return eps


####################################################################################################

def GetTVSeasons(url):

	# The description meta header for some shows inserts random double quotes in the
	# content which breaks the parsing of the page. Work around that by simply
	# removing the head section in which the meta elements are contained.
	headMassage = [(re.compile('<head>(.*)</head>', re.S), lambda match: '')]
	soupMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
	soupMassage.extend(headMassage)	
	
	soup = BeautifulSoup(HTTP.Request(Dict['LMWT_URL'] + url).content, markupMassage=soupMassage)

	seasons = []

	for item in soup.find("div", { 'id': 'first' }).findAll('h2'):
	
		season = {}
		season['season_name'] = str(item.a.string)
		season['season_url'] = item.a['href'][1:] 
		
		match = re.search("Season (\d+)", season['season_name'])
		
		if match:
			season['season_number'] = int(match.group(1))

		eps = []
		
		# Get next item that's not a string.
		ep = item.nextSibling
		while (ep and isinstance(ep, NavigableString)):
			ep = ep.nextSibling
		
		# While the next item that's not a string is a DIV...
		while ep and ep.name == 'div':
			if (ep['class'] == 'tv_episode_item'):
				eps.append({ 'ep_url': ep.a['href'][1:] })
			
			ep = ep.nextSibling
			while (ep and isinstance(ep, NavigableString)):
				ep = ep.nextSibling
			
		if (len(eps) > 0):
			season['season_episodes'] = eps
			
		seasons.append(season)
		
	return seasons


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
			res.title = re.search("Watch (.*)", item.find('a')['title']).group(1).strip()
			match = re.search("(.*)\((\d*)\)", res.title)
			
			if (match):
				res.title = match.group(1).strip()
				res.year = int(match.group(2).strip())
			
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

	url = Dict['LMWT_URL'] + "?" + type + "="
	
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

def GetSearchResults(query=None,type=None,imdb_id=None, exact=False):
	
	items = []
	
	
	if (imdb_id):
	
		res = MediaInfo()
		res.type = type
		res.id = "/item.php?imdb=" + imdb_id
		res.title = query
		
		items.append(res)
		
	else:
	
		soup = BeautifulSoup(HTTP.Request(Dict['LMWT_SEARCH_URL'] + "?search",cacheTime=0).content)
		key = soup.find('input', { 'type': 'hidden', 'name': 'key' })['value']
		
		section = "1"
		if (type == "tv"):
			section = "2"
		
		url = Dict['LMWT_SEARCH_URL'] + "?search_section=" + section + "&search_keywords=" + urllib.quote_plus(query) + "&key=" + key + "&sort=views"
		soup = BeautifulSoup(HTTP.Request(url,cacheTime=0).content)
		#Log(soup)
		
		for item in soup.findAll("div", { 'class': 'index_item index_item_ie' }):
		
			#Log('Found item: ' + str(item))
			res = MediaInfo()
			
			res.type = type
			
			# Extract out title
			res.title = re.search("Watch (.*)", item.find('a')['title']).group(1).strip()
			match = re.search("(.*)\((\d*)\)", res.title)
			
			if (match):
				res.title = match.group(1).strip()
				res.year = int(match.group(2).strip())
			
			# Extract out URL
			res.id = item.a['href'][1:]
			
			# Extract out thumb
			res.poster = item.find('img')['src']
			
			# Extract out rating
			rating_style = item.find('li')['style']
			res.rating = re.search("width:\s(\d)*px;", rating_style).group(1);
			
			# Add to item list.
			#Log("Adding item: " + str(res))
			if not exact or res.title.lower() == query.lower():
				items.append(res)
	
	#Log(items)
	return items
	
	
# Params:
#   mediainfo: A MediaInfo item for the current LMWT item being viewed (either a movie or single episode).
#   item:  A dictionary containing information for the selected source for the LMWT item being viewed.
def GetItemForSource(mediainfo, source_item):
	
	providerInfoURL = "http://providerinfo." + source_item['provider_name'].lower() + "/?plugin=lmwt"
	providerSupported = URLService.ServiceIdentifierForURL(providerInfoURL) is not None
	
	if (providerSupported):
	
		# See if we need to hide provider by asking the URL service to normalise it's special
		# providerinfo URL. This should return a URL where the query string is made up of
		# all the options that URL Service supports in this plugin's little world. 
		providerInfoNormalised = URLService.NormalizeURL(providerInfoURL)
		providerVisible =  'visible=true' in providerInfoNormalised
		
		if (providerVisible):
	
			return VideoClipObject(
				url=Dict['LMWT_URL'] + source_item['url'],
				title=source_item['name'] + " - " + source_item['provider_name'],
				summary=mediainfo.summary,
				art=mediainfo.background,
				thumb= mediainfo.poster,
				rating = float(mediainfo.rating),
				duration=mediainfo.duration,
				source_title = source_item['provider_name'] ,
				year=mediainfo.year,
				originally_available_at=mediainfo.releasedate,
				genres=mediainfo.genres
			)
			
	return None
	