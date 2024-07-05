#!/usr/bin/python3
import openai
import json
import sys
import os
from datetime import datetime, timedelta

openai.api_key = os.environ['OPENAI_API_KEY']

def load_articles_from_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            articles = json.load(f)
            return articles
    else:
        return []

def ask_chatgpt(news_count, most_hit_country, countries):
    messages = [
        {'role': 'system', 'content': 'Tu es un journaliste spécialisé en cybersécurité. Tu prépares une revue de presse portant sur les cyberattaques rapportées dans la presse au cours de la semaine écoulée. Cette revue de presse s\'appelle le Cyberhebdo.'},
        {'role': 'user', 'content': f'Rédige le texte d\'introduction de la revue de presse pour la semaine dernière, sachant que nous avons observé {news_count} cyberattaques évoquées dans les médias des pays suivants : {countries}. Indique que le pays le plus représenté est {most_hit_country["country"]} avec {most_hit_country["count"]} cas rapportés.'}
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
    
    return summary

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
    
    html = '<p>Chaque semaine, dans le Cyberhebdo, nous vous présentons une liste aussi exhaustive que possible des cyberattaques évoquées par la presse dans le monde entier.</p>\n'
    html += f'<p>{news_report}</p>\n'
    html += '<p>Nous vous rappelons que notre revue de presse se concentre sur les cyberattaques significatives et ne traite pas des attaques DDoS ni des défigurations de sites Web.</p>'
    html_list = ''
    for item in recent_items:
        date = datetime.strptime(item['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        html_list += f'<p>{date} - <b>{item["victim"]}</b> ({item["country"]})<br/>{item["summary"]} (<a href="{item["url"]}">source</a>)</p>\n'
    html += html_list
    html += '<i>Revue de presse réalisée en partie avec ChatGPT. <a href="https://www.lemagit.fr/actualites/365535799/Cyberhebdo-LeMagIT-met-lIA-au-service-de-linformation-de-ses-lecteurs">Les explications sont à lire ici</a>.</i>'
    
    with open(f'./cyberhebdo/{now.strftime("%Y-%m-%d")}.html', 'w') as html_file:
        html_file.write(html)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename.json>")
        sys.exit(1)
    main(sys.argv[1])
