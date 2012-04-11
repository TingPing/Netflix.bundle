import re

import US

TITLE           = 'Netflix'
ART             = 'art-default.png'
ICON_DEFAULT    = 'icon-default.png'
ICON_SEARCH     = 'icon-search.png'

###################################################################################################

def Start():

  ObjectContainer.title1 = TITLE
  ObjectContainer.art = R(ART)

  DirectoryObject.thumb = R(ICON_DEFAULT)
  DirectoryObject.art = R(ART)
  VideoClipObject.thumb = R(ICON_DEFAULT)
  VideoClipObject.art = R(ART)
  InputDirectoryObject.thumb = R(ICON_SEARCH)
  InputDirectoryObject.art = R(ART)

###################################################################################################

@handler('/video/netflix', TITLE)
def Menu():

  # Verify that Silverlight is currently installed.
  if Platform.HasSilverlight == False:
    return MessageContainer('Error', 'Silverlight is required for the Netflix plug-in. Please visit http://silverlight.net to install.')

  return Main().MainMenu()

###################################################################################################

def SetRating(key, rating):
  Main().SetRating(key, rating)

###################################################################################################

def Main():
  return US
