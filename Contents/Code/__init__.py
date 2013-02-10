import re
import US

TITLE = 'Netflix'
ART = 'art-default.jpg'
ICON = 'icon-default.png'

HTTP.Headers['Accept-Encoding'] = 'gzip,sdch'

###################################################################################################

def Start():

  ObjectContainer.title1 = TITLE
  ObjectContainer.art = R(ART)

  DirectoryObject.thumb = R(ICON)
  DirectoryObject.art = R(ART)
  VideoClipObject.thumb = R(ICON)
  VideoClipObject.art = R(ART)
  InputDirectoryObject.thumb = R('search.png')
  InputDirectoryObject.art = R(ART)

###################################################################################################

@handler('/video/netflix', TITLE, thumb=ICON, art=ART)
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
