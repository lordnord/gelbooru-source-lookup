import re
import json
import functools
# 3rd party
import requests
import pyperclip

hashmask = re.compile('[0-9a-f]{32}')
oldstyle = re.compile('/(\d+)\.(jpg|png|gif)')
fourthslash = re.compile('https?://[\w\.]+/\w+')

def raise_parse(regexp, url, pos=0):
    match = regexp.search(url)
    if match:
        return match.group(pos)
    else:
        raise Local('Wrong URL.')

with open('auth.json') as f:
    globals().update(json.load(f))
with open('gelbooru_only.json') as f:
    gelbooru_only = json.load(f)
def replacement_table():
    try:
        return replacement_table.cache
    except AttributeError:
        with open("tag_replacements.json") as f:
            table = json.load(f)
        replacement_table.cache = table.items()
        return table.items()
    
def last_param(link):
    return link.split('=').pop()
    
def optional_format(formatlist, kw):
    out = []
    for string in formatlist:
        try:
            x = string.format(**kw)
        except KeyError:
            continue
        out.append(x)
    return '\n' + '\n'.join(out)
     
_print_info = ('Artist tag: {tag}', 'Artist pixiv id: {id}', 'Artist pixiv login: {account}')
info_format = functools.partial(optional_format, _print_info)
        
class Local(Exception):
    pass
    
class BadToken(Exception):
    pass

class main:
    source = ''
    bad_id = False


class Pixiv:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.last_image = None
        
    def login(self):
        url = 'https://oauth.secure.pixiv.net/auth/token'
        headers = {
            'Referer': 'http://www.pixiv.net/',
        }
        data = {
            'username': self.username,
            'password': self.password,
            'grant_type': 'password',
            'client_id': 'bYGKuGVw91e0NMfPGp44euvGt59s',
            'client_secret': 'HP3RmkgAmEGro0gn1x9ioawQE8WMfvLXDz3ZqxpK',
        }

        r = requests.post(url, headers=headers, data=data)
        token = r.json()
        self.access_token = token['response']['access_token']
        raw_cookie = r.headers.get('Set-Cookie')
        for cookie_str in raw_cookie.split('; '):
            if 'PHPSESSID=' in cookie_str:
                self.session = cookie_str.split('=')[1]
        
    @property
    def req_header(self):
        header = {
            'Referer': 'http://spapi.pixiv.net/',
            'User-Agent': 'PixivIOSApp/5.6.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer %s' % self.access_token,
            'Cookie': 'PHPSESSID=%s' % self.session,
        }
        return header
        
    def illust(self, illust_id, extended=False):
        url = 'https://public-api.secure.pixiv.net/v1/works/{}.json'.format(illust_id)
        if extended:
            params = {
            'profile_image_sizes': 'px_170x170,px_50x50',
            'image_sizes': 'px_128x128,small,medium,large,px_480mw',
            'include_stats': 'true',
            }
        else:
            params = None
        r = requests.get(url, headers=self.req_header, params=params)
        return r.json()
        
    def illust2member(self, illust_id):
        data = self.illust(illust_id)
        
        try:
            illust = data['response'][0]
            user = illust['user']
        except KeyError:
            if data['errors']['system']['message'] == 'The access token provided is invalid.':
                raise BadToken
            else:
                raise Local('The image was deleted.')
                
        self.last_image = illust
        user[u'tag'] = None
        return user
        
        
class Danbooru:
    domain = 'http://danbooru.donmai.us/'
    
    def artist_search(self, url):
        r = requests.get(self.domain + 'artists.json?search[name]=' + url)
        return r.json()
        
    def tag_translation(self, jtag):
        r = requests.get(self.domain + 'wiki_pages.json?search[other_names_match]=' + jtag)
        data = r.json()
        return data[0]['title'] if data else ''
        
def translate():
    tags = {danbooru.tag_translation(tag) for tag in pixiv.last_image['tags'] if tag}
    tagstring = ' '.join(tuple(tags))
    for pair in replacement_table():
        tagstring = tagstring.replace(*pair)
    if pixiv.last_image['is_manga']:
        count = pixiv.last_image['page_count']
        print 'Beware, these tags related to set of {} images.'.format(count)
    print 'Tags:', tagstring
    
