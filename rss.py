#!/usr/bin/python3
import feedparser
import requests
import json
import base64
import functools
import re
import deepl
import hashlib
import openai
import os
import time
import uuid
from feedgen.feed import FeedGenerator
from datetime import datetime

# Constants
openai.api_key = os.environ['OPENAI_API_KEY']
gpt_model      = 'gpt-4o'
ATRANS_API_KEY = os.environ['ATRANS_API_KEY']
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
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+q=%E3%82%B5%E3%82%A4%E3%83%90%E3%83%BC%E6%94%BB%E6%92%83&scoring=n&gl=JP&hl=ja&ceid=JP:ja',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+%E7%BD%91%E7%BB%9C%E6%94%BB%E5%87%BB&scoring=n&hl=zh-CN&gl=CN&ceid=CN:zh-Hans',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+%E7%BD%91%E7%BB%9C%E6%94%BB%E5%87%BB&scoring=n&hl=zh-TW&gl=TW&ceid=TW:zh-Hant',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+%E7%BD%91%E7%BB%9C%E6%94%BB%E5%87%BB&scoring=n&hl=zh-HK&gl=HK&ceid=HK:zh-Hant'
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
    'PRWire',
    'ESET',
    'TechTargetジャパン',
    'TEISS',
    'Smartphone Magazine',
]

def atranslate(text):
    endpoint = "https://api.cognitive.microsofttranslator.com"
    location = "centralus"
    path = "/translate"
    constructed_url = endpoint + path
    params = {
        "api-version" : "3.0",
        "from" : "",
        "to" : "en"
    }

    headers = {
        "Ocp-Apim-Subscription-Key": ATRANS_API_KEY,
        # location required if you're using a multi-service or regional (not global) resource.
        "Ocp-Apim-Subscription-Region": location,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4())
    }

    # You can pass more than one object in body.
    body = [{
        "text": text
    }]

    request    = requests.post(constructed_url, params=params, headers=headers, json=body)
    response   = request.json()
    result     = response[0]["translations"][0]["text"]
    print(text)
    print(result)
    return result

def decode_google_news_url(url):
    print(url)
    match = _ENCODED_URL_RE.match(url)
    encoded_text = match.groupdict()['encoded_url']  # type: ignore
    encoded_text += '==='  # Fix incorrect padding. Ref: https://stackoverflow.com/a/49459036/
    decoded_text = base64.urlsafe_b64decode(encoded_text)

    match = _DECODED_URL_RE.match(decoded_text)
    primary_url = match.groupdict()['primary_url']  # type: ignore
    primary_url = primary_url.decode()
    return primary_url

def get_item_hash(item):
    return hashlib.md5(item.encode('utf-8')).hexdigest()

def is_item_seen(item_hash):
    try:
        with open(SEEN_ITEMS_FILE, 'r') as file:
            return item_hash in file.read()
    except FileNotFoundError:
        return False

def mark_item_seen(item_hash):
    with open(SEEN_ITEMS_FILE, 'a') as file:
        file.write(item_hash + '\n')

def ask_chatgpt(news_title):
    today  = datetime.now()
    messages = [
        {'role': 'system', 'content': 'Tu es un journaliste technique, spécialisé dans l\'informatique professionnelle, et en particulier la cybersécurité. L’une de tes missions consiste à produire une revue de presse des cyberattaques rapportées à travers le monde, dans les médias. Tu dois évaluer des titres d’articles et dire si, selon toi, le titre suggère que l’article parle vraisemblement d’une véritable cyberattaque (qu’elle soit avérée ou soupçonnée) ou pas, et surtout pas une statistique, un produit, ni une étude de marché. Pour chaque titre évalué, tu ne peux répondre que par “likely”, “unlikely”, “no”. Date d’aujourd’hui: '+today.strftime('%Y-%m-%d')+'.'},
        {'role': 'user', 'content': news_title}
    ]

    completion = openai.chat.completions.create(
        model=gpt_model,
        messages=messages,
        max_tokens=5,
        n=1,
        temperature=0.1,
    )
    time.sleep(2)
    assessment = completion.choices[0].message.content
    
    return assessment

def extract_title(input_string):
    index_dash = input_string.find(" - ")
    index_pipe = input_string.find(" | ")

    if index_dash != -1 and (index_pipe == -1 or index_dash < index_pipe):
        delimiter = " - "
        index = index_dash
    elif index_pipe != -1:
        delimiter = " | "
        index = index_pipe
    else:
        index = -1

    if index != -1:
        result = input_string[:index]
    else:
        result = input_string
    return(result)

