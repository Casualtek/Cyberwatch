#!/usr/bin/env python3
"""
Vermont state-specific breach monitor configuration and processing
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_tz, mktime_tz
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import extract_pdf

logger = logging.getLogger(__name__)

class VermontConfig:
    RSS_URL = "https://ago.vermont.gov/taxonomy/term/10/feed"
    BASE_URL = "https://ago.vermont.gov"
    STATE_NAME = "Vermont"
    
    @staticmethod
    def parse_rss_feed(rss_content):
        """Parse the Vermont RSS feed"""
        try:
            # Calculate yesterday's date (day before execution)
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime('%Y-%m-%d')
            logger.info(f"Filtering RSS items for date: {yesterday_str}")
            
            # Parse XML
            root = ET.fromstring(rss_content)
            
            # Find all items
            items = root.findall('.//item')
            breaches = []
            
            for item in items:
                try:
                    # Extract title, link, and pubDate
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    pubdate_elem = item.find('pubDate')
                    
                    title = title_elem.text.strip()
                    link = link_elem.text.strip()
                    pubdate_str = pubdate_elem.text.strip()
                    
                    # Parse pubDate: "Thu, 19 Jun 2025 12:12:39 +0000"
                    pubdate_tuple = parsedate_tz(pubdate_str)
                    if pubdate_tuple:
                        pubdate = datetime.fromtimestamp(mktime_tz(pubdate_tuple))
                        pubdate_formatted = pubdate.strftime('%Y-%m-%d')
                    else:
                        logger.warning(f"Could not parse pubDate: {pubdate_str}")
                        continue
                    
                    # Only process items from yesterday
                    if pubdate_formatted != yesterday_str:
                        logger.debug(f"Skipping item dated {pubdate_formatted} (not from yesterday {yesterday_str})")
                        continue
                    
                    breaches.append({
                        'title': title,
                        'link': link,
                        'pubdate': pubdate_formatted
                    })
                    logger.info(f"Added RSS item from {pubdate_formatted}: {title}")
                    
                except Exception as e:
                    logger.warning(f"Error parsing RSS item: {e}")
                    continue
            
            logger.info(f"Found {len(breaches)} RSS items from {yesterday_str}")
            return breaches
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}")
            return []
    
    @staticmethod
    def extract_pdf_link(url, fetch_webpage_func):
        """Extract PDF link from Vermont notification page"""
        try:
            html_content = fetch_webpage_func(url)
            if not html_content:
                return None
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find div with class "field__item"
            field_div = soup.find('span', class_='file--application-pdf')
            if not field_div:
                logger.warning(f"No field__item div found in {url}")
                return None
            
            # Find link to PDF within the div
            pdf_link = field_div.find('a')
            if not pdf_link:
                logger.warning(f"No PDF link found in field__item div in {url}")
                return None
            
            href = pdf_link.get('href')
            if not href:
                logger.warning(f"PDF link has no href in {url}")
                return None
            
            # Convert relative URL to absolute
            full_pdf_url = urljoin(VermontConfig.BASE_URL, href)
            logger.info(f"Found PDF link: {full_pdf_url}")
            
            return full_pdf_url
            
        except Exception as e:
            logger.error(f"Error extracting PDF link from {url}: {e}")
            return None
    
    @staticmethod
    def process_breach(item, fetch_webpage_func):
        """Process Vermont breach notification"""
        try:
            title = item['title']
            link = item['link']
            logger.info(f"Processing Vermont breach: {title}")
            
            # Extract PDF link from the notification page
            pdf_url = VermontConfig.extract_pdf_link(link, fetch_webpage_func)
            if not pdf_url:
                logger.error(f"Failed to extract PDF link from notification page: {link}")
                return None
            
            # Call extract_pdf with the PDF URL
            extracted_data = extract_pdf.main(pdf_url)
            
            if extracted_data:
                # Override with Vermont-specific details where available
                extracted_data['url'] = link  # Keep the notification page URL as the main URL
                extracted_data['title'] = title
                extracted_data['pubdate'] = item['pubdate']
                
                logger.info(f"Successfully processed Vermont breach: {title}")
                return extracted_data
            else:
                logger.info(f"No data extracted from PDF {pdf_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing Vermont breach {item.get('title', 'unknown')}: {e}")
            return None
    
    @staticmethod
    def get_telegram_message_prefix():
        """Get Telegram message prefix for Vermont"""
        return "🚨 *Vermont Breach Monitor Alert*\n\n"