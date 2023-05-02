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

def ask_chatgpt(news_count, countries):
    messages = [
        {'role': 'system', 'content': 'Tu es un journaliste spécialisé en cybersécurité. Tu prépares une revue de presse portant sur les cyberattaques rapportées dans la presse au cours de la semaine écoulée. Cette revue de presse s\'appelle le Cyberhebdo.'},
        {'role': 'user', 'content': f'Rédige le texte d\'introduction de la revue de presse pour la semaine dernière, sachant que nous avons observé {news_count} cyberattaques évoquées dans les médias des pays suivants : {countries}. Pense à préciser que les cyberattaques en DDoS ne sont pas traitées !'}
    ]

    print(f'Obtaining introduction.')
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
        max_tokens=180,
        n=1,
        temperature=0.2,
    )
    summary = completion.choices[0].message.content
    print(summary)

    messages.append({'role': 'assistant', 'content': summary})
    messages.append({'role': 'user', 'content': 'Rédige un résumé de ce texte en moins de 150 caractères.'})

    print(f'Obtaining summary.')
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
        max_tokens=30,
        n=1,
        temperature=0.2,
    )
    victim = completion.choices[0].message.content
    print(victim)

    messages.append({'role': 'assistant', 'content': victim})
    messages.append({'role': 'user', 'content': 'Il nous faudrait un titre également.'})

    print(f'Obtaining title.')
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
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

def main(json_file):
    stories = load_articles_from_json(json_file)
    stories.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))
    
    now          = datetime.now()
    one_week_ago = now - timedelta(days=7)
    recent_items = [item for item in stories if datetime.strptime(item['date'], '%Y-%m-%d') >= one_week_ago]
    recent_items.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))
    news_count     = len(recent_items)
    countries_list = set([item['country'] for item in recent_items])
    countries      = ', '.join(countries_list)
    
    news_report = ask_chatgpt(news_count,countries)
    
    html = f'<html>\n<head>\n<title>{news_report["title"]}</title>\n</head>\n<body>\n'
    html += f'<p>{news_report["summary"]}</p>\n'
    html += f'<p>{news_report["introduction"]}</p>\n'
    html_list = '<ul>\n'
    for item in recent_items:
        date = datetime.strptime(item['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        html_list += f'<li>{date} - <b>{item["victim"]}</b> ({item["country"]})<br/>{item["summary"]} (<a href="{item["url"]}">source</a>)</li>\n'
    html_list += '</ul>\n'
    html += html_list
    html += '<i>Revue de presse réalisée en partie avec ChatGPT. <a href="https://www.lemagit.fr/actualites/365535799/Cyberhebdo-LeMagIT-met-lIA-au-service-de-linformation-de-ses-lecteurs">Les explications sont à lire ici</a>.</i>'
    html += '</body>\n</html>'
    
    with open(f'./cyberhebdo/{now.strftime("%Y-%m-%d")}.html', 'w') as html_file:
        html_file.write(html)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename.json>")
        sys.exit(1)
    main(sys.argv[1])
