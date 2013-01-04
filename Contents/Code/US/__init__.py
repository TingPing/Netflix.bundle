import cgi
from us_account import US_Account

ICON_MOVIES     = 'icon-movie.png'
ICON_PREFS      = 'icon-prefs.png'
ICON_SEARCH     = 'icon-search.png'

SEARCH_URL      = 'http://api-public.netflix.com/catalog/titles?v=2.0&term=%s&filters=http://api-public.netflix.com/categories/title_formats/instant'

MOVIE_PATTERN   = Regex('^http://(.)+\.netflix.com/catalog/titles/movies/[0-9]+$')
TVSHOW_PATTERN  = Regex('^http://(.)+\.netflix.com/catalog/titles/series/[0-9]+$')
SEASON_PATTERN  = Regex('^http://(.)+\.netflix.com/catalog/titles/series/[0-9]+/seasons/[0-9]+$')
EPISODE_PATTERN = Regex('^http://(.)+\.netflix.com/catalog/titles/programs/[0-9]+/[0-9]+')

EPISODE_TITLE_PATTERN = Regex('^S(?P<season>[0-9]+):E(?P<episode>[0-9]+) - (?P<title>.+)$')

###################################################################################################

def MainMenu():

  # Attempt to log in
  logged_in = US_Account.LoggedIn()
  if not logged_in:
    logged_in = US_Account.TryLogIn()

  oc = ObjectContainer(no_cache = True)

  if logged_in:
    
    oc.add(DirectoryObject(key = Callback(UserList), title = 'TV & Movies'))
    oc.add(DirectoryObject(key = Callback(MenuItem, url = 'http://api-public.netflix.com/users/%s/queues/instant' % US_Account.GetUserId(), title = 'Instant Queue', is_queue = True), title = 'Instant Queue'))
    oc.add(InputDirectoryObject(key = Callback(Search), title = 'Search', prompt = 'Search for a Movie or TV Show...', thumb = R(ICON_SEARCH)))

  else:

    # The user has not yet provided valid credentials. Therefore, we should allow them to be redirected
    # to sign up for a free trial.
    oc.add(DirectoryObject(key = Callback(FreeTrial), title = 'Sign up for free trial', thumb = R(ICON_MOVIES)))

  oc.add(PrefsObject(title = 'Preferences', thumb = R(ICON_PREFS)))

  return oc

###################################################################################################

@route('/video/netflix/us/userlist')
def UserList():

  oc = ObjectContainer()

  user_id = US_Account.GetUserId()
  user_list_url = US_Account.GetAPIURL('http://api-public.netflix.com/users/%s/lists' % user_id, params = { 'v': '2', 'client': 'plex' })
  user_list = XML.ElementFromURL(user_list_url)

  # Add the found items
  for item in user_list.xpath('//lists/list/link'):
    url = item.get('href')
    title = item.get('title')
    oc.add(DirectoryObject(key = Callback(MenuItem, url = url, title = title), title = title))

  return oc

###################################################################################################

@route('/video/netflix/us/search')
def Search(query):
  return MenuItem(SEARCH_URL % query, query)

###################################################################################################

@route('/video/netflix/us/freetrial')
def FreeTrial():
  url = "http://www.netflix.com/"
  webbrowser.open(url, new=1, autoraise=True)
  return MessageContainer("Free Trial Signup", """A browser has been opened so that you may sign up for a free trial.  If you do not have a mouse 
      and keyboard handy, visit http://www.netflix.com and sign up for free today!""")

###################################################################################################

