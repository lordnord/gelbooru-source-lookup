Advanced user's tool for gelbooru.com. 
It looks up for artist tag and original pixiv tags.

to run it from binary (Windows)
 - register to pixiv.net (if you haven't already)
 - edit auth.json to put there your auth info
 - run main.exe

to run it from source
 - install python 2.7
 - install requests and pyperclip libraries
   "pip install requests, pyperclip"
 - register to pixiv.net (if you haven't already)
 - edit auth.json to put there your auth info
 - run main.py (if you use console run from it's directory)

JSON settings:

==| auth.json             |==

Pixiv login and password are required.
Saucenao API key already here but it allows only 100 requests 
for all users of this program. You can replace it with your own
key to have 100 requests just for you.

==| tag_replacements.json |==

Program uses danbooru wiki to find booru tag by original japanese tag.
But not all danbooru tags are acceptable on gelbooru

Examples:
{
"otoko_no_ko": "trap",               // replace 'otoko_no_ko' to 'trap'
"naked_randoseru": "nude randoseru", // replace one tag with two another
"car": "car vehicle",                // implication
"super_cool_tag": ""                 // delete inappropriate tag
}


==| gelbooru_only.json    |==

Some Pixiv artists have no wiki page on Danbooru.
They can be added to file with "save" and "save as" commands of manually (in that
case you should close program before edit) 
"pixiv id": "gelbooru_tag", // scheme

You can use pixiv account name or twitter username as tag if it looks good.
Also you can try to transliterate japanese artist name. (http://romaji.me)

==| proxy.json            |==

https is for pixiv
http is for saucenao and danbooru
To connect without proxy leave the file as is. Do not delete it.

example of use
{
"http": "",                         // danbooru and saucenao aren't proxified
"https": "https://159.8.54.34:3128" // pixiv is
}

Examples of valid links:

www.pixiv.net/member.php?id=206950
www.pixiv.net/member_illust.php?id=206950
www.pixiv.net/member_illust.php?mode=medium&illust_id=52832272
img20.pixiv.net/img/milligram/4567983.jpg
gelbooru.com//images/bb/95/bb956eee533a0ad755a9b1e941615092.png
gelbooru.com//samples/bb/95/sample_bb956eee533a0ad755a9b1e941615092.jpg?2869828
gelbooru.com/thumbnails/bb/95/thumbnail_bb956eee533a0ad755a9b1e941615092.jpg?2869828
twitter.com/riorua16/status/536876762878476288