def main():
    entries = []
    unique_ids = set()

    fg = FeedGenerator()
    fg.id('https://raw.githubusercontent.com/Casualtek/Cyberwatch/main/cyberattacks_news.xml')
    fg.title('Cyberattacks News')
    fg.author( {'name':'Valéry Marchive','email':'valery@casualtek.com'} )
    fg.language('en')
    fg.link( href='https://www.lemagit.fr', rel='self')
    fg.description('Aggregated and Translated Likely Cyberattacks News Feed')

    fgnot = FeedGenerator()
    fgnot.id('https://raw.githubusercontent.com/Casualtek/Cyberwatch/main/unlikely_cyberattacks_news.xml')
    fgnot.title('Cyberattacks News (low likeliness)')
    fgnot.author( {'name':'Valéry Marchive','email':'valery@casualtek.com'} )
    fgnot.language('en')
    fgnot.link( href='https://www.lemagit.fr', rel='self')
    fgnot.description('Aggregated and Translated Unlikely Cyberattacks News Feed')

    print('Getting existing entries (likely).')
    existing_entries = feedparser.parse('./cyberattacks_news.xml')
    for entry in existing_entries.entries:
        fe = fg.add_entry()
        fe.id(entry.id)
        fe.title(entry.title)
        fe.link( href=f'{entry.id}', rel='self')
        fe.pubDate(entry.published)

    print('Getting existing entries (unlikely).')
    existing_entries = feedparser.parse('./unlikely_cyberattacks_news.xml')
    for entry in existing_entries.entries:
        fe = fgnot.add_entry()
        fe.id(entry.id)
        fe.title(entry.title)
        fe.link( href=f'{entry.id}', rel='self')
        fe.pubDate(entry.published)

    print('Getting English entries.')
    for rss_feed_url in rss_feed_urls_en:
        feed = feedparser.parse(rss_feed_url)
        entries += feed.entries

    for entry in entries:
        source    = entry.source['title']
        realTitle = extract_title(entry.title)
        item_hash = get_item_hash(realTitle)

        if (is_item_seen(item_hash) or (source in ignored_sources)):
            continue
        mark_item_seen(item_hash)

        link  = decode_google_news_url(entry.link)
        date  = entry.published

        assessment = ask_chatgpt(realTitle)
        assessment = assessment.lower()

        if assessment == 'likely':
            title = atranslate(realTitle)
            link  = decode_google_news_url(entry.link)
            date  = entry.published

            fe = fg.add_entry()
            fe.id(link)
            fe.title(str(title))
            fe.link( href=f'{link}', rel='self')
            fe.pubDate(date)
        else:
            title = atranslate(realTitle)
            link  = decode_google_news_url(entry.link)
            date  = entry.published

            fe = fgnot.add_entry()
            fe.id(link)
            fe.title(str(title))
            fe.link( href=f'{link}', rel='self')
            fe.pubDate(date)

    print('Getting non-English entries.')
    for rss_feed_url in rss_feed_urls_others:
        feed = feedparser.parse(rss_feed_url)
        entries += feed.entries

    for entry in entries:
        source    = entry.source['title']
        realTitle = extract_title(entry.title)
        item_hash = get_item_hash(realTitle)

        if (is_item_seen(item_hash) or (source in ignored_sources)):
            continue
        mark_item_seen(item_hash)
        
        assessment = ask_chatgpt(realTitle)
        assessment = assessment.lower()
#        print(f'{realTitle}: {assessment}')

        if assessment == 'likely':
            title = atranslate(realTitle)
            link  = decode_google_news_url(entry.link)
            date  = entry.published

            fe = fg.add_entry()
            fe.id(link)
            fe.title(str(title))
            fe.link( href=f'{link}', rel='self')
            fe.pubDate(date)
        else:
            title = atranslate(realTitle)
            link  = decode_google_news_url(entry.link)
            date  = entry.published

            fe = fgnot.add_entry()
            fe.id(link)
            fe.title(str(title))
            fe.link( href=f'{link}', rel='self')
            fe.pubDate(date)

    # Save the output to a file
    fg.rss_str(pretty=True)
    fg.rss_file('./cyberattacks_news.xml')
    fgnot.rss_str(pretty=True)
    fgnot.rss_file('./unlikely_cyberattacks_news.xml')

if __name__ == '__main__':
    main()
