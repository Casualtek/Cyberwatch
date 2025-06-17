#!/usr/bin/python3
import argparse
import json
import requests
import os
import PyPDF2
import re
import socket
import time
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
from groq import Groq
from io import BytesIO
import domain_discovery

groq_api_key   = os.environ['GROQ_API']
gpt_model      = 'llama-3.3-70b-versatile'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}



def extract_country_code(text):
    pattern = r'\b[A-Z]{3}\b'
    matches = re.findall(pattern, text)
    if matches:
        return matches[0]
    else:
        return None

def summarise_pdf(pdf_file, victim):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""

    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()

    text_without_images = ""

    for word in text.split():
        if word.startswith("Image") or word.startswith("IMAGE"):
            continue
        text_without_images += word + " "

    text_chunks = []
    chunk_size = 500

    for i in range(0, len(text_without_images), chunk_size):
        text_chunks.append(text_without_images[i:i+chunk_size])

    client = Groq(
        api_key=groq_api_key,
    )

    summary = ""
    for chunk in text_chunks:
        messages = [
            {'role': 'user', 'content': chunk},
            {'role': 'user', 'content': 'Résume le texte précédent en une phrase, en Français.'}
        ]
        response = client.chat.completions.create(
            model=gpt_model,
            messages=messages,
            max_tokens=50,
            n=1,
            temperature=0.1
        )
        summary += response.choices[0].message.content

    merged_text = ""
    for chunk in text_chunks:
        merged_text += chunk + " "

    # Write a new summary of the merged chunks
    messages = [
        {'role': 'user', 'content': merged_text},
        {'role': 'user', 'content': 'Résume le texte précédent en un paragraphe de cinq phrases, au maximum.'}
    ]
    merged_summary = client.chat.completions.create(
        model=gpt_model,
        messages=messages,
        max_tokens=200,
        n=1,
        temperature=0.1
    ).choices[0].message.content

    # Try to discover domain using multiple methods
    domain_name = domain_discovery.discover_domain(victim, client, model=gpt_model)

    messages = [
        {'role': 'user', 'content': 'Indique-moi, au format YYYY-MM-DD, la date de découverte de l\'incident rapporté dans le texte suivant : '+merged_summary}
    ]
    date_discovered = client.chat.completions.create(
        model=gpt_model,
        messages=messages,
        max_tokens=10,
        n=1,
        temperature=0.1
    ).choices[0].message.content


    return {
        'domain' : domain_name,
        'date'   : date_discovered,
        'summary': merged_summary
    }

def scrape_page(url):

    with requests.Session() as session:
        try:
            response = session.get(
                url,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error requesting page {page_number}: {e}")
            return None

def extract_details(html):
    soup = BeautifulSoup(html, 'html.parser')

    victim = None
    date = None
    link = None
    breach_description = None

    for li in soup.find_all('li'):
        if 'Entity Name:' in li.get_text(strip=True):
            victim = li.find('strong').get_text(strip=True)
        if 'Date(s) Breach Occured:' in li.get_text(strip=True):
            date = li.find('strong').get_text(strip=True)
        if 'Copy of notice to affected Maine residents' in li.get_text(strip=True):
            link = li.find('a')['href']
        if 'Description of the Breach:' in li.get_text(strip=True):
            breach_description = li.find('strong').get_text(strip=True)
    
    return {
        'victim': victim,
        'date' : date_parser.parse(date).strftime("%Y-%m-%d"),
        'link' : link,
        'breach_description': breach_description,
        }

def main(url):

    notification = scrape_page(url)

    details  = extract_details(notification)
    print(details)
    
    # Check if breach description is "External system breach (hacking)"
    breach_description = details.get('breach_description', '')
    if breach_description != 'External system breach (hacking)':
        print(f"Skipping notification - breach description is '{breach_description}', not 'External system breach (hacking)'")
        return None
    
    print("Processing notification - breach description matches 'External system breach (hacking)'")
    
    pdf_link = details['link']
    victim   = details['victim']
    date     = details['date']
    
    pdf_file = requests.get('https://www.maine.gov'+pdf_link, headers=headers)     
    summary  = summarise_pdf(BytesIO(pdf_file.content), victim)

    domain = summary['domain']
    if not domain:
        domain = ''

    today  = datetime.now()

    story = {
        'date': date,
        'victim': victim,
        'domain': domain,
        'country': 'USA',
        'summary': summary['summary'],
        'title': 'Data Breach Notification',
        'url': url,
        'added': today.strftime('%Y-%m-%d'),
    }

    print(story)
    return story

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze the content of a breach disclosure.')
    parser.add_argument('url', help='The URL of the webpage to analyze.')
    args = parser.parse_args()
    main(args.url)
