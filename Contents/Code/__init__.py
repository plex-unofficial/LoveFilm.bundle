# Additional
import webbrowser
import re
import datetime
import time

# Plugin
import lovefilm

####################################################################################################

VIDEO_PREFIX = "/video/lovefilm"

TOKEN_KEY = 'accesstoken'

NAME = L('Title')

ART = 'art-default.png'
ICON = 'icon-default.png'
ICON_COMPUTER = 'icon-movie.png'
ICON_USER = 'icon-user.png'
ICON_SEARCH = 'icon-search.png'

MAX_SEARCH_RESULTS = 25

GOOGLE_LOOKUP = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s+site:imdb.com"
IMDB_DETAILS_PAGE = "http://www.imdb.com/video/imdb/%s/html5"

ERROR = MessageContainer('Network Error','A Network error has occurred')

####################################################################################################

# This function is initially called by the PMS framework to initialize the plugin. This includes
# setting up the Plugin static instance along with the displayed artwork.
def Start():

    # Initialize the plugin
    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, Locale.LocalString('Title'), ICON, ART)
    Plugin.AddViewGroup("Basic", viewMode = "InfoList", mediaType = "items")
    Plugin.AddViewGroup("Basic", viewMode = "List", mediaType = "items")

    # Setup the artwork associated with the plugin
    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)
    
    # Set the default localization
    Locale.SetDefaultLocale(loc = "en-gb")

    # Reset the user's dictionary. This is only used as a temporary cache which shoud live the
    # lifetime of the application. When we restart, we will re-cache in order to ensure that all
    # the information is up to date.
    Dict.Reset()

# This main function will setup the displayed items. This will depend if the user is currently 
# logged in.
def MainMenu():
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1 = Locale.LocalString('Title'))

    if isAccountActivated() == True:
        dir.Append(Function(
            InputDirectoryItem(
                SearchMenu,
                Locale.LocalString('SearchTitle'),
                Locale.LocalString('SearchPrompt'), 
                thumb=R(ICON_SEARCH))))
        
        dir.Append(Function(
            DirectoryItem(
                FilmAndTVMenu,
                Locale.LocalString('Film%TVTitle'),
                thumb=R("icon-search.png"))))
        
        dir.Append(Function(
            DirectoryItem(
                MyListMenu,
                Locale.LocalString('MyListTitle'),
                thumb=R(ICON_USER))))
    else:
        
        request = lovefilm.LoveFilmRequest()
        reqToken = request.get_request_token()
        reqTokenKey = reqToken.key
        Dict['reqToken'] = reqToken

        activationMessage = str(Locale.LocalString('ActivateMessage'))
        activationMessage = activationMessage % reqTokenKey

        dir.Append(Function(
            InputDirectoryItem(
                ActivateAccount,
                Locale.LocalString('ActivateTitle'),
                Locale.LocalString('ActivatePrompt'),
                subtitle = Locale.LocalString('ActivateSubtitle'),
                summary = activationMessage,
                thumb = R(ICON_COMPUTER))))
                
        dir.Append(Function(
            DirectoryItem(
                FreeTrial,
                Locale.LocalString('FreeSignupTitle'), 
                thumb=R(ICON_COMPUTER))))
                
    dir.nocache = 1

    return dir

# This function will allow the user to sign up for a free trial of LoveFilm.
def FreeTrial(sender):
    url = "http://www.lovefilm.com/"
    webbrowser.open(url,new=1,autoraise=True)
    return MessageContainer(
       Locale.LocalString('FreeSignupMessageTitle'),
       Locale.LocalString('FreeSignupMessage')
    )
    pass

def ActivateAccount(sender, query = None):
    reqToken = Dict['reqToken']
    
    reqToken.set_verifier(query)
    
    request = lovefilm.LoveFilmRequest()
    accessToken = request.get_access_token(reqToken)
    setAccessToken(accessToken)
    pass

def SearchMenu(sender, query=None):
    
    # Obtain a query that accesses the user's search query.
    (url, params) = lovefilm.LoveFilmRequest().search_titles_query(term=query)
    
    # Process the query.
    dir = ProcessQuery(sender, url, params)
    dir.title2 = query
    return dir

def FilmAndTVMenu(sender):
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1="Film & TV")
    
    # Append an item for each of the supported hot lists. We use the infoLabel to indicate to the 
    # user that these items are hotlist instead of genres.
    dir.Append(Function(
    	DirectoryItem(
            HotListMenu,
            Locale.LocalString('NewReleasesTitle'),
            thumb = R(ICON),
            infoLabel = Locale.LocalString('HotlistInfoLobal')),
        hotlist='new_releases'))
    dir.Append(Function(
    	DirectoryItem(
            HotListMenu,
            Locale.LocalString('MostPopularTitle'),
            thumb = R(ICON),
            infoLabel = Locale.LocalString('HotlistInfoLobal')),
        hotlist='most_popular'))
    dir.Append(Function(
    	DirectoryItem(
            HotListMenu,
            Locale.LocalString('ComingSoonTitle'),
            thumb=R(ICON),
            infoLabel = Locale.LocalString('HotlistInfoLobal')),
        hotlist='coming_soon'))

    # There are numerous different genres supported. We therefore define a collection of the names
    # and then simply iterate over them, adding a new item for each one. We use the infoLabel to
    # indicate to the user that these are genres instead of hotlists.
    genres = [
        Locale.LocalString('GenreActionAdventure'), Locale.LocalString('GenreAnimated'),
        Locale.LocalString('GenreAnime'), Locale.LocalString('GenreAudioDescriptive'), 
        Locale.LocalString('GenreBollywood'), Locale.LocalString('GenreChildren'),
        Locale.LocalString('GenreComedy'), Locale.LocalString('GenreDocumentary'),
        Locale.LocalString('GenreDrama'), Locale.LocalString('GenreFamily'),
        Locale.LocalString('GenreGayLesbian'), Locale.LocalString('GenreHorror'),
        Locale.LocalString('GenreMusicMusical'), Locale.LocalString('GenreRomance'),
        Locale.LocalString('GenreSciFiFantasy'), Locale.LocalString('GenreSpecialInterest'),
        Locale.LocalString('GenreSport'), Locale.LocalString('GenreTeen'),
        Locale.LocalString('GenreTelevision'), Locale.LocalString('GenreThriller'),
        Locale.LocalString('GenreWorldCinema') ]
    for i in genres:
        dir.Append(Function(
            DirectoryItem(
                GenreListMenu,
                i,
                thumb=R(ICON),
                infoLabel=Locale.LocalString('GenresInfoLabel')),
            genre=i))

    return dir

