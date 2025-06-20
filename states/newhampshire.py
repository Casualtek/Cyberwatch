#!/usr/bin/env python3
"""
New Hampshire state-specific breach monitor configuration and processing
"""

import logging
import json
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin
import extract_pdf

logger = logging.getLogger(__name__)

class NewHampshireConfig:
    API_URL = "https://www.doj.nh.gov/content/api/documents?q=%40field_document_category%7C%3D%7C2146%40field_document_purpose%7CCONTAINS%7C5996&textsearch=&sort=field_date_posted%7Cdesc%7CALLOW_NULLS&iterate_nodes=true&filter_mode=INCLUSIVE&type=document&page=1&size=25"
    BASE_URL = "https://www.doj.nh.gov"
    STATE_NAME = "New Hampshire"
    
    @staticmethod
    def fetch_json_api():
        """Fetch JSON API with specific headers for New Hampshire"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Referer': 'https://www.doj.nh.gov/consumer/security-breaches',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = requests.get(NewHampshireConfig.API_URL, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching New Hampshire JSON API: {e}")
            return None
    
    @staticmethod
    def parse_json_api(json_content):
        """Parse the New Hampshire JSON API response"""
        try:
            # Calculate yesterday's date (day before execution)
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime('%Y-%m-%d')
            logger.info(f"Filtering notifications for date: {yesterday_str}")
            
            # Parse JSON
            data = json.loads(json_content)
            
            # Get the data list
            if 'data' not in data:
                logger.error("No 'data' field found in JSON response - unable to parse API response")
                return None  # Indicates parsing failure
            
            items = data['data']
            breaches = []
            
            for item in items:
                try:
                    # Extract title (organization name)
                    title = item.get('title', '').strip()
                    if not title:
                        logger.warning("Item has no title, skipping")
                        continue
                    
                    # Extract date from field_date_posted
                    if 'fields' not in item or 'field_date_posted' not in item['fields']:
                        logger.warning(f"No date field found for item: {title}")
                        continue
                    
                    date_posted_list = item['fields']['field_date_posted']
                    if not date_posted_list or len(date_posted_list) == 0:
                        logger.warning(f"Empty date field for item: {title}")
                        continue
                    
                    # Get the first date from the list
                    date_posted = date_posted_list[0]
                    # Parse date (assuming format like "2024-06-19T12:00:00")
                    if 'T' in date_posted:
                        date_obj = datetime.fromisoformat(date_posted.replace('Z', '+00:00'))
                    else:
                        date_obj = datetime.strptime(date_posted, '%Y-%m-%d')
                    
                    date_formatted = date_obj.strftime('%Y-%m-%d')
                    
                    # Only process notifications from yesterday
                    if date_formatted != yesterday_str:
                        logger.debug(f"Skipping notification dated {date_formatted} (not from yesterday {yesterday_str})")
                        continue
                    
                    # Extract PDF URL from field_document_file
                    if 'field_document_file' not in item['fields']:
                        logger.warning(f"No document file field found for item: {title}")
                        continue
                    
                    doc_file_dict = item['fields']['field_document_file']
                    if not doc_file_dict or '0' not in doc_file_dict:
                        logger.warning(f"Empty or invalid document file field for item: {title}")
                        continue
                    
                    # Get the first document file
                    doc_file = doc_file_dict['0']
                    if 'fields' not in doc_file or 'uri' not in doc_file['fields']:
                        logger.warning(f"No URI field found in document file for item: {title}")
                        continue
                    
                    pdf_uri_list = doc_file['fields']['uri']
                    if not pdf_uri_list or len(pdf_uri_list) == 0:
                        logger.warning(f"Empty URI field for item: {title}")
                        continue
                    
                    pdf_uri = pdf_uri_list[0]
                    if not pdf_uri:
                        logger.warning(f"Empty URI field for item: {title}")
                        continue
                    
                    # Convert relative URL to absolute if needed
                    if pdf_uri.startswith('/'):
                        full_pdf_url = urljoin(NewHampshireConfig.BASE_URL, pdf_uri)
                    else:
                        full_pdf_url = pdf_uri
                    
                    breaches.append({
                        'title': title,
                        'date': date_formatted,
                        'pdf_url': full_pdf_url
                    })
                    logger.info(f"Added notification from {date_formatted}: {title}")
                    
                except Exception as e:
                    logger.warning(f"Error parsing JSON item: {e}")
                    continue
            
            logger.info(f"Found {len(breaches)} notifications from {yesterday_str}")
            return breaches  # Empty list is valid - means no matching results
            
        except Exception as e:
            logger.error(f"Error parsing JSON API response: {e}")
            return None  # Indicates parsing failure
    
    @staticmethod
    def process_breach(item, fetch_webpage_func):
        """Process New Hampshire breach notification"""
        try:
            title = item['title']
            pdf_url = item['pdf_url']
            date = item['date']
            logger.info(f"Processing New Hampshire breach: {title}")
            
            # Call extract_pdf with the PDF URL
            extracted_data = extract_pdf.main(pdf_url)
            
            if extracted_data:
                # Override with New Hampshire-specific details where available
                extracted_data['victim'] = title
                extracted_data['date'] = date
                extracted_data['url'] = pdf_url  # Use PDF URL as the main URL
                
                logger.info(f"Successfully processed New Hampshire breach: {title}")
                return extracted_data
            else:
                logger.info(f"No data extracted from PDF {pdf_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing New Hampshire breach {item.get('title', 'unknown')}: {e}")
            return None
    
    @staticmethod
    def get_telegram_message_prefix():
        """Get Telegram message prefix for New Hampshire"""
        return "🚨 *New Hampshire Breach Monitor Alert*\n\n"
