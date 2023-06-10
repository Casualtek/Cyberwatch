#!/usr/bin/python3
import feedparser
import requests
import json
import base64
import functools
import re
import deepl
import hashlib
import os
from datetime import datetime, timedelta
from feedgen.feed import FeedGenerator

# Constants
CUTOFF_DATE     = datetime.now() - timedelta(days=28)

def main():
    entries = []
    unique_ids = set()

    fg = FeedGenerator()
    fg.id('https://raw.githubusercontent.com/Casualtek/Cyberwatch/main/cyberattacks_news.xml')
    fg.title('Cyberattacks News')
    fg.author( {'name':'Valéry Marchive','email':'valery@ynside.net'} )
    fg.language('en')
    fg.link( href='https://www.lemagit.fr', rel='self')
    fg.description('Aggregated and Translated Cyberattacks News Feed')

    existing_entries = feedparser.parse('./cyberattacks_news.xml')
#    for entry in existing_entries.entries:
#        entries += entry

    entries = [item for item in existing_entries.entries if datetime.strptime(f'{item.published_parsed[0]}-{item.published_parsed[1]}-{item.published_parsed[2]}', '%Y-%m-%d') > CUTOFF_DATE]

    for entry in entries:
        title = entry.title
        link  = entry.id
        date  = entry.published

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link( href=f'{link}', rel='self')
        fe.pubDate(date)

    # Save the output to a file
    fg.rss_str(pretty=True)
    fg.rss_file('./cyberattacks_news.xml')

if __name__ == '__main__':
    main()

