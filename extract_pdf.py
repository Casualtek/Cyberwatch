#!/usr/bin/python3
import argparse
import requests
import PyPDF2
import re
from datetime import datetime
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

def extract_pdf_metadata(pdf_file):
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

    merged_text = ""
    for chunk in text_chunks:
        merged_text += chunk + " "

    # Extract victim/entity name from PDF content
    messages = [
        {'role': 'user', 'content': merged_text},
        {'role': 'user', 'content': 'Identifie le nom de l\'entité ou organisation victime de la violation de données mentionnée dans ce texte. Réponds seulement avec le nom de l\'organisation.'}
    ]
    victim_response = client.chat.completions.create(
        model=gpt_model,
        messages=messages,
        max_tokens=50,
        n=1,
        temperature=0.1
    )
    victim = victim_response.choices[0].message.content.strip()

    # Generate summary
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

    # Extract date from PDF content
    messages = [
        {'role': 'user', 'content': merged_text},
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
        'victim': victim,
        'domain': domain_name,
        'date': date_discovered,
        'summary': merged_summary
    }


def main(pdf_url):
    try:
        pdf_response = requests.get(pdf_url, headers=headers, timeout=30)
        pdf_response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None
    
    metadata = extract_pdf_metadata(BytesIO(pdf_response.content))
    
    domain = metadata['domain']
    if not domain:
        domain = ''

    today = datetime.now()

    story = {
        'date': metadata['date'],
        'victim': metadata['victim'],
        'domain': domain,
        'country': 'USA',
        'summary': metadata['summary'],
        'title': 'Data Breach Notification',
        'url': pdf_url,
        'added': today.strftime('%Y-%m-%d'),
    }

    print(story)
    return story

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze the content of a breach disclosure.')
    parser.add_argument('url', help='The URL of the PDF file to analyze.')
    args = parser.parse_args()
    main(args.url)
