

help = """
Copy source link to clipboard (don't paste it here, program will get it from clipboard itself).
Then press <Enter> and wait for result.
If artist tag will be found, it will be copied to clipboard.
Also you can copy link to image itself when source isn't provided.
In that case program looks up for source in Pixiv with Saucenao. 
But free Saucenao account allows only 100 requests per day.

Commands:
 Empty string             
(just press <Enter>)    : Main function. Get source link from clipboard and search for artist tag.
 Non-empty string 
(except commands below) : Copy last printed link to clipboard.
                         (useful for pasting source to Gelbooru source field)
 +    :  Turn on Pixiv tags translation by Danbooru wiki pages.
 -    :  Turn off tags translation. (default state)
 t    :  Copy last printed tags to clipboard.
 save :  Save artist id to local database under pixiv login as a tag.
         To choose different tag for id use command "save as put_tag_here"
 check:  Check tags in "gelbooru only" database.
 help :  Show this message.
 exit :  Leave the program.
"""

at_start = """
Copy source URL to clipboard or URL to image itself.
Then press <Enter> to fetch data.
Type help for more info.
"""

limit = """
Saucenao limit reached.
The limits refer to the number of searches possible for your account type. 
Currently the short period is 30 seconds, the long period is 24 hours.
Limits of periods for a free account are: 7 requests for short, 100 requests for long.
"""