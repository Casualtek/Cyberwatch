#!/usr/bin/python3
import argparse
import json
import os
import requests
import PyPDF2
import re
from datetime import datetime
from groq import Groq
from io import BytesIO
import domain_discovery
from pydantic import BaseModel, ValidationError

groq_api_key   = os.environ.get('GROQ_API')
gpt_model      = 'llama-3.1-8b-instant'

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

    # Define Pydantic model for structured response
    class BreachMetadata(BaseModel):
        victim: str
        summary: str  
        date_discovered: str
        domain: str

    # Extract all metadata at once using structured JSON
    system_prompt = """
You are a data breach analysis expert. When asked to analyze breach notifications,
always respond with valid JSON objects that match this structure:
{
  "victim": "string",
  "summary": "string", 
  "date_discovered": "string",
  "domain": "string"
}
Your response should ONLY contain the JSON object and nothing else.
"""
    
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': f'''Analyze this data breach notification text and extract the following information:

Text to analyze:
{merged_text}

Extract:
- victim: Name of the organization/entity that suffered the breach
- summary: Summary of the breach in maximum 3 sentences
- date_discovered: Date when the incident was discovered (format: YYYY-MM-DD)  
- domain: Primary internet domain name of the organization (e.g., company.com, leave empty if unknown)'''}
    ]
    
    try:
        metadata_response = client.chat.completions.create(
            model=gpt_model,
            messages=messages,
            max_tokens=400,
            n=1,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON and validate with Pydantic
        response_content = metadata_response.choices[0].message.content
        json_data = json.loads(response_content)
        breach_data = BreachMetadata(**json_data)
        
        victim = breach_data.victim.strip()
        merged_summary = breach_data.summary.strip()
        date_discovered = breach_data.date_discovered.strip()
        domain_name = breach_data.domain.strip()
        
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Error with structured JSON response: {e}")
        print(f"Raw response: {metadata_response.choices[0].message.content}")
        # Fallback to empty values
        victim = ''
        merged_summary = ''
        date_discovered = ''
        domain_name = ''
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Fallback to empty values
        victim = ''
        merged_summary = ''
        date_discovered = ''
        domain_name = ''
    
    # If LLM didn't provide a domain, try domain discovery as fallback
    if not domain_name and victim:
        domain_name = domain_discovery.discover_domain(victim, client, model=gpt_model)

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