def HotListMenu(sender, hotlist=''):
    
    # Obtain a query that accesses the requested hot list.
    (url, params) = lovefilm.LoveFilmRequest().search_titles_query()
    params['f'] = "hotlist|" + hotlist
    
    # Process the query.
    dir = ProcessQuery(sender, url, params)
    dir.title2 = sender.itemTitle
    return dir

def GenreListMenu(sender, genre=''):
    (url, params) = lovefilm.LoveFilmRequest().search_titles_query()
    params['genre'] = genre
    
    dir = ProcessQuery(sender, url, params)
    dir.title2=sender.itemTitle
    return dir

def MyListMenu(sender):
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1)
    dir.noCache = True
    
    # Get the user's id. This is a Guid and is required when querying for user specific information.
    userGuid = getUser()
    
    # Obtain the list of titles which have been previously rented.
    (query, params)  = lovefilm.LoveFilmRequest().user_titles_query(
        userGuid,
        "rented")
    rented_query = lovefilm.LoveFilmRequest().make_query(
        getAccessToken(), 
        query,
        params=params,
        expand=False)
    rented_str = HTTP.Request(rented_query)
    rented = XML.ElementFromString(rented_str)
    
    no_rented = ""
    rented_elements = rented.xpath("//rented/total_results/text()")
    if (len(rented_elements) > 0):
        no_rented = rented_elements[0]
    
    # Obtain the list of titles which the user has previously rated.
    (query, params)  = lovefilm.LoveFilmRequest().user_titles_query(
        userGuid,
        "ratings/title")
    rated_query = lovefilm.LoveFilmRequest().make_query(
        getAccessToken(), 
        query,
        params=params,
        expand=False)
    rated_str = HTTP.Request(rated_query)
    rated = XML.ElementFromString(rated_str)
    
    no_rated = "0"
    rated_elements = rated.xpath("//ratings/total_results/text()")
    if (len(rated_elements) > 0):
        no_rated = rated_elements[0]
    
    dir.Append(Function(
    	DirectoryItem(
            UserListMenu,
            Locale.LocalString('TitlesAtHomeTitle'),
            thumb=R(ICON)),
        user=userGuid,
        listname="at_home"))
    
    for queue_name, id in getUserQueueNames():
    
        noTitles = numberOfTitlesInQueue(queue_name)
        dir.Append(Function(
            DirectoryItem(
                UserListMenu,
                "%s (%s)" % (queue_name, noTitles),
                thumb=R(ICON)),
            user=userGuid,
            listname="queues/" + id))
    
    rented_title_title = Locale.LocalString('RentedTitlesTitle')
    dir.Append(Function(
    	DirectoryItem(
            UserListMenu,
            "%s (%s)" % (rented_title_title, no_rented),
            thumb=R(ICON)),
        user=userGuid,
        listname="rented"))
    
    rated_title_title = Locale.LocalString('RatedTitlesTitle')
    dir.Append(Function(
    	DirectoryItem(
            UserListMenu,
            "%s (%s)" % (rated_title_title, no_rated),
            thumb=R(ICON)),
        user=userGuid,
        listname="ratings/title"))
    
    return dir

def UserListMenu(sender, user='', listname=''):
    
    # Obtain a query that accesses the user's specific list.
    (url, params) = lovefilm.LoveFilmRequest().user_titles_query(user, listname)
    
    # Process the query.
    dir = ProcessQuery(sender, url, params)
    dir.title2=sender.itemTitle
    return dir

