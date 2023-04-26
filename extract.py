import openai
import os
import json
import re
from datetime import datetime
from newspaper import Article

openai.api_key = os.environ['OPENAI_API']
article_url    = os.environ['URL']
json_file      = './cyberattacks.json'

def load_articles_from_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            articles = json.load(f)
            return articles
    else:
        return []

def save_articles_to_json(articles, filename):
    with open(filename, 'w') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

def extract_country_code(text):
    pattern = r'\b[A-Z]{3}\b'
    matches = re.findall(pattern, text)
    if matches:
        return matches[0]
    else:
        return None

def ask_chatgpt(news_content, news_title):
    messages = [
        {'role': 'system', 'content': 'Tu es un modèle d\'intelligence artificielle entraîné pour analyser des articles de presse et répondre à des questions. Tu es spécialisé en cybersécurité.'},
        {'role': 'user', 'content': f'Voici un article au sujet d\'une cyberattaque:\n{news_title}\n{news_content}\n\nRésume cet article en 5 phrases maximum, en français.'}
    ]

    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
        max_tokens=180,
        n=1,
        temperature=0.2,
    )
    summary = completion.choices[0].message.content
    
    messages.append({'role': 'assistant', 'content': summary})
    messages.append({'role': 'user', 'content': 'Sans faire de phrase, indique le nom de la victime.'})

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=10,
        n=1,
        temperature=0.2,
    )
    victim = completion.choices[0].message.content

    messages.append({'role': 'assistant', 'content': victim})
    messages.append({'role': 'user', 'content': 'Indique le nom du pays concerné ou, à défaut, celui dont est originaire la victime.'})

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=10,
        n=1,
        temperature=0.2,
    )
    country = completion.choices[0].message.content

    messages.append({'role': 'assistant', 'content': country})
    messages.append({'role': 'user', 'content': 'Sans faire de phrase, indique le code ISO 3166-1 alpha-3 du pays que tu viens de mentionner.'})

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=10,
        n=1,
        temperature=0.2,
    )
    country = completion.choices[0].message.content

    output = {
        'summary': summary,
        'victim' : victim,
        'country': country
        }

    return output

def main(url):
    stories = load_articles_from_json(json_file)

    article = Article(url)
    article.download()
    article.parse()

    print(article.text)
    
    PubDate  = article.publish_date
    if PubDate is None or PubDate == '':
        PubDate = datetime.now()
    
    victim = ''
    country= ''
    summary= ''

    if article.summary != '' and article.title !='':
        analysis = ask_chatgpt(article.summary, article.title)
        victim = analysis['victim']
        country= analysis['country']
        summary= analysis['summary']
    elif article.text !='':
        analysis = ask_chatgpt(article.text, article.title)
        victim = analysis['victim']
        country= analysis['country']
        summary= analysis['summary']

    print(victim)
    print(country)
    print(summary)
    
    story = {
        'date': PubDate.strftime('%Y-%m-%d'),
        'victim': victim,
        'country': country,
        'summary': summary,
        'title': article.title,
        'url': url
    }

    stories.append(story)
    save_articles_to_json(stories, json_file)

if __name__ == "__main__":
    main(article_url)

