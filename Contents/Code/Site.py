VIDEO_PREFIX = "/video/lmwt"
NAME = "Let Me Watch This"

LATEST_VERSION_URL = 'https://bit.ly/xoGzzQ'

# Plugin interest tracking.
VERSION = "13.08.28.1"
VERSION_URLS = {
	"13.08.28.1": "http://bit.ly/ZTqp3A",
	"13.08.15.1": "http://bit.ly/ZTqp3A",
	"13.05.10.1": "http://bit.ly/ZTqp3A",
	"13.05.05.1": "http://bit.ly/102Wvtb",
	"12.12.11.1": "http://bit.ly/UQnFkz",
	"12.11.24.1": "http://bit.ly/WojpGg",
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

FEATURED_ICON='icon-featured.png'
GENRE_ICON='icon-genre.png'
AZ_ICON='icon-az.png'

ADDITIONAL_SOURCES = ['icefilms']

def GetGenres():

	return [
		"Action", "Adventure", "Animation", "Biography", "Comedy", "Crime", "Documentary", "Drama",
		"Family", "Fantasy", "History", "Horror", "Japanese", "Korean", "Music", "Musical", "Mystery",
		"Romance", "Sci-Fi", "Short", "Sport", "Thriller", "War", "Western", "Zombies"
	]
	
def GetSections(type, genre):

	type_desc = "Movies"
	if (type == "tv"):
		type_desc = "TV Shows"
		
	sections = [
		{ 
			'title': 'Popular',
			'summary': "List of most popular " + type_desc,
			'icon': R("Popular.png"),
			'sort': 'views',
			'type': 'items',
		},
		{
			'title': 'Featured',
			'summary': "List of featured " + type_desc,
			'icon': R(FEATURED_ICON),
			'sort': 'featured',
			'type': 'items',
		},
		{ 
			'title': 'Highly Rated',
			'summary': "List of highly rated " + type_desc,
			'icon': R("Favorite.png"),
			'sort': 'ratings',
			'type': 'items',
		},
		{
			'title': 'Recently Added',
			'summary': "List of recently added " + type_desc,
			'icon': R("History.png"),
			'sort': 'date',
			'type': 'items',
		},
		{
			'title': 'Latest Releases',
			'summary': "List of latest releases",
			'icon': R("Recent.png"),
			'sort': 'release',
			'type': 'items',
		},
	]	
	
	if (not genre):
			
		sections.append(
			{
				'title':"Genre",
				'summary':"Browse " + type_desc + " by genre.",
				'icon':R(GENRE_ICON),
				'type':'genre'
			}
		)
		
		sections.append(
			{
				'title': "A-Z List",
				'summary': "Browse " + type_desc + " in alphabetical order",
				'icon': R(AZ_ICON),
				'type': 'alphabet'
			}
		)
			
		sections.append(
			{
				'type': 'search'
			}
		)
		
	return sections