def ProcessQuery(sender, query, params, initialResults=None):
    dir = MediaContainer(disabledViewModes=["Coverflow"], title1=sender.title1, title2=sender.title2) 
    
    # Update the start_index associated with the query. If the previous call included a specific
    # start_index then we should increment it by maximum viewable results.
    start_index = 1
    max_results = MAX_SEARCH_RESULTS
    if params.has_key('start_index'):
        start_index = params['start_index'] + max_results
    
    # All containers, except from the first, should replace it's parent. Therefore, when the user
    # exits from a second, or third page, they are returned to the original container.
    if start_index != 1:
        dir.replaceParent = True
        
    # Assign the appropriate page to the query.
    params = lovefilm.LoveFilmRequest().set_page(params, start_index, max_results)
    
    # Make the query and obtain the results.
    query = lovefilm.LoveFilmRequest().make_query(
        getAccessToken(), 
        query,
        params=params)
    xmlstr = HTTP.Request(query)
    xml = XML.ElementFromString(xmlstr)

    # Find the number of total results.
    total_results = -1
    total_results_element = xml.xpath("//total_results/text()")
    if len(total_results_element) > 0:
        total_results = int(total_results_element[0])

    # Parse the Catalog elements returned by the search. This will translate the returned XML into
    # list of dictionaries. The dictionaries contain the useful information about each individual
    # title.
    items = []
    catalog_title_elements = xml.xpath(
        "//at_home/at_home_item | //rented/rented_item")
    catalog_item_elements = xml.xpath("//catalog_title")
    if len(catalog_title_elements) > 0:
        for i in catalog_title_elements:
            items.append(parseUserCatalogTitle(i))
    else:
        for i in catalog_item_elements:
            items.append(parseCatalogTitle(i))
        
    # If no search results were found, inform the user.
    if len(items) == 0:
        return MessageContainer(
            Locale.LocalString('SearchTitle'), 
            Locale.LocalString('ErrorNoTitles'))
 
    # Populate the MediaContainer with the found titles.
    dir = populateFromCatalog(items, dir)

    # It's possible for the query to return more items than we can display. If this occurs, we 
    # should add another option for them to move to the next set. This is recursive and will simply
    # call back to this function with an updated start_index.
    if start_index + MAX_SEARCH_RESULTS < total_results:
        next_string = Locale.LocalString('SearchNextTitles')
        dir.Append(Function(
            DirectoryItem(
        	    ProcessQuery,
        	    "%s %s" % (next_string, MAX_SEARCH_RESULTS),
        	    thumb=R(ICON)),
            query=query,
            params=params))

    # We do another sanity check to ensure that the populated MediaContainer actually contains
    # some elements. Otherwise, inform the user.
    if len(dir) == 0:
        return MessageContainer(sender.itemTitle, Locale.LocalString('ErrorNoTitlesAlternative'))
    return dir

def parseUserCatalogTitle(item):
    parsed = parseCatalogTitle(item)

    shipped_date = ''
    try:
        shipped_date_item = item.xpath(".//shipped/text()")
        if len(shipped_date_item) > 0:
            shipped_date = shipped_date_item[0]
    except:
        pass
    
    returned_date = ''
    try:
        returned_date_item = item.xpath(".//returned/text()")
        if len(returned_date_item) > 0:
            returned_date = returned_date_item[0]
    except:
        pass
        
    parsed['shipped_date'] = shipped_date
    parsed['returned_date'] = returned_date
    
    return parsed

def parseCatalogTitle(item):

    # Attempt to locate the id from the Element.
    try:
        id_link = item.xpath(".//id/text()")[0]
        parts = id_link.split('/')
        id = parts[len(parts) - 1]
    except:
        id = ''

    # Attempt to locate the title from the Element.
    title = ''
    try:
        title = item.xpath(".//title")[0].get('clean')
    except:
        pass

    # Attempt to locate the synopsis from the Element.
    try:
        synopsis = item.xpath('.//synopsis_text/text()')[0]
        synopsis = re.sub(r'<[^>]+>','',synopsis)
    except:
        synopsis = ''

    # Attempt to locate the runtime from the Element. We will convert this value (which is in 
    # minutes) into milliseconds.
    try:
        runtime = item.xpath('.//run_time/text()')[0]
        runtime = int(runtime) * 60 * 1000
    except:
        runtime = 0

    # Attempt to locate the production year from the Element.
    production_year = ''
    try:
        production_year = item.xpath('.//production_year/text()')[0]
    except:
        pass
    
    # Attempt to locate the release year from the Element.
    release_date = ''
    try:
        release_date = item.xpath('//release_date/text()')[0]
    except:
        pass
    
    # Attempt to locate the studio from the Element.
    studio = ''
    try:
        studio = item.xpath('.//studio/text()')[0]
    except:
        pass

    # Attempt to determine the various genre's from the Element. This will be a list of the names
    # of all the different associated genre's.
    genres = []
    try:
        genre_elements = item.xpath(
            ".//category[@scheme='http://openapi.lovefilm.com/categories/genres']")
        for genre in genre_elements:
            genres.append(genre.get('term'))
    except:
        pass

    # Attempt to locate the assoicate box art from the Element. There maybe a number of different
    # box arts available, therefore we must find the highest quality one available.
    BOX_ART_PREFS = [
        'large',
        'medium',
        'small',
        'tiny',
        'mini'
    ]
    box_art = R(ICON)
    try:
        # Locate the associated images.
        art_options = {}
        arts = item.xpath(".//artwork[@type='title']/image")
        
        # Iterate over the found images and construct a dictionary mapping the 'size' paramter
        # to the actual link. The 'size' parameter will match the terms used within BOX_ART_PREFS.
        for o in arts:
            art_options[ o.get('size') ] = o.get('href')
            
        # Iterate over the BOX_ART_PREFS (in order of quality) and once we have found the first one
        # we will stop. This will be the artwork used.
        for o in BOX_ART_PREFS:
            if o in art_options:
                box_art = art_options[o]
                break
    except Exception, e:
        pass

    hero_art = ''
    try:
        # Locate the associated images.
        art_options = {}
        arts = item.xpath(".//artwork[@type='hero']/image")

        # Iterate over the found images and construct a dictionary mapping the 'size' paramter
        # to the actual link. The 'size' parameter will match the terms used within BOX_ART_PREFS.
        for o in arts:
            art_options[ o.get('size') ] = o.get('href')
            
        # Iterate over the BOX_ART_PREFS (in order of quality) and once we have found the first one
        # we will stop. This will be the artwork used.
        for o in BOX_ART_PREFS:
            if o in art_options:
                hero_art = art_options[o]
                break
    except Exception, e:
        pass

    # Attempt to locate the assoicated user rating from the Element. The value provided to us by
    # LoveFilm is a scale from 0 - 5, however, Plex uses a scale from 0 - 10. We therefore must 
    # convert it to be useable.
    user_rating = float(0.0)
    try:
        user_rating = float(item.xpath(".//rating/text()")[0])
        user_rating = user_rating * 2
    except:
        pass
    
    # Attempt to locate the assoicated certification from the Element.
    certification = ''
    try:
        certification = item.xpath(
           ".//category[@scheme='http://openapi.lovefilm.com/categories/certificates/bbfc']"
        )[0].get('term')
    except:
        pass

    # Attempt to locate the media format from the Element.
    format = ''
    try:
        format = item.xpath(
            ".//category[@scheme='http://openapi.lovefilm.com/categories/format']")[0].get('term')
    except:
        pass

    # Attempt to determine if the title is available for rental from the Element
    can_rent = False
    try:
        can_rent_string = item.xpath(".//can_rent/text()")[0]
        can_rent = can_rent_string.lower() in ("true")
    except:
        pass

    parsed = {}
    parsed['title'] = title
    parsed['id'] = id
    parsed['synopsis'] = synopsis
    parsed['duration'] = runtime
    parsed['user_rating'] = user_rating
    parsed['certification'] = certification
    parsed['boxart'] = box_art
    parsed['hero_art'] = hero_art
    parsed['release_date'] = release_date
    parsed['production_year'] = production_year
    parsed['studio'] = studio
    parsed['genres'] = genres
    parsed['format'] = format
    parsed['can_rent'] = can_rent

    return parsed

