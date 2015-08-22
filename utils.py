import sys
import re
import traceback
import functools

class Local(Exception):
    pass
class BadToken(Exception):
    pass

   
_regexps = {
'hash': re.compile('[0-9a-f]{32}'),
'pixiv_old':  re.compile('/(\d+)\.(jpg|png|gif)'),
'username': re.compile('https?://[\w\.]+/\w+'),
}

def raise_parse(re_code, url, pos=0):
    match = _regexps[re_code].search(url)
    if match:
        return match.group(pos)
    else:
        raise Local('Wrong URL.')
    

def last_param(link):
    return link.split('=').pop()
    
def _optional_format(pattern, kw):
    out = []
    for string in pattern.split('\n'):
        try:
            x = string.format(**kw)
        except KeyError:
            continue
        out.append(x)
    return '\n' + '\n'.join(out)
     
_print_info = """Artist tag: {tag}
Artist pixiv id: {id}
Artist pixiv login: {account}"""
info_format = functools.partial(_optional_format, _print_info)

def _custom(*data):
    with open('last_traceback.txt', 'w') as f:
        traceback.print_exception(*data, file=f)
        traceback.print_exception(*data)
    print 'Exception occured. Shutting down.'
    
sys.excepthook = _custom