def urlhandler(url):
    """
    Main routine.
    Parses URL and returns tag for artist.

    Current map of API calls (may change in future):
    URL type /member.php?id=20736 or /member_illust.php?id=20736
    > danbooru > output
    
    URL type /member_illust.php?mode=medium&illust_id=48020617
    > pixiv > danbooru > output
    
    URL type simg4.gelbooru.com//images/93/db/93db57a3bcdc66f060f4d5d1fbe5a663.jpg?2521780
    (or it can be URL to sample or preview)
    > saucenao > danbooru > output
    
    URL type https://twitter.com/riorua16/status/536876762878476288
    > danbooru > output
    """
    
    PREFIX = 'http://www.pixiv.net/member.php?id='
    artist_info = dict()
    
    if 'gelbooru.com' in url:
        if not SAUCENAO_API_KEY:
            raise Local('Saucenao API-key is not provided.')
        hash = raise_parse(hashmask, url)
        t = hash[0:2], hash[2:4], hash
        thumb = 'http://gelbooru.com/thumbnails//{}/{}/thumbnail_{}.jpg'.format(*t)
        urlout = PREFIX + pic2member(thumb)
        
    elif 'pixiv.net' in url:
        if 'illust_id' in url:
            artist_info = pixiv.illust2member(last_param(url))
            if translate_tags: translate()
        elif 'img' in url:
            x = raise_parse(oldstyle, url, pos=1)
            artist_info = pixiv.illust2member(x)
            if translate_tags: translate()
        else:
            artist_info[u'id'] = last_param(url)
            
        urlout = PREFIX + str(artist_info['id'])
            
    elif 'twitter.com' in url or 'geocities.jp' in url:
        urlout = raise_parse(fourthslash, url)
    else:
        raise Local('Wrong URL.')
        
    artist_info[u'tag'] = link2tag(urlout)
    return artist_info

def pic2member(thumbnail_link):
    """
    Returns pixiv user id from gelbooru image link
    using saucenao api.
    """

    params = {
    'output_type': '2', # json response
    'api_key': SAUCENAO_API_KEY,
    'url': thumbnail_link,
    'dbmask': '96', # pixiv db 5 and 6, more info http://saucenao.com/status.html
    'numres': '1',
    }

    r = requests.get('https://saucenao.com/search.php', params=params)
    try:
        json_response = r.json()
    except ValueError:
        message = """
Saucenao limit reached.
The limits refer to the number of searches possible for your account type. 
Currently the short period  is 30 seconds, the long period is 24 hours.
Limits for a free account are: 7 per 30 sec, 100 per 24 hours.
        """
        raise Local(message)

    header = json_response['results'][0]['header']
    data = json_response['results'][0]['data']
    
    similar = float(header['similarity'])
    if similar < 75:
        raise Local('Low Similarity %.02f%%' % similar)
    
    database = header['index_id']
    if database == 6: # so called Pixiv Historical. But Saucenao isn't always knows about image status
        print 'Image was deleted from pixiv.'
        main.bad_id = True
    
    main.source = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + data['pixiv_id']
    print 'Link to image page:'
    print main.source
    
    return data['member_id']



def link2tag(url):
    """
    Looks up for link in Danbooru artist pages
    and returns tag for artist.
    """

    if 'pixiv' in url:
        user = last_param(url)
    else:
        user = None
        
    try:
        x = gelbooru_only[user]
        pyperclip.copy(' ' + x)
        return x
    except KeyError:
        data = danbooru.artist_search(url)
    
    if len(data) > 1:
        print 'Warning. {} artist tags on one url'.format(len(data))
        for artist in data:
            print artist['name'],
            print
    if user and not data:
        artist = None
    else:
        artist = data[0]['name']
        # leading space need for fast ctrl+v in tag entry field
        outline = ' ' + artist
        if main.bad_id:
            outline += ' bad_id'
        pyperclip.copy(outline)

    main.bad_id = False
    return artist

        
pixiv = Pixiv(PIXIV_LOGIN, PIXIV_PASSWORD)
danbooru = Danbooru()
translate_tags = False

helpmessage = """
Copy source link to clipboard (don't paste it here, program gets it from clipboard itself).
Then press Enter and wait for result.
If artist tag will be found, it will be copied to clipboard.
Also you can copy link to image itself when source isn't provided.
In that case program looks up for source in pixiv with Saucenao. 
Beware that free Saucenao accounts allow only 100 requests per day.

Commands:
Empty string (just press Enter): Main function. Get source link from clipboard and search for artist tag.
Not empty string (except commands below): Copy last printed link to clipboard.
        Do it when you want to paste source to gelbooru source field.
+:      Turn on pixiv tags translation by danbooru wiki pages.
        It's very helpful for uploading images.
-:      Turn off tags translation. 
        It's turned off by default.
help:   Show this message.
exit:   Leave the program.
"""

def run():
    try:
        artist = urlhandler(pyperclip.paste())
    except Local as err:
        print err
    except BadToken:
        pixiv.login()
        print 'Pixiv re-auth completed.'
        run()
    except TypeError as err:
        print err # debug
        print 'There is no text in clipboard.'
    except requests.exceptions.ConnectionError:
        print 'Unable to connect.'
    else:
        print info_format(artist)

        
if __name__ == '__main__':
    
    print 'Pixiv authorization...',
    pixiv.login()
    print ('\rCopy source URL to clipboard or url to image itself\n'
           'Then press Enter to fetch data.\n'
           'Type help for more info.')
    
    while True:
        x = raw_input('\n>>> ')
        if x in ('exit', 'quit'):
            break
        elif x == '+':
            print 'Tag translation enabled.'
            translate_tags = True
        elif x == '-':
            print 'Tag translation disabled.'
            translate_tags = False
        elif 'help' in x:
            print helpmessage
        elif x:
            pyperclip.copy(main.source)
            print 'Last printed link copied to clipboard.'
        else:
            run()