def populateFromCatalog(titleList, dir):
    
    quickCache = {}
    if 'quickCache' in Dict:
        quickCache = Dict['quickCache']

    for t in titleList:

        details = ''
        if t['certification']:
            cert_string = Locale.LocalString('Certification')
            details = "%s %s\n" % (cert_string, t['certification'])
        if t['duration'] > 0:
            runtime_string = Locale.LocalString('Runtime')
            details = "%s%s %s\n" % (details, runtime_string, msToRuntime(t['duration']))
        if t['format']:
            format_string = Locale.LocalString('Format')
            details = "%s%s %s\n" % (details, format_string, t['format'])
            
        if t.has_key('shipped_date'):
            shipped_date_status = Locale.LocalString('ShippingDispatchingSoon')
            if t['shipped_date'] != '':
                shipped_date_status = t['shipped_date']
            
            shipped_string = Locale.LocalString('ShippingShipped')
            details = "%s\n%s %s\n" % (details, shipped_string, shipped_date_status)
        if t.has_key('returned_date'):
            returned_date_status = Locale.LocalString('AtHome')
            if t['returned_date'] != '':
                returned_date_status = t['returned_date']
            
            returned_string = Locale.LocalString('Returned')
            details = "%s%s %s\n" % (details, returned_string, returned_date_status)

        full_summary = "%s\n%s" % (details, t['synopsis'])
        t['summary'] = full_summary
        
        quickCache[t['id']] = t
        
        infoLabel = priorityInfoLabel(t)

        # Create a DirectoryItem for each title using the associated information.
        dirItem = Function(
            DirectoryItem(
                InstantMenu,
                t['title'],
                subtitle=t['production_year'],
                summary=full_summary,
                thumb=t['boxart'],
                art=t['hero_art'],
                duration=t['duration'],
                userRating = getRating(url = t['id'], defaultRating = t['user_rating']),
                infoLabel=infoLabel,
            ),
            url="%s" % t['id']
        )
        dir.Append(dirItem)

    Dict['quickCache'] = quickCache

    dir.nocache = 1
    return dir

def simpleInfoLabel(title_info):
    return title_info['format']

def priorityInfoLabel(title_info):
    title_id = title_info['id']
    
    if isQueued(title_id) == False:
        return simpleInfoLabel(title_info)
    
    user_queues = getUserQueues()
            
    (priority, queue_name, shipped_in_order, availability) = user_queues[title_id]
    return getStatus(priority, availability)
            
def msToRuntime(ms):

    # Validate the input
    if ms is None or ms <= 0:
        return None

    ret = []

    # Convert the given number of milliseconds into seconds, minutes and hours.
    sec = int(ms/1000) % 60
    min = int(ms/1000/60) % 60
    hr  = int(ms/1000/60/60)

    # Return a string containing the converted milliseconds into the runtime format, hrs:mins:secs.
    return "%02d:%02d:%02d" % (hr,min,sec)

def getUser():

    # If we already know the user, just access it
    userCache = None
    if 'userCache' in Dict:
        userCache = Dict['userCache']

    if userCache is not None:
        return userCache

    # Get the url associated with the user.
    url = lovefilm.LoveFilmRequest().getUser(getAccessToken())
    xmlstr = HTTP.Request(url)
    xml = XML.ElementFromString(xmlstr)
    
    # The XML response will be in the form of a href which includes the user's GUID as the last
    # section of the URI. We therefore can get this by splitting the response based upon the '/'
    # character and getting the last element.
    href = xml.xpath(".//link")[0].get('href')
    parts = href.split('/')
    userCache = parts[len(parts) - 1]
    
    # Store the current user
    Dict['userCache'] = userCache
    
    return userCache

