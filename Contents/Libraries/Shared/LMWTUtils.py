import urllib2, base64

LMWT_PLAYBACK_URL = "http://127.0.0.1:32400/video/lmwt/playback/%s"

def PlaybackStarted(url):
	
	
	# Bad things can happen here. Still want to run rest of code if possible though...
	#try:
	url_encode = base64.urlsafe_b64encode(url)
	
	print(LMWT_PLAYBACK_URL % url_encode)
	request = urllib2.Request(LMWT_PLAYBACK_URL % url_encode)
	response = urllib2.urlopen(request)
	#except Exception, ex:
	#	print(str(ex))
	#	pass
			
#PlaybackStarted("http://daclips.com/ht1hpm4x4qte?lmwt_playback_hist=%2Fwatch-2280191-Hangover-r2")
