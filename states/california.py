#!/usr/bin/env python3
"""
California state-specific breach monitor configuration and processing
"""

import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import extract_pdf

logger = logging.getLogger(__name__)

class CaliforniaConfig:
    URL = "https://oag.ca.gov/privacy/databreach/list"
    BASE_URL = "https://oag.ca.gov"
    STATE_NAME = "California"
    
    @staticmethod
    def parse_breach_table(html_content):
        """Parse the California breach notification table"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Calculate yesterday's date (day before execution) in MM/DD/YYYY format
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%m/%d/%Y')
        logger.info(f"Filtering notifications for date: {yesterday_str}")
        
        # Find the table with the specified class
        table = soup.find('table', class_='views-table cols-3 table table-hover table-striped')
        
        if not table:
            logger.error("California breach table not found - unable to parse page structure")
            return None  # Indicates parsing failure
        
        # Find tbody
        tbody = table.find('tbody')
        if not tbody:
            logger.warning("No tbody found, looking for rows in table directly")
            rows = table.find_all('tr')
        else:
            rows = tbody.find_all('tr')
        
        breaches = []
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            # Skip header rows or rows with insufficient columns
            if len(cells) < 3 or row.find('th'):
                continue
                
            try:
                # Column 0: Organization name and link
                org_cell = cells[0]
                # Column 1: Date(s) of breach (we don't filter on this)
                breach_date_cell = cells[1]
                # Column 2: Reported date (we filter on this)
                reported_date_cell = cells[2]
                
                # Extract reported date from third column
                reported_date_text = reported_date_cell.get_text(strip=True)
                
                # Only process notifications from yesterday
                if reported_date_text != yesterday_str:
                    logger.debug(f"Skipping notification reported {reported_date_text} (not from yesterday {yesterday_str})")
                    continue
                
                # Extract organization name and link from first column
                link_elem = org_cell.find('a')
                if link_elem:
                    org_name = link_elem.get_text(strip=True)
                    link_href = link_elem.get('href')
                    if link_href:
                        # Convert relative URL to absolute if needed
                        if link_href.startswith('/'):
                            full_link = urljoin(CaliforniaConfig.BASE_URL, link_href)
                        else:
                            full_link = link_href
                    else:
                        logger.warning(f"Link element found but no href for: {org_name}")
                        full_link = None
                else:
                    # If no link, just get the text
                    org_name = org_cell.get_text(strip=True)
                    full_link = None
                    logger.warning(f"No link found for organization: {org_name}")
                
                # Extract breach dates for logging
                breach_dates = breach_date_cell.get_text(strip=True)
                
                if org_name and reported_date_text and full_link:
                    breaches.append({
                        'organization': org_name,
                        'breach_dates': breach_dates,
                        'reported_date': reported_date_text,
                        'link': full_link
                    })
                    logger.info(f"Added notification reported {reported_date_text}: {org_name} (breach dates: {breach_dates})")
                else:
                    logger.warning(f"Incomplete data for row: org={org_name}, reported_date={reported_date_text}, link={full_link}")
                    
            except Exception as e:
                logger.warning(f"Error parsing row: {e}")
                continue
        
        logger.info(f"Found {len(breaches)} notifications reported on {yesterday_str}")
        return breaches  # Empty list is valid - means no matching results
    
    @staticmethod
    def extract_pdf_link(notification_url, fetch_webpage_func):
        """Extract PDF link from California notification page"""
        try:
            logger.info(f"Extracting PDF link from notification page: {notification_url}")
            html_content = fetch_webpage_func(notification_url)
            if not html_content:
                logger.error(f"Failed to fetch notification page: {notification_url}")
                return None
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for PDF links (typically Individual Notification Letter or similar)
            pdf_links = []
            
            # Find all links that point to PDF files
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.lower().endswith('.pdf'):
                    # Convert relative URL to absolute if needed
                    if href.startswith('/'):
                        full_pdf_url = urljoin(CaliforniaConfig.BASE_URL, href)
                    else:
                        full_pdf_url = href
                    
                    link_text = link.get_text(strip=True)
                    pdf_links.append({
                        'url': full_pdf_url,
                        'text': link_text
                    })
                    logger.info(f"Found PDF link: {link_text} -> {full_pdf_url}")
            
            if not pdf_links:
                logger.warning(f"No PDF links found on notification page: {notification_url}")
                return None
            
            # Prefer links that contain words like "individual", "notification", "letter", "notice"
            preferred_keywords = ['individual', 'notification', 'letter', 'notice', 'sample']
            
            for pdf_link in pdf_links:
                text_lower = pdf_link['text'].lower()
                if any(keyword in text_lower for keyword in preferred_keywords):
                    logger.info(f"Selected preferred PDF: {pdf_link['text']}")
                    return pdf_link['url']
            
            # If no preferred PDF found, return the first one
            selected_pdf = pdf_links[0]
            logger.info(f"No preferred PDF found, using first available: {selected_pdf['text']}")
            return selected_pdf['url']
            
        except Exception as e:
            logger.error(f"Error extracting PDF link from {notification_url}: {e}")
            return None
    
    @staticmethod
    def process_breach(link, fetch_webpage_func):
        """Process California breach notification"""
        try:
            logger.info(f"Processing California breach: {link}")
            
            # First, extract PDF link from the notification page
            pdf_url = CaliforniaConfig.extract_pdf_link(link, fetch_webpage_func)
            if not pdf_url:
                logger.error(f"Failed to extract PDF link from notification page: {link}")
                return None
            
            logger.info(f"Extracted PDF URL: {pdf_url}")
            
            # Now process the PDF using extract_pdf
            extracted_data = extract_pdf.main(pdf_url)
            
            if extracted_data:
                # Override URL to point to the notification page (not the PDF)
                extracted_data['url'] = link
                extracted_data['pdf_url'] = pdf_url
                
                logger.info(f"Successfully processed California breach: {link}")
                return extracted_data
            else:
                logger.info(f"No data extracted from PDF {pdf_url} (likely filtered out)")
                return None
                
        except Exception as e:
            logger.error(f"Error processing California breach {link}: {e}")
            return None
    
    @staticmethod
    def get_telegram_message_prefix():
        """Get Telegram message prefix for California"""
        return "🚨 *California Breach Monitor Alert*\n\n"