def getUserQueueNames():
    
    userQueueNameCache = []
    if 'userQueueNameCache' in Dict:
        userQueueNameCache = Dict['userQueueNameCache']
    
    if len(userQueueNameCache) > 0:
        return userQueueNameCache

    userQueueNameCache = []

    # Get the url associated with the user's queues.
    (query, params)  = lovefilm.LoveFilmRequest().user_titles_query(
        getUser(),
        "queues")
    queue_query = lovefilm.LoveFilmRequest().make_query(
        getAccessToken(), 
        query,
        params=params)
    queue_str = HTTP.Request(queue_query)
    queue_element = XML.ElementFromString(queue_str)
    
    # Iterate over all the found queues and record their name and unique identifiers. This should
    # then be added to the userQueueCache so that we don't need to recompute it everytime. This
    # information is unlikely to change during the execution of the plugin, therefore there is no
    # issues with storing this.
    queues = queue_element.xpath(".//queue")
    for queue in queues:
        queue_name = queue.xpath(".//name/text()")[0]
        queue_link = queue.xpath(".//link")[0].get('href')
        parts = queue_link.split('/')
        queue_id = parts[len(parts) - 1]
        
        userQueueNameCache.append((queue_name, queue_id))
    
    # Store the list of the names of the user's queues
    Dict['userQueueNameCache'] = userQueueNameCache
    
    return userQueueNameCache
    
def getUserQueues(refresh=False):

    userQueueCache = None
    if 'userQueueCache' in Dict:
        userQueueCache = Dict['userQueueCache']
    
    if refresh == False:
        if userQueueCache is not None:
            return userQueueCache

    # Iterate over all the known user's queues.
    user = getUser()
    userQueueCache = {}
    for (queue_name, queue_id) in getUserQueueNames():
    
        # Get the url associated with the user's specific queues.
        (url, params) = lovefilm.LoveFilmRequest().user_titles_query(user, "queues/" + queue_id)
        
        # Query to determine all the items located within the queue
        query = lovefilm.LoveFilmRequest().make_query(
            getAccessToken(), 
            url,
            params=params)
        query_str = HTTP.Request(query)
        query_element = XML.ElementFromString(query_str)
        
        # Iterate over all the items within the queue and determine the status and additional 
        # information associated with them. This includes when they were shipped and their
        # current availability.
        queue_items = query_element.xpath("//queue_item")
        for queue_item in queue_items:
           title_id_text = queue_item.xpath(".//catalog_title/id/text()")[0]
           parts = title_id_text.split('/')
           title_id = parts[len(parts) - 1]
           
           # Obtain the priority of the title, 1 = High, 2 = Medium, 3 = Low
           priority = queue_item.xpath(".//priority/text()")[0]
           
           # Obtain whether the titles are shipped in order (such as collections)
           shipped_in_order = queue_item.xpath(".//shipped_in_order/text()")[0]
           
           # Obtain the title's current availability
           availability = queue_item.xpath(
               ".//category[@scheme='http://openapi.lovefilm.com/categories/availability']")[0].get(
               'term')
           
           userQueueCache[title_id] = (priority, queue_name, shipped_in_order, availability)
           
    # Store the user's queue
    Dict['userQueueCache'] = userQueueCache
    
    return userQueueCache

def numberOfTitlesInQueue(required_queue_name):
    noTitles = 0
    
    # Iterate over all the titles currently queued (in all queues)
    userQueueList = getUserQueues()
    for (priority, queue_name, shipped_in_order, availability) in userQueueList.values():
    
        # If we find a title within the required queue, increment the counter.
        if queue_name == required_queue_name:
            noTitles = noTitles + 1
    
    return noTitles

def getTitlesAtHome():

    titlesAtHomeCache = []
    if 'titlesAtHomeCache' in Dict:
        return Dict['titlesAtHomeCache']

    # Obtain a query that accesses the user's specific list.
    (url, params) = lovefilm.LoveFilmRequest().user_titles_query(
        getUser(), 
        'at_home')
        
    at_home_query = lovefilm.LoveFilmRequest().make_query(
        getAccessToken(), 
        url,
        params=params)
    at_home_str = HTTP.Request(at_home_query)
    at_home_element = XML.ElementFromString(at_home_str)

    titles = at_home_element.xpath("//at_home/at_home_item")
    for title in titles:
        full_title_id = title.xpath(".//catalog_title/id/text()")[0]
        
        parts = full_title_id.split('/')
        title_id = parts[len(parts) - 1]
        
        titlesAtHomeCache.append(title_id)

    Dict['titlesAtHomeCache'] = titlesAtHomeCache
    
    return titlesAtHomeCache

def isQueued(title_id):

    # Obtain a list of all the currently queues titles.
    user_queues = getUserQueues()
    queued_items = user_queues.keys()
    
    # If the queued titles contains the required one, notify the caller.
    if title_id in queued_items:
        return True

    return False

def isAtHome(title_id):

    # Obtain a list of all the titles currently at home. If the one
    # specified by the caller is contained, then the title is at
    # home.
    titles_at_home = getTitlesAtHome()
    if title_id in titles_at_home:
        return True
    
    return False

def isRated(title_id):
    if 'userRatedCache' in Dict:
        userRatedCache = Dict['userRatedCache']
        return userRatedCache.has_key(title_id)
    
    return False

