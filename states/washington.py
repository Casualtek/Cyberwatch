#!/usr/bin/env python3
"""
Washington state-specific breach monitor configuration and processing
"""

import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import extract_pdf

logger = logging.getLogger(__name__)

class WashingtonConfig:
    URL = "https://www.atg.wa.gov/data-breach-notifications"
    STATE_NAME = "Washington"
    
    @staticmethod
    def parse_breach_table(html_content):
        """Parse the Washington breach notification table"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for the table with the specified class
        table = soup.find('table', class_='tablesaw tablesaw-stack cols-5')
        
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
                # Washington has different cell order: date is in cells[2], name in cells[1]
                date_cell = cells[2]
                name_cell = cells[1] if len(cells) > 1 else cells[0]
                
                # Extract date
                date_text = date_cell.get_text(strip=True)
                
                # Extract organization name and link
                link_elem = name_cell.find('a')
                if link_elem:
                    org_name = link_elem.get_text(strip=True)
                    link_href = link_elem.get('href')
                else:
                    org_name = name_cell.get_text(strip=True)
                    link_href = None
                
                if org_name and date_text:
                    breaches.append({
                        'date': date_text,
                        'organization': org_name,
                        'link': link_href
                    })
                    
            except Exception as e:
                logger.warning(f"Error parsing row: {e}")
                continue
        
        return breaches
    
    @staticmethod
    def process_breach(link, fetch_webpage_func):
        """Process Washington breach notification"""
        try:
            logger.info(f"Processing Washington breach: {link}")
            
            # Washington links are direct PDF links, so we can use extract_pdf directly
            extracted_data = extract_pdf.main(link)
            
            if extracted_data:
                logger.info(f"Successfully processed Washington breach: {link}")
                return extracted_data
            else:
                logger.info(f"No data extracted from {link} (likely filtered out)")
                return None
                
        except Exception as e:
            logger.error(f"Error processing Washington breach {link}: {e}")
            return None
    
    @staticmethod
    def get_telegram_message_prefix():
        """Get Telegram message prefix for Washington"""
        return "🚨 *Washington Breach Monitor Alert*\n\n"