@route('/video/netflix/us/menuitem', is_queue = bool)
def MenuItem(url, title, start_index = 0, max_results = 50, content = ContainerContent.Mixed, is_queue = False):
  oc = ObjectContainer(title2 = title, content = content)

  # Separate out the specified parameters from the original URL
  params = {}
  if url.find('?') > -1:
    original_params = String.ParseQueryString(url[url.find('?') + 1:])
    for key, value in original_params.items():
  	 params[key] = value[0]

  # Add the paging parameters
  params['start_index'] = str(start_index)
  params['max_results'] = str(max_results)

  # Add the additional parameters to ensure that we get all of the required items expaned.
  params['expand'] = '@title,@box_art,@synopsis,@directors,@seasons,@episodes'
  menu_item_url = US_Account.GetAPIURL(url, params = params)
  menu_item = XML.ElementFromURL(menu_item_url)

  show_url = None

  for item in menu_item.xpath('//catalog_title'):

    item_details = ParseCatalogueItem(item)

    # Movies
    if MOVIE_PATTERN.match(item_details['id']):

      if Prefs['playbackpreference'] != "Ask":
        video_url = PlaybackURL(item_details['url'], Prefs['playbackpreference'])
        oc.add(MovieObject(
          key = Callback(Lookup, type = "Movie", id = item_details['id']),
          items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = "Movie", url = video_url, id = item_details['id']))], protocol = 'webkit') ],
          rating_key = item_details['id'],
          title = item_details['title'],
          thumb = item_details['thumb'][0],
          summary = item_details['summary'],
          genres = item_details['genres'],
          directors = item_details['directors'],
          duration = item_details['duration'],
          rating = item_details['rating'],
          content_rating = item_details['content_rating']))
      else:
        oc.add(DirectoryObject(
          key = Callback(
            PlaybackSelection,
            url = item_details['url'],
            title = item_details['title'],
            type = "Movie",
            id = item_details['id'],
            thumb = item_details['thumb'][0],
            summary = item_details['summary'],
            directors = item_details['directors'],
            duration = item_details['duration'],
            rating = item_details['rating'],
            content_rating = item_details['content_rating'],
            genres = item_details['genres'],
            is_queue = is_queue),
          title = item_details['title'],
          thumb = item_details['thumb'][0],
          summary = item_details['summary'],
          duration = item_details['duration']))

    # TV Shows
    elif TVSHOW_PATTERN.match(item_details['id']):
      oc.add(TVShowObject(
        key = Callback(MenuItem, url = item_details['episode_url'], title = item_details['title'], content = ContainerContent.Seasons, is_queue = is_queue),
        rating_key = item_details['id'],
        title = item_details['title'],
        thumb = item_details['thumb'][0],
        summary = item_details['summary'],
        genres = item_details['genres'],
        duration = item_details['duration'],
        rating = item_details['rating'],
        content_rating = item_details['content_rating']))

    # TV Show Seasons
    elif SEASON_PATTERN.match(item_details['id']):
      oc.add(SeasonObject(
        key = Callback(MenuItem, url = item_details['episode_url'], title = item_details['title'], content = ContainerContent.Episodes),
        rating_key = item_details['id'],
        title = item_details['title'],
        thumb = item_details['thumb'][0],
        summary = item_details['summary'],
        episode_count = item_details['episode_count']))

    # TV Episodes
    elif EPISODE_PATTERN.match(item_details['id']):
      show_url = url

      if Prefs['playbackpreference'] != "Ask":
        video_url = PlaybackURL(item_details['url'], Prefs['playbackpreference'])
        oc.add(EpisodeObject(
          key = Callback(Lookup, type = "Episode", id = item_details['id']),
          items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = "Episode", url = video_url, id = item_details['id']))], protocol = 'webkit') ],
          rating_key = item_details['id'],
          title = item_details['title'],
          show = item_details['show'],
          season = item_details['season_index'],
          index = item_details['episode_index'],
          thumb = item_details['thumb'][0],
          summary = item_details['summary'],
          directors = item_details['directors'],
          duration = item_details['duration'],
          rating = item_details['rating'],
          content_rating = item_details['content_rating']))
      else:
        oc.add(DirectoryObject(
          key = Callback(
            PlaybackSelection,
            url = item_details['url'],
            title = item_details['title'],
            type = "Episode",
            id = item_details['id'],
            thumb = item_details['thumb'][0],
            summary = item_details['summary'],
            directors = item_details['directors'],
            duration = item_details['duration'],
            rating = item_details['rating'],
            content_rating = item_details['content_rating'],
            show = item_details['show'],
            season = item_details['season_index'],
            index = item_details['episode_index']),
          title = item_details['title'],
          thumb = item_details['thumb'][0],
          summary = item_details['summary'],
          duration = item_details['duration']))

  # Provide a way to remove a show from the Instant Queue.
  if Prefs['playbackpreference'] == "Ask" and is_queue and show_url:
    oc.add(DirectoryObject(
      key = Callback(RemoveFromQueue, url = show_url),
      title = "Remove",
      summary = "Remove this show from your Instant Queue."))

  # If there are further results, add an item to allow them to be browsed.
  start_index = int(start_index)
  max_results = int(max_results)
  number_of_results_node = menu_item.xpath('//number_of_results/text()')
  if len(number_of_results_node) > 0:
    number_of_results = int(number_of_results_node[0])
    if number_of_results > (start_index + max_results):
      oc.add(DirectoryObject(
        key = Callback(MenuItem, url = url, title = title, start_index = start_index + max_results, max_results = max_results), 
        title = "Next..."))

  # Check to see if we have any results
  if len(oc) == 0:
    return MessageContainer('No Results','No results were found')

  return oc

###################################################################################################

