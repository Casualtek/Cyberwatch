#!/usr/bin/env python3
"""
Idaho state-specific breach monitor configuration and processing
"""

import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import extract_pdf

logger = logging.getLogger(__name__)

class IdahoConfig:
    URL = "https://www.ag.idaho.gov/consumer-protection/security-breaches/"
    STATE_NAME = "Idaho"
    
    @staticmethod
    def parse_breach_table(html_content):
        """Parse the Idaho breach notification table"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Calculate yesterday's date (day before execution) in M/DD/YYYY format
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%-m/%d/%Y')  # Remove leading zeros
        logger.info(f"Filtering notifications for date: {yesterday_str}")
        
        # Find the table with breach notifications
        table = soup.find('table')
        
        if not table:
            logger.error("No table found on the page")
            return []
        
        # Find the tbody
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
            if len(cells) < 2 or row.find('th'):
                continue
                
            try:
                # First column: organization name and link
                org_cell = cells[0]
                date_cell = cells[1]
                
                # Extract date from second column
                date_text = date_cell.get_text(strip=True)
                
                # Only process notifications from yesterday
                if date_text != yesterday_str:
                    logger.debug(f"Skipping notification dated {date_text} (not from yesterday {yesterday_str})")
                    continue
                
                # Extract organization name and link from first column
                link_elem = org_cell.find('a')
                if link_elem:
                    org_name = link_elem.get_text(strip=True)
                    link_href = link_elem.get('href')
                    if link_href:
                        # Convert relative URL to absolute if needed
                        if link_href.startswith('/'):
                            full_link = urljoin(IdahoConfig.URL, link_href)
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
                
                if org_name and date_text and full_link:
                    breaches.append({
                        'date': date_text,
                        'organization': org_name,
                        'link': full_link
                    })
                    logger.info(f"Added notification from {date_text}: {org_name}")
                else:
                    logger.warning(f"Incomplete data for row: org={org_name}, date={date_text}, link={full_link}")
                    
            except Exception as e:
                logger.warning(f"Error parsing row: {e}")
                continue
        
        logger.info(f"Found {len(breaches)} notifications from {yesterday_str}")
        return breaches
    
    @staticmethod
    def process_breach(link, fetch_webpage_func):
        """Process Idaho breach notification"""
        try:
            logger.info(f"Processing Idaho breach: {link}")
            
            # Idaho links are direct PDF links, so we can use extract_pdf directly
            extracted_data = extract_pdf.main(link)
            
            if extracted_data:
                logger.info(f"Successfully processed Idaho breach: {link}")
                return extracted_data
            else:
                logger.info(f"No data extracted from {link} (likely filtered out)")
                return None
                
        except Exception as e:
            logger.error(f"Error processing Idaho breach {link}: {e}")
            return None
    
    @staticmethod
    def get_telegram_message_prefix():
        """Get Telegram message prefix for Idaho"""
        return "🚨 *Idaho Breach Monitor Alert*\n\n"