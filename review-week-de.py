#!/usr/bin/python3
import openai
import deepl
import json
import sys
import os
from datetime import datetime, timedelta

openai.api_key = os.environ['OPENAI_API_KEY']
DEEPL_API_KEY  = os.environ['DEEPL_API_KEY']

def translate_text(text):
    translator = deepl.Translator(DEEPL_API_KEY)
    result     = translator.translate_text(text , target_lang='DE')
    return result.text

def load_articles_from_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            articles = json.load(f)
            return articles
    else:
        return []

def ask_chatgpt(news_count, most_hit_country, countries):
    messages = [
        {'role': 'system', 'content': 'Du bist ein Journalist, der sich auf Cybersicherheit spezialisiert hat. Du erstellst eine Presseschau über Cyberangriffe, die in der vergangenen Woche in der Presse berichtet wurden. Diese Presseschau wird Cyberhebdo genannt.'},
        {'role': 'user', 'content': f'Verfasse die Einleitung zur Presseschau der letzten Woche und beachte dabei, dass wir {news_count} Cyberangriffe beobachtet haben, die in den Medien der folgenden Länder erwähnt wurden: {countries}. Gibt an, dass das am stärksten vertretene Land {most_hit_country["country"]} mit {most_hit_country["count"]} gemeldeten Fällen ist. Denkt daran zu erwähnen, dass DDoS-Cyberangriffe nicht behandelt werden, ebenso wenig wie die Verunstaltung von Websites.'}
    ]

    print(f'Obtaining introduction.')
    completion = openai.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        max_tokens=180,
        n=1,
        temperature=0.2,
    )
    summary = completion.choices[0].message.content
    print(summary)

    messages.append({'role': 'assistant', 'content': summary})
    messages.append({'role': 'user', 'content': 'Schreibe eine Zusammenfassung dieses Textes in weniger als 150 Zeichen.'})

    print(f'Obtaining summary.')
    completion = openai.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        max_tokens=30,
        n=1,
        temperature=0.2,
    )
    victim = completion.choices[0].message.content
    print(victim)

    messages.append({'role': 'assistant', 'content': victim})
    messages.append({'role': 'user', 'content': 'Wir bräuchten auch einen Titel.'})

    print(f'Obtaining title.')
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=90,
        n=1,
        temperature=0.2,
    )
    country = completion.choices[0].message.content
    print(country)

    output = {
        'introduction': summary,
        'summary' : victim,
        'title': country
        }

    return output

def most_seen_country(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    most_seen = max(counts, key=counts.get)
    
    output = {
        'country': most_seen,
        'count'  : counts[most_seen]
    }

    return output

def main(json_file):
    stories = load_articles_from_json(json_file)
    stories.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))
    
    now          = datetime.now()
    one_week_ago = now - timedelta(days=9)
    recent_items = [item for item in stories if datetime.strptime(item['date'], '%Y-%m-%d') >= one_week_ago]
    recent_items.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))
    news_count     = len(recent_items)

    # most affected country
    countries_all  = [item['country'] for item in recent_items]
    most_hit       = most_seen_country(countries_all)

    # affected countries
    countries_list = set([item['country'] for item in recent_items])
    countries      = ', '.join(countries_list)
    
    news_report = ask_chatgpt(news_count,most_hit,countries)

    html = f'<html>\n<head>\n<title>{news_report["title"]}</title>\n</head>\n<body>\n'
    html += f'<p>{news_report["summary"]}</p>\n'
    html += f'<p>{news_report["introduction"]}</p>\n'
    html_list = ''
    for item in recent_items:
        date = datetime.strptime(item['date'], '%Y-%m-%d').strftime('%d.%m.%Y')
        html_list += f'<p>{date}, <b>{item["victim"]} ({item["country"]}).</b>{translate_text(item["summary"])}. <a href="{item["url"]}">Quelle</a>.</p>\n'
    html += html_list
    html += '<i>Presseschau, teilweise mit ChatGPT erstellt und von der Redaktion geprüft. <a href="https://www.lemagit.fr/actualites/365535799/Cyberhebdo-LeMagIT-met-lIA-au-service-de-linformation-de-ses-lecteurs">Cyberhebdo</a> wurde von unseren französischen Kollegen von LeMagIT entwickelt.</i>'
    html += '</body>\n</html>'
    
    with open(f'./cyberhebdo/{now.strftime("%Y-%m-%d")}-de.html', 'w') as html_file:
        html_file.write(html)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename.json>")
        sys.exit(1)
    main(sys.argv[1])
