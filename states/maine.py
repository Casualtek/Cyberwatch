#!/usr/bin/env python3
"""
Maine state-specific breach monitor configuration and processing
"""

import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dateutil import parser as date_parser
import extract_pdf

logger = logging.getLogger(__name__)

class MaineConfig:
    URL = "https://www.maine.gov/agviewer/content/ag/985235c7-cb95-4be2-8792-a1252b4f8318/list.html"
    STATE_NAME = "Maine"
    
    @staticmethod
    def parse_breach_table(html_content):
        """Parse the Maine breach notification table"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Calculate yesterday's date (day before execution)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        logger.info(f"Filtering notifications for date: {yesterday}")
        
        # Look for the table with the specified class
        table = soup.find('table', class_='breachTable stripe hover dataTable no-footer')
        
        if not table:
            # Fallback: look for any table or div containing breach data
            logger.warning("Specific table class not found, looking for alternative structure")
            rows = soup.find_all('tr')
            if not rows:
                logger.error("No table structure found")
                return []
        else:
            rows = table.find_all('tr')
        
        breaches = []
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            # Skip header rows
            if len(cells) < 2 or row.find('th'):
                continue
                
            try:
                # Assuming first cell is date, second cell contains the organization name/link
                date_cell = cells[0]
                name_cell = cells[1] if len(cells) > 1 else cells[0]
                
                # Extract date
                date_text = date_cell.get_text(strip=True)
                
                # Only process notifications from yesterday
                if date_text != yesterday:
                    logger.debug(f"Skipping notification dated {date_text} (not from yesterday {yesterday})")
                    continue
                
                # Extract organization name and link
                link_elem = name_cell.find('a')
                if link_elem:
                    org_name = link_elem.get_text(strip=True)
                    link_href = link_elem.get('href')
                    if link_href:
                        # Convert relative URL to absolute
                        full_link = urljoin(MaineConfig.URL, link_href)
                    else:
                        full_link = None
                else:
                    org_name = name_cell.get_text(strip=True)
                    full_link = None
                
                if org_name and date_text:
                    breaches.append({
                        'date': date_text,
                        'organization': org_name,
                        'link': full_link
                    })
                    logger.info(f"Added notification from {date_text}: {org_name}")
                    
            except Exception as e:
                logger.warning(f"Error parsing row: {e}")
                continue
        
        logger.info(f"Found {len(breaches)} notifications from {yesterday}")
        return breaches
    
    @staticmethod
    def extract_notification_details(url, fetch_webpage_func):
        """Extract details from Maine notification page"""
        try:
            html_content = fetch_webpage_func(url)
            if not html_content:
                return None
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            victim = None
            date = None
            pdf_link = None
            breach_description = None
            
            for li in soup.find_all('li'):
                li_text = li.get_text(strip=True)
                if 'Entity Name:' in li_text:
                    strong_elem = li.find('strong')
                    if strong_elem:
                        victim = strong_elem.get_text(strip=True)
                elif 'Date(s) Breach Occured:' in li_text:
                    strong_elem = li.find('strong')
                    if strong_elem:
                        date = strong_elem.get_text(strip=True)
                elif 'Copy of notice to affected Maine residents' in li_text:
                    link_elem = li.find('a')
                    if link_elem:
                        pdf_link = link_elem.get('href')
                elif 'Description of the Breach:' in li_text:
                    strong_elem = li.find('strong')
                    if strong_elem:
                        breach_description = strong_elem.get_text(strip=True)
            
            if not all([victim, date, pdf_link, breach_description]):
                logger.warning(f"Missing required details from {url}")
                return None
                
            return {
                'victim': victim,
                'date': date_parser.parse(date).strftime("%Y-%m-%d"),
                'pdf_link': pdf_link,
                'breach_description': breach_description,
            }
            
        except Exception as e:
            logger.error(f"Error extracting notification details from {url}: {e}")
            return None
    
    @staticmethod
    def process_breach(link, fetch_webpage_func):
        """Process Maine breach notification"""
        try:
            logger.info(f"Processing Maine breach: {link}")
            
            # First extract details from the notification page
            details = MaineConfig.extract_notification_details(link, fetch_webpage_func)
            if not details:
                logger.error(f"Failed to extract details from notification page: {link}")
                return None
                
            # Check if breach description matches the filter criteria
            breach_description = details.get('breach_description', '')
            if breach_description != 'External system breach (hacking)':
                logger.info(f"Skipping notification - breach description is '{breach_description}', not 'External system breach (hacking)'")
                return None
                
            logger.info("Processing notification - breach description matches 'External system breach (hacking)'")
            
            # Construct full PDF URL
            pdf_url = 'https://www.maine.gov' + details['pdf_link']
            logger.info(f"Extracting from PDF: {pdf_url}")
            
            # Call extract_pdf with the PDF URL
            extracted_data = extract_pdf.main(pdf_url)
            
            if extracted_data:
                # Override with Maine-specific details where available
                extracted_data['victim'] = details['victim']
                extracted_data['date'] = details['date']
                extracted_data['url'] = link  # Keep the notification page URL as the main URL
                
                logger.info(f"Successfully processed Maine breach: {link}")
                return extracted_data
            else:
                logger.info(f"No data extracted from PDF {pdf_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing Maine breach {link}: {e}")
            return None
    
    @staticmethod
    def get_telegram_message_prefix():
        """Get Telegram message prefix for Maine"""
        return "🚨 *Maine Breach Monitor Alert*\n\n"