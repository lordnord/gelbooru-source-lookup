import sys
import json

import requests as _requests
import requests
import pyperclip

from utils import *
import message

   
class GelbooruArtists(object):
    def __init__(self, fn):
        with open(fn) as f:
            self.artists = json.load(f)
            
    def add(self, id, tag):
        artist_exist = self.artists.get(str(id))
        if artist_exist:
            print 'You are trying to add an artist which is already in a database.'
            print id, ':', artist_exist
            return
        self.artists[str(id)] = tag
        self.save()
     
    def get(self, id):
        return self.artists.get(id)
        
    def __getitem__(self, id):
        return self.artists[id]
        
    def save(self):
        with open('gelbooru_only.json', 'w') as f:
            json.dump(self.artists, f, indent=0)
        print 'Saved.'
            
    def check(self):
        db = Danbooru()
        xcopy = self.artists.copy()
        for id, tag in self.artists.items():
            res = db.artist_search(Pixiv.member_url(id))
            if res:
                if tag == res[0]['name']:
                    msg = 'Tag "{}" for id={} was created on Danbooru.'
                    print msg.format(tag, id)
                else:
                    msg = 'Tag "{}" for id={} was created on Danbooru as "{}".'
                    print msg.format(tag, id, res[0]['name'])
                del self.artists[id]
        if self.artists == xcopy:
            print 'No changes in Danbooru db.'
        else:
            self.save()


class Pixiv:
    member_url = staticmethod('http://www.pixiv.net/member.php?id={}'.format)
    illust_url = staticmethod('http://www.pixiv.net/member_illust.php?mode=medium&illust_id={}'.format)
    
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
        self.access_token = r.json()['response']['access_token']
        
    @property
    def header(self):
        h = {
            'Referer': 'http://spapi.pixiv.net/',
            'User-Agent': 'PixivIOSApp/5.6.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer %s' % self.access_token,
        }
        return h
        
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
        r = requests.get(url, headers=self.header, params=params)
        return r.json()
       
    def user_info(self, author_id):
        url = 'https://public-api.secure.pixiv.net/v1/users/{}.json'.format(author_id)
        params = {
			'profile_image_sizes': 'px_170x170,px_50x50',
			'image_sizes': 'px_128x128,small,medium,large,px_480mw',
			'include_stats': 1,
			'include_profile': 1,
			'include_workspace': 1,
			'include_contacts': 1,
		}
        r = requests.get(url, headers=self.header, params=params)
        return r.json()
        
    def getmember(self, illust_id):
        data = self.illust(illust_id)
        try:
            illust = data['response'][0]
            user = illust['user']
        except KeyError:
            if data['errors']['system']['message'] == 'The access token provided is invalid.':
                raise BadToken
            else:
                raise Local('The image was deleted.')
                # todo
                # saucenao request
                
        self.last_image = illust
        user['tag'] = None
        return user
        
        
class Danbooru:    
    def artist_search(self, url):
        r = requests.get('http://danbooru.donmai.us/artists.json?search[name]=' + url)
        return r.json()
        
    def tag_translation(self, jtag):
        r = requests.get('http://danbooru.donmai.us/wiki_pages.json?search[other_names_match]=' + jtag)
        data = r.json()
        return data[0]['title'] if data else ''
        
    def artist_exist(self, artist):
        r = requests.get('http://danbooru.donmai.us/tags.json?search[category]=1&search[name_matches]=' + artist)
        return bool(r.json())
        
