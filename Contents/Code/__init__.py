import re
import US

TITLE = 'Netflix'

HTTP.Headers['Accept-Encoding'] = 'gzip,sdch'

###################################################################################################

def Start():

  ObjectContainer.title1 = TITLE

  InputDirectoryObject.thumb = R('search.png')

###################################################################################################

@handler('/video/netflix', TITLE)
def Menu():

  # Verify that Silverlight is currently installed.
  if Platform.HasSilverlight == False:
    return ObjectContainer(header='Error', message='Silverlight is required for the Netflix plug-in. On your Plex Media Server please visit http://silverlight.net to install.')

  return Main().MainMenu()

###################################################################################################

def SetRating(key, rating):
  Main().SetRating(key, rating)

###################################################################################################

def Main():
  return US