def ParseCatalogueItem(item):

  id = item.xpath('.//id/text()')[0]

  title_node = item.xpath('.//title')[0]
  title = title_node.get('short')

  video_url = item.xpath('.//link[contains(@title, "web page")]')[0].get('href')
  summary = String.StripTags(item.xpath('.//synopsis//text()')[0])
  content_rating = item.xpath('.//category[contains(@scheme, "_ratings")]')[0].get('term')

  directors = item.xpath('.//link[contains(@title, "directors")]/people/link')
  directors = [ director.get('title') for director in directors ]

  genres = item.xpath('.//category[contains(@scheme, "/categories/genres")]')
  genres = [ genre.get('label') for genre in genres]

  # [Optional]
  rating = None
  try: rating = float(item.xpath('.//average_rating/text()')[0]) * 2
  except: pass

  # [Optional]
  # Only certain items have durations (e.g. a TV Show Season does not)
  duration = None
  try: duration = int(item.xpath('.//runtime/text()')[0]) * 1000
  except: pass

  # There are mutiple resolutions available for artwork. We will just try to find all available and build up a list
  # with the highest first.
  artwork = []
  artwork_resolutions = ['HD box art', 'large box art', 'medium box art', 'small box art']
  for resolution in artwork_resolutions:
    node = item.xpath('.//box_art/link[contains(@title, "%s")]' % resolution)
    if len(node) == 1:
      artwork.append(node[0].get('href'))

  # [Optional]
  # Attempt to extract any episode details from the title
  # Example: The Office: Season 1: Pilot
  show = None
  episode_title_regular = title_node.get('regular')
  if episode_title_regular:
    show = episode_title_regular.split(':')[0]

  # [Optional]
  # Example: S1:E1 - Pilot
  season_index = None
  episode_index = None
  episode_title_short = title_node.get('episode_short')
  if episode_title_short:
    episode_details = EPISODE_TITLE_PATTERN.match(episode_title_short)
    if episode_details:
      episode_details_dict = episode_details.groupdict()
      title = episode_details_dict['title']
      season_index = int(episode_details_dict['season'])
      episode_index = int(episode_details_dict['episode'])

  # [Optional]
  episode_count = None
  try: episode_count = int(item.xpath('.//link[contains(@title, "episodes")]/catalog_titles/number_of_results/text()')[0])
  except: pass

  # [Optional]
  # If the item represents a TV Show, then it will contain a URL to access the available seasons
  season_url = None
  try: season_url = item.xpath('.//link[contains(@title, "seasons")]')[0].get('href')
  except: pass

  # [Optional]
  # If the item represents a TV Show Season, then it will contain a URL to access the available episodes
  episode_url = None
  try: episode_url = item.xpath('.//link[contains(@title, "episodes")]')[0].get('href')
  except: pass

  return {
    'id': id,
    'url': video_url,
    'season_url': season_url,
    'episode_url': episode_url,
    'title': title,
    'show': show,
    'season_index': season_index,
    'episode_index': episode_index,
    'episode_count': episode_count,
    'summary': summary,
    'duration': duration,
    'rating': rating,
    'content_rating': content_rating,
    'directors': directors,
    'genres': genres,
    'thumb': artwork}

###################################################################################################

def SetRating(key, rating):

  # The provided rating will be a value between 0 and 10. However, Netflix expects an interger 
  # between 1 and 5. Therefore, we must translate...
  netflix_rating = int(rating / 2)
  US_Account.SetTitleRating(key, netflix_rating)
  pass

###################################################################################################

@route('/video/netflix/us/removefromqueue')
def RemoveFromQueue(url):
    if US_Account.RemoveFromQueue(url):
        return ObjectContainer(header='Instant Queue', message='The item was removed from your queue.')
    else:
        return ObjectContainer(header='Instant Queue', message='There was a problem removing your item from the queue.')

###################################################################################################
def PlaybackURL(url, preference):
  if preference == "Resume":
    return url + '&resume=true'

  return url

###################################################################################################

