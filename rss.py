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
from feedgen.feed import FeedGenerator

# Constants
DEEPL_API_KEY = os.environ['DEEPL_API_KEY']
SEEN_ITEMS_FILE = './seen_items.txt'

_ENCODED_URL_PREFIX = 'https://news.google.com/rss/articles/'
_ENCODED_URL_RE = re.compile(fr'^{re.escape(_ENCODED_URL_PREFIX)}(?P<encoded_url>[^?]+)')
_DECODED_URL_RE = re.compile(rb'^\x08\x13".+?(?P<primary_url>http[^\xd2]+)\xd2\x01')

# List of RSS feeds
rss_feed_urls_en = [
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+attack&scoring=n&hl=en-CA&gl=CA&ceid=CA:en',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+attack&scoring=n&hl=en-US&gl=US&ceid=US:en',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+attack&scoring=n&hl=en-IN&gl=IN&ceid=IN:en',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+attack&scoring=n&hl=en-AU&gl=AU&ceid=AU:en',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+attack&scoring=n&hl=en-GB&gl=GB&ceid=GB:en',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+attack&scoring=n&hl=en-NZ&gl=NZ&ceid=NZ:en',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+attack&scoring=n&hl=en-ZA&gl=ZA&ceid=ZA:en',
]

rss_feed_urls_others = [
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+attaque+informatique&scoring=n&hl=fr-FR&gl=FR&ceid=FR:fr',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+attaque&scoring=n&hl=fr-FR&gl=FR&ceid=FR:fr',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+attaque&scoring=n&hl=fr-BE&gl=BE&ceid=BE:fr',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+attaque&scoring=n&hl=fr-CH&gl=CH&ceid=CH:fr',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+angriff&scoring=n&hl=de-CH&gl=CH&ceid=CH:de',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+angriff&scoring=n&hl=de-DE&gl=DE&ceid=DE:de',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyber+angriff&scoring=n&hl=de-AT&gl=AT&ceid=AT:de',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+ataque+cibernetico&scoring=n&hl=es-ES&gl=ES&ceid=ES:es',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+ataque+cibernetico&scoring=n&hl=es-MX&gl=MX&ceid=MX:es',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+ataque+cibernetico&scoring=n&hl=es-CL&gl=CL&ceid=CL:es',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+ataque+cibernetico&scoring=n&hl=pt-PT&gl=PT&ceid=PR:pt',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+ataque+cibernetico&scoring=n&hl=pt-BR&gl=BR&ceid=BR:pt',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+attacco+informatico&scoring=n&hl=it&gl=IT&ceid=IT:it',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyberaanval&scoring=n&hl=nl&gl=NL&ceid=NL:nl',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyberangreb&scoring=n&hl=dk&gl=DK&ceid=DK:dk',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+verkkohy%C3%B6kk%C3%A4ys&scoring=n&hl=fi&gl=FI&ceid=FI:fi',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyberattack&scoring=n&hl=se&gl=SE&ceid=SE:se',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyberangrep&scoring=n&hl=no&gl=NO&ceid=NO:no'
    'https://news.google.com/rss/search?q=%E3%82%B5%E3%82%A4%E3%83%90%E3%83%BC%E6%94%BB%E6%92%83&gl=JP&hl=ja&ceid=JP:ja',
]

ignored_sources = [
    'GlobeNewswire',
    'PR Newswire UK',
    'PR Newswire Asia',
    'PR Newswire',
    'Business Wire',
    'openPR',
    'Canada NewsWire',
    'PR Web',
    'businesswire.com',
    'PR TIMES',
    'ESET',
    'TechTargetジャパン',
]

def decode_google_news_url(url):
    match = _ENCODED_URL_RE.match(url)
    encoded_text = match.groupdict()['encoded_url']  # type: ignore
    encoded_text += '==='  # Fix incorrect padding. Ref: https://stackoverflow.com/a/49459036/
    decoded_text = base64.urlsafe_b64decode(encoded_text)

    match = _DECODED_URL_RE.match(decoded_text)
    primary_url = match.groupdict()['primary_url']  # type: ignore
    primary_url = primary_url.decode()
    return primary_url

def translate_text(text):
    translator = deepl.Translator(DEEPL_API_KEY)
    result     = translator.translate_text(text , target_lang='EN-US')
    return result.text

def get_item_hash(item):
    return hashlib.md5(item.title.encode('utf-8')).hexdigest()

def is_item_seen(item_hash):
    try:
        with open(SEEN_ITEMS_FILE, 'r') as file:
            return item_hash in file.read()
    except FileNotFoundError:
        return False

def mark_item_seen(item_hash):
    with open(SEEN_ITEMS_FILE, 'a') as file:
        file.write(item_hash + '\n')

def main():
    entries = []
    unique_ids = set()

    fg = FeedGenerator()
    fg.id('./cyberattcks_news.xml')
    fg.title('Cyberattacks News')
    fg.author( {'name':'Valéry Marchive','email':'valery@ynside.net'} )
    fg.language('en')
    fg.link( href='https://www.lemagit.fr', rel='self')
    fg.description('Aggregated and Translated Cyberattacks News Feed')

    existing_entries = feedparser.parse('./cyberattacks_news.xml')
    for entry in existing_entries.entries:
        fe = fg.add_entry()
        fe.id(entry.id)
        fe.title(entry.title)
        fe.link( href=f'{entry.id}', rel='self')
        fe.pubDate(entry.published)

    for rss_feed_url in rss_feed_urls_en:
        feed = feedparser.parse(rss_feed_url)
        entries += feed.entries

    for entry in entries:
        source = entry.source['title']
        item_hash = get_item_hash(entry)

        if (is_item_seen(item_hash) or (source in ignored_sources)):
            continue
        mark_item_seen(item_hash)

        title = entry.title
        link  = decode_google_news_url(entry.link)
        date  = entry.published

        fe = fg.add_entry()
        fe.id(link)
        fe.title(title)
        fe.link( href=f'{link}', rel='self')
        fe.pubDate(date)

    for rss_feed_url in rss_feed_urls_others:
        feed = feedparser.parse(rss_feed_url)
        entries += feed.entries

    for entry in entries:
        source = entry.source['title']
        item_hash = get_item_hash(entry)

        if (is_item_seen(item_hash) or (source in ignored_sources)):
            continue
        mark_item_seen(item_hash)

        title = translate_text(entry.title)
        link  = decode_google_news_url(entry.link)
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