def getRating(url, defaultRating, refresh=False):
    
    # If there user rating has already been computed, then we should simply access
    # instead of re-working it out.
    userRatedCache = None
    if 'userRatedCache' in Dict:
        userRatedCache = Dict['userRatedCache']
    
    if refresh == False:
        if userRatedCache is not None:
            if userRatedCache.has_key(url):
                user_rating = float(userRatedCache[url])
                return user_rating * 2
            else:
                return defaultRating
        else:
            userRatedCache = {}
    else:
        userRatedCache = {}

    # Get the url associated with the user's queues.
    (query, params)  = lovefilm.LoveFilmRequest().user_titles_query(
        getUser(),
        "ratings/title")
    
    ITEMS_PER_QUERY = 100
    params['start_index'] = 1
    params['items_per_page'] = ITEMS_PER_QUERY
    
    no_rated = None
    more_results_available = True
    while(more_results_available):
        
        rated_query = lovefilm.LoveFilmRequest().make_query(
            getAccessToken(), 
            query,
            params=params)
        rated_str = HTTP.Request(rated_query)
        rated_element = XML.ElementFromString(rated_str)
        
        # Determine the number of rated items that are known.
        if no_rated is None:
            no_rated = 0
            rated_elements = rated_element.xpath("//ratings/total_results/text()")
            if len(rated_elements) > 0:
                no_rated = float(rated_elements[0])
    
        # Iterate over all the rated items contained within the current query.
        rated = rated_element.xpath("//ratings/rating_item")
        for rated_item in rated:
            id_element = rated_item.xpath(".//id/text()")[0]
            parts = id_element.split('/')
            id = parts[len(parts) - 1]
        
            # Update the cache to contain the title's rating.
            rating = rated_item.xpath(".//rating/text()")[0]
            userRatedCache[id] = rating
        
        # Once we've processed all items contained within this query, we must
        # determine if we need to make another in order to get a complete list
        if params['start_index'] + ITEMS_PER_QUERY > no_rated:
            more_results_available = False
        else:
            params['start_index'] = params['start_index'] + ITEMS_PER_QUERY
    
    # Store the current user ratings
    Dict['userRatedCache'] = userRatedCache
    
    # Convert the LoveFilm rating (0-5) to a Plex rating (0-10)
    if userRatedCache.has_key(url):
        user_rating = float(userRatedCache[url])
        return user_rating * 2
    else:
        return defaultRating
    
def getStatus(priority, availability):

    status = ''
    if availability == "unavailable":
       reserved = Locale.LocalString('PriorityReserved')
       status = "%s/" % reserved
    if priority == "1":
        high = Locale.LocalString('PriorityHigh')
        status = "%s%s" % (status, high)
    elif priority == "2":
        medium = Locale.LocalString('PriorityMedium')
        status = "%s%s" % (status, medium)
    elif priority == "3":
        low = Locale.LocalString('PriorityLow')
        status = "%s%s" % (status, low)
    else:
        unknown = Locale.LocalString('PriorityUknown')
        status = "%s%s" % (status, unknown)
    
    return status

def removeTitle(url):

    # Obtain a query to delete a title from the user's queue
    user = getUser()
    item = "queues/item/" + url
    (query, params) = lovefilm.LoveFilmRequest().user_titles_query(user, item)

    # Make the query, we don't expect any results.
    query = lovefilm.LoveFilmRequest().make_query(
        getAccessToken(), 
        query,
        method='DELETE',
        params=params,
        returnURL=False)

    # Refresh the cached list of user queues.
    userQueueItems = getUserQueues(refresh = True)

def addTitle(url, queue_id = None):

    if queue_id is None:
        # We will use the first known queue to be the default to add the title too.
        queue_list = getUserQueueNames()
        (queue_name, queue_id) = queue_list[0]
    
    # Obtain a query to add a title from the user's queue
    user = getUser()
    item = "queues/" + queue_id
    (query, params) = lovefilm.LoveFilmRequest().user_titles_query(user, item)

    # Construct a full path for the POST parameters
    api_url = str(Locale.LocalString('API_URL'))
    fullPath = "%s/catalog/title/%s" % (api_url, url)

    params = {}
    params['title_refs'] = fullPath

    # Make the query, we don't expect any results.
    query = lovefilm.LoveFilmRequest().make_query(
        getAccessToken(), 
        query,
        method = 'POST',
        params = params,
        expand = False,
        returnURL = False)
    Log(query.read())

    # Refresh the cached list of user queues
    userQueueItems = getUserQueues(refresh = True)

def changePriority(url, priority):

    # Obtain a query to change the priority of a title
    user = getUser()
    item = "queues/item/" + url
    (query, params) = lovefilm.LoveFilmRequest().user_titles_query(user, item)
    
    # Translate the priority string to a numerical value
    priorityNo = 2
    if priority == "High":
        priorityNo = 1
    elif priority == "Low":
        priorityNo = 3
    
    params = {}
    params['priority'] = priorityNo

    # Make the query, we don't expect any results.
    query = lovefilm.LoveFilmRequest().make_query(
        getAccessToken(), 
        query,
        method='PUT',
        params=params,
        returnURL=False)

    # Refresh the cached list of user queues
    userQueueItems = getUserQueues(refresh = True)

def changeQueue(url, queue_name):

    # Attempt to find the corresponding queue id from the given name
    queue_id = None
    for (name, id) in getUserQueueNames():
        if name == queue_name:
            queue_id = id
            break

    # If we have found the appropriate queue, we should remove the current
    # title and add it to the new one
    if queue_id is not None:
        removeTitle(url)
        addTitle(url, queue_id = queue_id)
    
    pass

def changeRating(url, newRating):
    
    params = {}
    params['rating'] = newRating
    
    item = "ratings/title/%s" % url
    
    method = 'PUT'
    
    if isRated(url) == False:
        fullPath = "http://api.lovefilm.com/catalog/title/" + url
        params['title_ref'] = fullPath   
        
        item = "ratings/title"
        
        method = 'POST'
    
    # Obtain a query to add a title from the user's queue
    user = getUser()
    (query, unusedParams) = lovefilm.LoveFilmRequest().user_titles_query(user, item)

    # Make the query, we don't expect any results.
    query = lovefilm.LoveFilmRequest().make_query(
        getAccessToken(), 
        query,
        method = method,
        params = params,
        returnURL = False)
    Log(query.read())

    # Refresh the cached user rating
    newRating = getRating(url, newRating, refresh = True)