class App:
    def __init__(self):
        self.source = ''
        self.bad_id = False
        self.tags = ''
        self.translate_tags = False
        self.last_response = {}
        self.gelbooru_only = GelbooruArtists('gelbooru_only.json')
        with open('auth.json') as f:
            reg = json.load(f)
        self.pixiv = Pixiv(reg['pixiv_login'], reg['pixiv_password'])
        self.saucenao_api_key = reg['saucenao_api_key']
        with open("tag_replacements.json") as f:
            self.replacement_table = json.load(f).items()

        
    def translate(self):
        db = Danbooru()
        tags = {db.tag_translation(tag) for tag in self.pixiv.last_image['tags'] if tag}
        tagstring = ' '.join(tuple(tags))
        for pair in self.replacement_table:
            tagstring = tagstring.replace(*pair)
        if self.pixiv.last_image['is_manga']:
            count = self.pixiv.last_image['page_count']
            print 'Beware, these tags related to set of {} images.'.format(count)
        self.tags = tagstring
        print 'Tags:', tagstring
    
    def urlhandler(self, url):
        """
        Main routine.
        Parse URL and return tag for artist.

        Map of API calls.
        URL types: 
        
        PIXIV MEMBER
        www.pixiv.net/member.php?id=206950
        www.pixiv.net/member_illust.php?id=206950
        > danbooru > 
        
        PIXIV ILLUSTRATION
        www.pixiv.net/member_illust.php?mode=medium&illust_id=52832272
        (mode can be anything but link has to end with id)
        > pixiv > danbooru > 
        
        GELBOORU IMAGE 
        original gelbooru.com//images/bb/95/bb956eee533a0ad755a9b1e941615092.png
        resized gelbooru.com//samples/bb/95/sample_bb956eee533a0ad755a9b1e941615092.jpg?2869828
        preview gelbooru.com/thumbnails/bb/95/thumbnail_bb956eee533a0ad755a9b1e941615092.jpg?2869828
        > saucenao > danbooru > 
        
        TWITTER USERNAME
        https://twitter.com/riorua16/status/536876762878476288
        > danbooru >
        """
    
        artist_info = {}
    
        if 'gelbooru.com' in url:
            urlout = Pixiv.member_url(self.by_gelbooru_image(url))
        
        elif 'pixiv.net' in url:
            if 'illust_id' in url:
                x = raise_parse('illust', url, pos=1)
                artist_info = self.pixiv.getmember(x)
                if self.translate_tags: self.translate()
            elif 'img' in url:
                x = raise_parse('pixiv_old', url, pos=1)
                artist_info = self.pixiv.getmember(x)
                if self.translate_tags: self.translate()
            else:
                artist_info['id'] = last_param(url)
                
            info = self.pixiv.user_info(artist_info['id'])['response'][0]
            artist_info['account'] = info['account']
            twitter = info['profile']['contacts']['twitter']
            if twitter:
                artist_info['twitter'] = twitter
                
            
            urlout = Pixiv.member_url(artist_info['id'])
            
        elif 'twitter.com' in url or 'geocities.jp' in url:
            urlout = raise_parse('username', url)
        else:
            raise Local('Wrong URL.')
        
        artist = self.link2tag(urlout)
        # leading space need for fast ctrl+v in tag entry field
        if artist:
            outline = ' ' + artist
            if self.bad_id:
                outline += ' bad_id'
            pyperclip.copy(outline)
        self.bad_id = False
        
        artist_info['tag'] = artist
        self.last_response = artist_info
        return artist_info
        
    def by_gelbooru_image(self, link):
        """
        Get hash part of the link, send thumbnail to Saucenao,
        return Pixiv user id.
        """
        if not self.saucenao_api_key:
            raise Local('Saucenao API-key is not provided.')
        hash = raise_parse('hash', link)
        t = hash[0:2], hash[2:4], hash

        params = {
        'output_type': '2', # json response
        'api_key': self.saucenao_api_key,
        'url': 'http://gelbooru.com/thumbnails//{}/{}/thumbnail_{}.jpg'.format(*t),
        'dbmask': '96', # pixiv db 5 and 6, more info http://saucenao.com/status.html
        'numres': '1',  # only one result to keep program simple
        }

        r = requests.get('https://saucenao.com/search.php', params=params)
        try:
            response = r.json()['results'][0]
        except ValueError:
            raise Local(message.limit)
        except KeyError as err: # debug
            print err
            print r.json()
            raise Local('Oops. Unexpected saucenao error.')
            
        similar = response['header']['similarity']
        database = response['header']['index_id']
        illust_id = response['data']['pixiv_id']
        member_id = response['data']['member_id']
    
        if float(similar) < 75:
            raise Local('Low similarity: {}%'.format(similar))
    
        if database == 6: # Pixiv Historical db. But Saucenao isn't always knows about image status.
            print 'Image was deleted from pixiv.'
            self.bad_id = True
    
        self.source = Pixiv.illust_url(illust_id)
        print 'Link to image page:'
        print self.source
    
        return member_id


    def link2tag(self, url):
        """
        Look up for link in Danbooru artist pages.
        Return tag for artist.
        """
        if 'pixiv' in url:
            user = last_param(url)
        else:
            user = None

        x = self.gelbooru_only.get(user)
        if x:
            return x
        else:
            data = Danbooru().artist_search(url)
    
        if len(data) > 1:
            print 'Warning. {} artist tags on one url'.format(len(data))
            for artist in data:
                print artist['name']
        if user and not data:
            artist = None
        else:
            artist = data[0]['name']

        return artist


    def run(self):
        'Wrapper for catching exceptions'
        try:
            artist = self.urlhandler(pyperclip.paste())
        except Local as err:
            print err
        except BadToken:
            self.pixiv.login()
            print 'Pixiv re-auth completed.'
            self.run()
        except TypeError as err:
            print err # 
            raise
            print 'There is no text in clipboard.'
        except _requests.exceptions.ConnectionError as err:
            #print err # debug
            print 'Unable to connect.'
        else:
            print info_format(artist)

            
    def console(self):
        print 'Pixiv authorization...'
        self.pixiv.login()
        print message.at_start
        
        while True:
            # command branches
            print
            x = raw_input('>>> ')
            if x in ('exit', 'quit'):
                break
                
            elif x == '+':
                print 'Tag translation enabled.'
                self.translate_tags = True
                
            elif x == '-':
                print 'Tag translation disabled.'
                self.translate_tags = False
                
            elif x == 'check':
                self.gelbooru_only.check()
                
            elif 'help' in x:
                print message.help
                
            elif 'save as' in x:
                tag = x.replace('save as', '').strip()
                if self.last_response.get('id'):
                    self.gelbooru_only.add(self.last_response['id'], tag)
                else:
                    print 'Nothing to save.'

            elif 'save' in x:
                if self.last_response.get('id'):
                    self.gelbooru_only.add(self.last_response['id'], self.last_response['account'])
                else:
                    print 'Nothing to save.'
                    
            elif x == 't':
                pyperclip.copy(self.tags)
                print 'Last printed tags copied to clipboard.'
                
            elif x:
                pyperclip.copy(self.source)
                print 'Last printed link copied to clipboard.'
                
            else:
                self.run()

PROXY = True         
if __name__ == '__main__':
    if PROXY:
        with open('proxy.json') as f:
            requests = _requests.Session()
            requests.proxies = json.load(f)
    sys.excepthook = save_traceback
    App().console()
