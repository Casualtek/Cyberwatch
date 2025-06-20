#!/usr/bin/env python3
"""
Iowa state-specific breach monitor configuration and processing
"""

import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import extract_pdf

logger = logging.getLogger(__name__)

class IowaConfig:
    BASE_URL = "https://www.iowaattorneygeneral.gov"
    STATE_NAME = "Iowa"
    
    @staticmethod
    def get_current_year_url():
        """Get the current year-specific URL for Iowa breach notifications"""
        current_year = datetime.now().year
        return f"https://www.iowaattorneygeneral.gov/for-consumers/security-breach-notifications/{current_year}-security-breach-notification"
    
    @staticmethod
    def parse_breach_table(html_content):
        """Parse the Iowa breach notification table"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Calculate yesterday's date (day before execution) in M-DD-YYYY format
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%-m-%-d-%Y')  # Remove leading zeros
        logger.info(f"Filtering notifications for date: {yesterday_str}")
        
        # Find the table (there should be only one)
        table = soup.find('table')
        
        if not table:
            logger.error("Iowa breach table not found - unable to parse page structure")
            return None  # Indicates parsing failure
        
        # Find tbody or look for rows directly
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            rows = table.find_all('tr')
        
        breaches = []
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            # Skip header rows or rows with insufficient columns
            if len(cells) < 2 or row.find('th'):
                continue
                
            try:
                # First column: date in M-DD-YYYY format
                date_cell = cells[0]
                # Second column: organization name and link(s)
                org_cell = cells[1]
                
                # Extract date from first column
                date_text = date_cell.get_text(strip=True)
                
                # Only process notifications from yesterday
                if date_text != yesterday_str:
                    logger.debug(f"Skipping notification dated {date_text} (not from yesterday {yesterday_str})")
                    continue
                
                # Extract organization names and links from second column
                # Note: There can be multiple links per organization (original + supplemental letters)
                links = org_cell.find_all('a')
                
                if not links:
                    logger.warning(f"No links found for date {date_text}")
                    continue
                
                # Process each link in the cell
                for link in links:
                    link_text = link.get_text(strip=True)
                    link_href = link.get('href')
                    
                    if not link_href:
                        logger.warning(f"Link found but no href for: {link_text}")
                        continue
                    
                    # Convert relative URL to absolute
                    if link_href.startswith('/'):
                        full_link = urljoin(IowaConfig.BASE_URL, link_href)
                    else:
                        full_link = link_href
                    
                    # Skip supplemental letters - focus on the main notification
                    if 'supplemental' in link_text.lower():
                        logger.debug(f"Skipping supplemental letter: {link_text}")
                        continue
                    
                    breaches.append({
                        'date': date_text,
                        'organization': link_text,
                        'link': full_link
                    })
                    logger.info(f"Added notification from {date_text}: {link_text}")
                    
            except Exception as e:
                logger.warning(f"Error parsing row: {e}")
                continue
        
        logger.info(f"Found {len(breaches)} notifications from {yesterday_str}")
        return breaches  # Empty list is valid - means no matching results
    
    @staticmethod
    def process_breach(link, fetch_webpage_func):
        """Process Iowa breach notification"""
        try:
            logger.info(f"Processing Iowa breach: {link}")
            
            # Iowa links are direct PDF links, so we can use extract_pdf directly
            extracted_data = extract_pdf.main(link)
            
            if extracted_data:
                logger.info(f"Successfully processed Iowa breach: {link}")
                return extracted_data
            else:
                logger.info(f"No data extracted from {link} (likely filtered out)")
                return None
                
        except Exception as e:
            logger.error(f"Error processing Iowa breach {link}: {e}")
            return None
    
    @staticmethod
    def get_telegram_message_prefix():
        """Get Telegram message prefix for Iowa"""
        return "🚨 *Iowa Breach Monitor Alert*\n\n"