def getIMDBTitle(name, release_date):
    
    # Attempt to translate the title into a url page in IMDB. We use Google
    # to locate the appropriate main page. This will then contain a link to
    # the trailer that it can stream.
    search_string = String.Quote("%s (%d)" % (name, int(release_date)), usePlus=False)
    lookup_url = GOOGLE_LOOKUP % search_string
    lookup = JSON.ObjectFromURL(lookup_url)
    
    # If there is no valid response, we cannot progress...
    if lookup.has_key('responseData') == False:
        return None
    
    # If the response does not contain any results, we cannot progress...
    lookup_response = lookup['responseData']
    if lookup_response.has_key('results') == False:
        return None
    
    lookup_results = lookup_response['results']
    if len(lookup_results) == 0:
        return None
    
    # If the first result does not contain a url, we cannot progress...
    lookup_first_result = lookup_results[0]
    if lookup_first_result.has_key('unescapedUrl') == False:
        return None
    
    # Request the IMDB url that we've found
    imdb_url = lookup_first_result['unescapedUrl']
    imdb_page_str = HTTP.Request(imdb_url)
    imdb_page = HTML.ElementFromString(imdb_page_str)
	
	# Find the element which is used to provide a link to the title's trailer. If this
	# is not available, we cannot progress...
    items = imdb_page.xpath("//td[@id='overview-bottom']/a")
    if len(items) == 0:
        return None
    
    item = items[0]
    href = item.get('href')
    if href == None:
        return None
    
    # Attempt to extract the video id from the href.
    parts = href.split('/')
    id = parts[len(parts) - 2]
    
    return id

def InstantMenu(
    sender, 
    url = '', 
    priority = None, 
    queue_name = None, 
    rating = None,
    mode = None,
    replaceParent = False):

    if mode == "Modify":
        if priority is not None:
            changePriority(url, priority)
        
        if queue_name is not None:
            changeQueue(url, queue_name)
        
        if rating is not None:
            changeRating(url, rating)
    
    if mode == "Add":
        addTitle(url)
    
    if mode == "Delete":
        removeTitle(url)
        
    quickCache = Dict['quickCache']
    t = quickCache[url]

    dir = MediaContainer(
        title1 = Locale.LocalString('DetailsTitle'),
        title2 = t['title'],
        disabledViewModes=["MediaPreview", "WallStream", "Coverflow", "PanelStream"])
    dir.replaceParent = replaceParent

    subtitle = "%s (%s)" % (t['title'], t['production_year'])
    userRating = getRating(url = t['id'], defaultRating = t['user_rating'])

    dir.Append(Function(
        VideoItem(
            ShowTrailer,
            Locale.LocalString('Trailer'),
            subtitle=subtitle,
            summary=t['summary'],
            thumb=t['boxart'],
            art=t['hero_art'],
            rating=t['user_rating'],
            userRating=userRating
        ),
        url="%s" % t['id']
    ))
    
    queued = isQueued(t['id'])
    at_home = isAtHome(t['id'])
    can_rent = t['can_rent']
    
    if queued == False and at_home == False:
        if can_rent == True:
            dir.Append(Function(
                DirectoryItem(
                    InstantMenu,
                    Locale.LocalString('RentTitle'),
                    subtitle=subtitle,
                    summary=t['summary'],
                    thumb=t['boxart'],
                    art=t['hero_art'],
                    duration=t['duration'],
                    userRating=userRating
                ),
                url="%s" % t['id'],
                mode="Add",
                replaceParent=True
            ))
    elif at_home == False:
        userQueueItems = getUserQueues()
        (priority, queue_name, shipped_in_order, availability) = userQueueItems[url]
    
        dir.Append(Function(
            PopupDirectoryItem(
                RentPriorityMenu,
                Locale.LocalString('Priority'),
                subtitle=subtitle,
                summary=t['summary'],
                thumb=t['boxart'],
                art=t['hero_art'],
                duration=t['duration'],
                userRating=userRating,
                infoLabel = getStatus(priority, availability)
            ),
            url="%s" % t['id']
        ))
        
        queue_list = getUserQueueNames()
        
        dir.Append(Function(
            PopupDirectoryItem(
                QueueMenu,
                Locale.LocalString('Queue'),
                subtitle=subtitle,
                summary=t['summary'],
                thumb=t['boxart'],
                art=t['hero_art'],
                duration=t['duration'],
                userRating=userRating,
                infoLabel = queue_name
            ),
            url="%s" % t['id'],
            queue_list = queue_list
        ))
        
        dir.Append(Function(
            DirectoryItem(
                InstantMenu,
                Locale.LocalString('RemoveTitle'),
                subtitle=subtitle,
                summary=t['summary'],
                thumb=t['boxart'],
                art=t['hero_art'],
                duration=t['duration'],
                userRating=userRating
            ),
            url="%s" % t['id'],
            mode="Delete",
            replaceParent=True
        ))
    
    dir.Append(Function(
        PopupDirectoryItem(
            RatingMenu,
            Locale.LocalString('RateTitle'),
            subtitle=subtitle,
            summary=t['summary'],
            thumb=t['boxart'],
            art=t['hero_art'],
            duration=t['duration'],
            userRating=userRating
        ),
        url="%s" % t['id']
    ))
    
    # Doesn't seem to be working. LoveFilm has confirmed that it's probably an issue
    # with permissions associated with the API key. However, until they fix this, I
    # wont be able to implement reviews. Maybe a future version...
    dir.Append(Function(
        DirectoryItem(
            ReviewMenu,
            "Reviews",
            subtitle=subtitle,
            summary=t['summary'],
            thumb=t['boxart'],
            art=t['hero_art'],
            duration=t['duration'],
            userRating=userRating
        ),
        url="%s" % t['id']
    ))
    
    dir.noCache = True
    return dir