@route('/video/netflix/us/playbackselection', directors = list, duration = int, genres = list, season = int, index = int, is_queue = bool)
def PlaybackSelection(url, title, type, id, thumb, summary, directors, duration, rating, content_rating, genres = None, show = None, season = None, index = None, is_queue = False):
  oc = ObjectContainer(title2 = title)

  # We have to deal with the fact that Ratings might actually be None for TV Shows
  try: rating = float(rating)
  except: rating = None

  if type == "Movie":
    video_url = PlaybackURL(url, "Restart")
    oc.add(MovieObject(
      key = Callback(Lookup, type = "Movie", id = id),
      items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = "Movie", url = video_url, id = id))], protocol = 'webkit') ],
      rating_key = id,
      title = "Restart",
      thumb = thumb,
      summary = summary,
      genres = genres,
      directors = directors,
      duration = duration,
      rating = rating,
      content_rating = content_rating))
    video_url = PlaybackURL(url, "Resume")

    oc.add(MovieObject(
      key = Callback(Lookup, type = "Movie", id = id),
      items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = "Movie", url = video_url, id = id))], protocol = 'webkit') ],
      rating_key = id,
      title = "Resume",
      thumb = thumb,
      summary = summary,
      genres = genres,
      directors = directors,
      duration = duration,
      rating = rating,
      content_rating = content_rating))

    if is_queue:
      oc.add(DirectoryObject(
        key = Callback(RemoveFromQueue, url = url),
        title = "Remove",
        thumb = thumb,
        summary = "Remove this movie from your Instant Queue."))
  elif type == "Episode":
    video_url = PlaybackURL(url, "Restart")
    oc.add(EpisodeObject(
      key = Callback(Lookup, type = "Episode", id = id),
      items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = "Episode", url = video_url, id = id))], protocol = 'webkit') ],
      rating_key = id,
      title = "Restart",
      show = show,
      season = season,
      index = index,
      thumb = thumb,
      summary = summary,
      directors = directors,
      duration = duration,
      rating = rating,
      content_rating = content_rating))

    video_url = PlaybackURL(url, "Resume")
    oc.add(EpisodeObject(
      key = Callback(Lookup, type = "Episode", id = id),
      items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = "Episode", url = video_url, id = id))], protocol = 'webkit') ],
      rating_key = id,
      title = "Resume",
      show = show,
      season = season,
      index = index,
      thumb = thumb,
      summary = summary,
      directors = directors,
      duration = duration,
      rating = rating,
      content_rating = content_rating))

  return oc

###################################################################################################

@route('/video/netflix/us/lookup')
def Lookup(type, id):
  oc = ObjectContainer()

  # Separate out the specified parameters from the original URL
  params = {}
  if id.find('?') > -1:
    original_params = String.ParseQueryString(id[id.find('?') + 1:])
    for key, value in original_params.items():
     params[key] = value[0]

  # Add the additional parameters to ensure that we get all of the required items expaned.
  params['expand'] = '@title,@box_art,@synopsis,@directors,@seasons,@episodes'
  item_url = US_Account.GetAPIURL(id, params = params)
  item = XML.ElementFromURL(item_url)

  item_details = ParseCatalogueItem(item)
  video_url = PlaybackURL(item_details['url'], Prefs['playbackpreference'])

  if type == "Movie":
    oc.add(MovieObject(
      key = Callback(Lookup, type = type, id = id),
      rating_key = id,
      items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = type, url = video_url, id = id))], protocol = 'webkit') ],
      title = item_details['title'],
      thumb = item_details['thumb'][0],
      summary = item_details['summary'],
      genres = item_details['genres'],
      directors = item_details['directors'],
      duration = item_details['duration'],
      rating = item_details['rating'],
      content_rating = item_details['content_rating']))
  else:
    oc.add(EpisodeObject(
      key = Callback(Lookup, type = type, id = id),
      rating_key = id,
      items = [ MediaObject(parts = [PartObject(key = Callback(PlayVideo, type = type, url = video_url, id = id))], protocol = 'webkit') ],
      title = item_details['title'],
      show = item_details['show'],
      season = item_details['season_index'],
      index = item_details['episode_index'],
      thumb = item_details['thumb'][0],
      summary = item_details['summary'],
      directors = item_details['directors'],
      duration = item_details['duration'],
      rating = item_details['rating'],
      content_rating = item_details['content_rating']))

  return oc

###################################################################################################

@route('/video/netflix/us/playvideo')
@indirect
def PlayVideo(type, url, id, indirect = None):
  oc = ObjectContainer()

  movie_id = re.match('http://www.netflix.com/Movie/.+/(?P<id>[0-9]+)', url).groupdict()['id']
  player_url = 'http://www.netflix.com/WiPlayer?movieid=%s' % movie_id
  user_url = "http://api-public.netflix.com/users/%s" % US_Account.GetUserId()

  params = {'movieid': movie_id, 'user': user_url}
  video_url = US_Account.GetAPIURL(player_url, params = params)

  # If the &resume=true parameter was specified, ensure that it's copied to the final webkit URL
  if url.endswith('&resume=true'):
    video_url = video_url + '&resume=true'
  Log("Final WebKit URL: " + video_url)

  oc.add(VideoClipObject(
    key = Callback(Lookup, type = type, id = id),
    rating_key = id,
    items = [
      MediaObject(
        parts = [PartObject(key = WebVideoURL(video_url))],
        protocol = 'webkit')
    ]
  ))

  return oc