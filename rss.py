#!/usr/bin/python3
import feedparser
import re
import hashlib
import os
import time
from feedgen.feed import FeedGenerator
from datetime import datetime
from openai import OpenAI
import json

# Constants
GROQ_MODEL = 'qwen/qwen3.6-27b'
GROQ_BASE_URL = 'https://api.groq.com/openai/v1'
# Stay comfortably under the 8000 TPM rate limit on the batch call.
TRIAGE_CHUNK_SIZE = 20
CHUNK_DELAY = 8  # seconds between chunked triage calls
SEEN_ITEMS_FILE = './seen_items.txt'

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
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+ataque+cibernetico&scoring=n&hl=pt-PT&gl=PT&ceid=PT:pt',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+ataque+cibernetico&scoring=n&hl=pt-BR&gl=BR&ceid=BR:pt',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+attacco+informatico&scoring=n&hl=it-IT&gl=IT&ceid=IT:it',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyberaanval&scoring=n&hl=nl-NL&gl=NL&ceid=NL:nl',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyberangreb&scoring=n&hl=da-DK&gl=DK&ceid=DK:da',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+verkkohy%C3%B6kk%C3%A4ys&scoring=n&hl=fi-FI&gl=FI&ceid=FI:fi',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyberattack&scoring=n&hl=sv-SE&gl=SE&ceid=SE:sv',
    'https://news.google.com/rss/search?tbm=nws&q=when:12h+cyberangrep&scoring=n&hl=no-NO&gl=NO&ceid=NO:no',
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

def triage_batch(client, titles):
    """Classify and deduplicate a list of titles in one LLM call.

    Returns a list the length of `titles` with values in
    {'first', 'likely', 'unlikely', 'no'}:
      - 'first'  : likely a real cyberattack AND first to report the event
      - 'likely' : likely a real cyberattack, but a same-event title already won
      - 'unlikely' / 'no' : not (or probably not) a real cyberattack
    Raises ValueError if the response cannot be parsed.
    """
    today  = datetime.now()
    system = ("Tu es un journaliste technique, spécialisé dans l'informatique professionnelle, et en particulier la cybersécurité. "
              "Ta mission consiste à produire une revue de presse des cyberattaques rapportées à travers le monde, dans les médias. "
              "On te fournit une liste numérotée de titres d'articles. Pour chaque titre, tu dois répondre "
              "\"first\", \"likely\", \"unlikely\" ou \"no\" : "
              "- \"no\" si le titre ne parle vraisemblablement pas d'une véritable cyberattaque (avérée ou soupçonnée) : "
              "statistique, produit, étude de marché, conseil, opinion, etc. "
              "- \"unlikely\" si ce pourrait être une cyberattaque mais que ce n'est pas probable. "
              "- \"likely\" si le titre parle vraisemblablement d'une véritable cyberattaque. "
              "Si plusieurs titres \"likely\" portent sur le même événement (même victime, même incident), "
              "seul le PREMIER titre de la liste concernant cet événement doit recevoir \"first\" ; "
              "les autres reçoivent \"likely\". "
              "Réponds uniquement avec un tableau JSON de chaînes, sans commentaire ni balisage, "
              "contenant exactement un verdict par titre, dans l'ordre. "
              "Date d'aujourd'hui : " + today.strftime('%Y-%m-%d') + ".")

    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(titles))
    response = client.responses.create(
        model=GROQ_MODEL,
        instructions=system,
        input=numbered,
        max_output_tokens=2000,
    )
    time.sleep(1)

    text = response.output_text.strip()
    valid = {'first', 'likely', 'unlikely', 'no'}

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Tolerate markdown fences or surrounding chatter.
        match = re.search(r'```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```', text, flags=re.DOTALL) or \
                re.search(r'(\[.*\]|\{.*\})', text, flags=re.DOTALL)
        if not match:
            # Maybe the model answered with the bare verdict, e.g. "likely".
            bare = text.strip().lower().strip('"\'`')
            if bare in ('first', 'likely', 'unlikely', 'no'):
                data = [bare]
            else:
                raise ValueError(f'no JSON in response: {text[:200]!r}')
        else:
            data = json.loads(match.group(1))

    if isinstance(data, str):
        data = [data]
    elif isinstance(data, dict):
        # Small models sometimes answer {"1": "first", "2": "no", ...}
        # instead of an array.
        try:
            data = [data[k] for k in sorted(data, key=lambda k: int(re.sub(r'\D', '', str(k))))]
        except Exception:
            data = list(data.values())

    if len(titles) == 1 and isinstance(data, list) and len(data) != 1:
        # Model gave a full batch-style answer to a single-title prompt.
        data = [data[0]]

    verdicts = []
    for v in data:
        if not isinstance(v, str):
            raise ValueError(f'unexpected verdict value: {v!r}')
        verdicts.append(v.strip().lower())

    if len(verdicts) != len(titles):
        raise ValueError(f'expected {len(titles)} verdicts, got {len(verdicts)}')
    return [v if v in valid else 'no' for v in verdicts]