def ShowTrailer(sender, url=''):

    quickCache = Dict['quickCache']
    title = quickCache[url]
    title_name = title['title']
    title_year = title['production_year']
    imdb_title = getIMDBTitle(title_name, title_year)
    
    if imdb_title is None:
        return MessageContainer(
            "No trailer available", 
            "The appropriate trailer could not be found.")
    
    details_url = IMDB_DETAILS_PAGE % imdb_title
    details = HTTP.Request(details_url).content
    index = details.find('mp4_h264')
    start = details.find('http', index)
    end = details.find("'", start)
    videoUrl = details[start:end]
    return Redirect(videoUrl)

def RentPriorityMenu(sender, url=''):
    dir = MediaContainer(title1="Priority",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
    
    dir.Append(Function(
        DirectoryItem(
            InstantMenu,
            Locale.LocalString('PriorityHigh')),
        priority='High',
        url=url,
        mode = "Modify",
        replaceParent=True))
    dir.Append(Function(
        DirectoryItem(
            InstantMenu,
            Locale.LocalString('PriorityMedium')),
        priority='Medium',
        url=url,
        mode = "Modify",
        replaceParent=True))
    dir.Append(Function(
        DirectoryItem(
            InstantMenu,
            Locale.LocalString('PriorityLow')),
        priority='Low',
        url=url,
        mode = "Modify",
        replaceParent=True))
    
    return dir

def QueueMenu(sender, url = '', queue_list = []):
    dir = MediaContainer(title1="Queue",title2=sender.itemTitle,disabledViewModes=["Coverflow"])
    
    # Iterate over all the know queues and add a DirectoryItem for each one. The user can select one
    # of these and it will call back to the InstantMenu and update the associated user queue.
    for (queue_name, queue_id) in queue_list:
        dir.Append(Function(
            DirectoryItem(
                InstantMenu,
                queue_name),
            queue_name=queue_name,
            url=url,
            mode = "Modify",
            replaceParent=True))
    
    return dir

def RatingMenu(sender, url=''):
    dir = MediaContainer(
        title1 = Locale.LocalString('Queue'),
        title2 = sender.itemTitle,
        disabledViewModes = ["Coverflow"])
    
    # Iterate over all the possible ratings and add a DirectoryItem for each one. The user can 
    # select one of these and it will call back to the InstantMenu and update the associated user 
    # query.
    ratings = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5] 
    for rating in ratings:
        dir.Append(Function(
            DirectoryItem(
                InstantMenu,
                str(rating)),
            url = url,
            rating = rating,
            mode = "Modify",
            replaceParent = True))
    
    return dir
    
def ReviewMenu(sender, url=''):
    dir = MediaContainer(title1="Reviews",title2=sender.itemTitle,disabledViewModes=["Coverflow"])

    quickCache = Dict['quickCache']
    t = quickCache[url]

    (url, params) = lovefilm.LoveFilmRequest().title_query(title=url, type='reviews')
    params['view'] = 'helpful'
    params['items_per_page'] = 25
    
    query = lovefilm.LoveFilmRequest().make_query(
        getAccessToken(), 
        url,
        params=params)
    xmlstr = HTTP.Request(query)
    xml = XML.ElementFromString(xmlstr)
    
    catalog_review_elements = xml.xpath("//reviews/review")
    if len(catalog_review_elements) == 0:
        return MessageContainer(sender.itemTitle, Locale.LocalString('ErrorNoTitlesAlternative')) 

    for review in catalog_review_elements:

        review_title = ''
        try:
            review_title = review.xpath(".//review_title/text()")[0]
        except:
            pass

        review_date = ''
        try:
            review_date_string = review.xpath(".//created/text()")[0]
            time_format = "%Y-%m-%dT%H:%M:%SZ"
            dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(review_date_string, time_format)))
            review_date = dt.strftime("%A, %d. %B %Y")
        except:
            pass

        review_text = ''
        try:
            review_text = review.xpath(".//review_text/text()")[0]
        except:
            pass
        
        review_rating = 0
        try:
           review_rating_text = review.xpath(".//rating/text()")[0]
           review_rating = float(review_rating_text) * 2
        except:
            pass
        
        dir.Append(Function(
                DirectoryItem(
                DoNothing,
                review_title,
                subtitle = review_date,
                summary = review_text,
                thumb = t['boxart'],
                art = t['hero_art'],
                userRating = review_rating
            )))

    return dir

def DoNothing(sender):
    pass

def getAccessToken():
    tok = Data.LoadObject(TOKEN_KEY)
    if tok != None:
        tok.app_name = 'Plex'
    return tok

def setAccessToken(tokObj):
    if tokObj == None:
        Data.Remove(TOKEN_KEY)
    else:
        Data.SaveObject(TOKEN_KEY, tokObj)

def isAccountActivated():

    # If there is no stored access token, the account is not activated.
    token = getAccessToken()
    if token is None:
        return False

    # Test the token
    response = lovefilm.LoveFilmRequest().make_query(
        access_token = token,
        query = '/user',
        method = "GET", 
        returnURL=False)
    if response.status == 401:
        Log('isAccountActivated - access token was found to be revoked: 401')
        setAccessToken(tokObj=None)
        return False
    
    # The account is activated
    return True