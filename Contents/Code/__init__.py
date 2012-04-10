import re

import US

TITLE           = 'Netflix'
ART             = 'art-default.png'
ICON_DEFAULT    = 'icon-default.png'

###################################################################################################

def Start():

  # Set the types of view groups
  Plugin.AddViewGroup('List', viewMode = 'List', mediaType = 'items')
  Plugin.AddViewGroup('InfoList', viewMode = 'InfoList', mediaType = 'items')

  ObjectContainer.title1 = TITLE
  ObjectContainer.view_group = 'List'
  ObjectContainer.art = R(ART)

  DirectoryObject.thumb = R(ICON_DEFAULT)
  DirectoryObject.art = R(ART)
  VideoClipObject.thumb = R(ICON_DEFAULT)
  VideoClipObject.art = R(ART)

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