def translate_title(client, title):
    system = ("Tu es un traducteur professionnel. Traduis le titre d'article suivant en anglais."
              "Réponds uniquement avec le titre traduit, sans guillemets ni commentaire.")

    response = client.responses.create(
        model=GROQ_MODEL,
        instructions=system,
        input=title,
        max_output_tokens=200,
    )
    time.sleep(1)
    return response.output_text.strip()

def extract_title(input_string):
    index_dash = input_string.find(" - ")
    index_pipe = input_string.find(" | ")

    if index_dash != -1 and (index_pipe == -1 or index_dash < index_pipe):
        index = index_dash
    elif index_pipe != -1:
        index = index_pipe
    else:
        index = -1

    if index != -1:
        result = input_string[:index]
    else:
        result = input_string
    return(result)

def add_feed_entry(fg, title, link, date):
    fe = fg.add_entry()
    fe.id(link)
    fe.title(str(title))
    fe.link( href=f'{link}', rel='self')
    fe.pubDate(date)

def process_entries(client, entries, fg):
    # Collect unseen, non-ignored items first so the LLM sees the full
    # list and can deduplicate same-event coverage across languages.
    pending = []
    for entry in entries:
        source    = entry.source['title']
        realTitle = extract_title(entry.title)
        item_hash = get_item_hash(realTitle)

        if (is_item_seen(item_hash) or (source in ignored_sources)):
            continue
        pending.append({'title': realTitle, 'hash': item_hash,
                        'link': entry.link, 'date': entry.published})

    if not pending:
        return

    titles = [p['title'] for p in pending]
    chunks = [titles[i:i + TRIAGE_CHUNK_SIZE] for i in range(0, len(titles), TRIAGE_CHUNK_SIZE)]
    try:
        verdicts = []
        for chunk in chunks:
            verdicts += triage_batch(client, chunk)
            if len(chunks) > 1:
                time.sleep(CHUNK_DELAY)
    except Exception as e:
        print(f'Batch triage failed, falling back to individual calls: {e}')
        verdicts = []
        for t in titles:
            try:
                verdicts.append(triage_batch(client, [t])[0])
            except Exception as e2:
                print(f'Error assessing "{t}": {e2}')
                verdicts.append(None)

    for item, verdict in zip(pending, verdicts):
        if verdict != 'first':
            # Not a real attack, or a duplicate of an earlier item.
            if verdict is not None:
                mark_item_seen(item['hash'])
            continue
        try:
            title = translate_title(client, item['title'])
            add_feed_entry(fg, title, item['link'], item['date'])
            mark_item_seen(item['hash'])
        except Exception as e:
            print(f'Error processing "{item["title"]}": {e}')

def main():
    client = OpenAI(
        api_key=os.environ.get('GROQ_API_KEY'),
        base_url=GROQ_BASE_URL,
    )

    fg = FeedGenerator()
    fg.id('https://raw.githubusercontent.com/Casualtek/Cyberwatch/main/cyberattacks_news.xml')
    fg.title('Cyberattacks News')
    fg.author( {'name':'Valéry Marchive','email':'valery@casualtek.com'} )
    fg.language('en')
    fg.link( href='https://www.lemagit.fr', rel='self')
    fg.description('Aggregated and Translated Likely Cyberattacks News Feed')

    print('Getting existing entries (likely).')
    existing_entries = feedparser.parse('./cyberattacks_news.xml')
    for entry in existing_entries.entries:
        fe = fg.add_entry()
        fe.id(entry.id)
        fe.title(entry.title)
        fe.link( href=f'{entry.id}', rel='self')
        fe.pubDate(entry.published)

    print('Getting entries.')
    entries = []
    for rss_feed_url in rss_feed_urls_en + rss_feed_urls_others:
        feed = feedparser.parse(rss_feed_url)
        entries += feed.entries
    process_entries(client, entries, fg)

    # Save the output to a file
    fg.rss_file('./cyberattacks_news.xml')

if __name__ == '__main__':
    main()
