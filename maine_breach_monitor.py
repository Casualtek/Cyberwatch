#!/usr/bin/env python3
"""
Maine Breach Notification Monitor
Scrapes the Maine Attorney General's breach notification page and checks
against existing cyberattacks.json data to identify new breaches.
"""

import requests
import json
import subprocess
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from datetime import datetime
import extract_pdf
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URLs and files
MAINE_BREACH_URL = "https://www.maine.gov/agviewer/content/ag/985235c7-cb95-4be2-8792-a1252b4f8318/list.html"
CYBERATTACKS_JSON_FILE = "cyberattacks.json"

def fetch_webpage(url):
    """Fetch webpage content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Error fetching webpage {url}: {e}")
        return None

def load_cyberattacks_json():
    """Load the local cyberattacks.json file"""
    try:
        if not os.path.exists(CYBERATTACKS_JSON_FILE):
            logger.warning(f"Local {CYBERATTACKS_JSON_FILE} not found, returning empty list")
            return []
            
        with open(CYBERATTACKS_JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing {CYBERATTACKS_JSON_FILE}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading {CYBERATTACKS_JSON_FILE}: {e}")
        return []

def parse_breach_table(html_content):
    """Parse the breach notification table"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Look for the table with the specified class
    table = soup.find('table', class_='breachTable stripe hover dataTable no-footer')
    
    if not table:
        # Fallback: look for any table or div containing breach data
        logger.warning("Specific table class not found, looking for alternative structure")
        # Try to find table rows or data rows
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
            
            # Extract organization name and link
            link_elem = name_cell.find('a')
            if link_elem:
                org_name = link_elem.get_text(strip=True)
                link_href = link_elem.get('href')
                if link_href:
                    # Convert relative URL to absolute
                    full_link = urljoin(MAINE_BREACH_URL, link_href)
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
                
        except Exception as e:
            logger.warning(f"Error parsing row: {e}")
            continue
    
    return breaches

def check_existing_urls(cyberattacks_data, notification_url):
    """Check if notification URL already exists in cyberattacks.json"""
    if not cyberattacks_data:
        return False
        
    for attack in cyberattacks_data:
        if isinstance(attack, dict) and 'url' in attack:
            if attack['url'] == notification_url:
                return True
    return False

def call_extract_pdf(link):
    """Call extract_pdf module with the given link and return extracted data"""
    try:
        logger.info(f"Processing {link}")
        extracted_data = extract_pdf.main(link)
        
        if extracted_data:
            logger.info(f"Successfully processed {link}")
            return extracted_data
        else:
            logger.info(f"No data extracted from {link} (likely filtered out)")
            return None
            
    except Exception as e:
        logger.error(f"Error calling extract_pdf for {link}: {e}")
        return None

def send_telegram_notification(new_notifications):
    """Send Telegram notification about new breach notifications"""
    try:
        bot_token = os.environ.get('TG_TK')
        chat_id = os.environ.get('TG_CHAT_ID')
        
        if not bot_token or not chat_id:
            logger.warning("Telegram bot token or chat ID not found in environment variables")
            return False
        
        # Format message
        message = f"🚨 *Maine Breach Monitor Alert*\n\n"
        message += f"Found {len(new_notifications)} new breach notification(s):\n\n"
        
        for i, notification in enumerate(new_notifications, 1):
            victim = notification.get('victim', 'Unknown')
            date = notification.get('date', 'Unknown')
            url = notification.get('url', '')
            
            message += f"{i}. *{victim}*\n"
            message += f"   Date: {date}\n"
            if url:
                message += f"   URL: {url}\n"
            message += "\n"
        
        message += f"All details saved to `new_notification.json`"
        
        # Send message via Telegram API
        telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(telegram_url, json=payload, timeout=30)
        response.raise_for_status()
        
        logger.info("Successfully sent Telegram notification")
        return True
        
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting Maine breach notification monitor")
    
    # Fetch webpage
    logger.info("Fetching Maine breach notification page")
    html_content = fetch_webpage(MAINE_BREACH_URL)
    if not html_content:
        logger.error("Failed to fetch webpage")
        return 1
    
    # Parse breach table
    logger.info("Parsing breach notification table")
    breaches = parse_breach_table(html_content)
    logger.info(f"Found {len(breaches)} breach notifications")
    
    if not breaches:
        logger.warning("No breaches found - check page structure")
        return 1
    
    # Load existing cyberattacks data
    logger.info("Loading existing cyberattacks.json data")
    cyberattacks_data = load_cyberattacks_json()
    logger.info(f"Loaded {len(cyberattacks_data)} existing cyberattack records")
    
    # Process each breach
    new_breaches = 0
    new_notifications = []
    
    for breach in breaches:
        org_name = breach['organization']
        link = breach['link']
        date = breach['date']
        
        logger.info(f"Checking breach: {org_name} ({date})")
        
        if not link:
            logger.warning(f"No link found for {org_name}")
            continue
        
        # Convert relative URL to absolute URL for comparison
        full_url = urljoin(MAINE_BREACH_URL, link)
        
        # Check if notification URL already exists
        if check_existing_urls(cyberattacks_data, full_url):
            logger.info(f"Notification URL '{full_url}' already exists in cyberattacks.json")
            logger.info("Found already processed notification - stopping processing (assuming chronological order)")
            break
        
        # New breach found
        logger.info(f"New breach found: {org_name}")
        new_breaches += 1
        
        logger.info(f"Processing link: {full_url}")
        extracted_data = call_extract_pdf(full_url)
        if extracted_data:
            logger.info(f"Successfully processed new breach: {org_name}")
            new_notifications.append(extracted_data)
        else:
            logger.info(f"No data extracted for {org_name} (likely filtered out or error)")
    
    # Save new notifications to JSON file
    if new_notifications:
        logger.info(f"Saving {len(new_notifications)} new notifications to new_notification.json")
        with open('new_notification.json', 'w', encoding='utf-8') as f:
            json.dump(new_notifications, f, ensure_ascii=False, indent=4)
        logger.info("Successfully saved new_notification.json")
        
        # Send Telegram notification
        logger.info("Sending Telegram notification")
        send_telegram_notification(new_notifications)
    else:
        logger.info("No new notifications to save")
    
    logger.info(f"Processing complete. Found {new_breaches} new breaches, {len(new_notifications)} saved to file")
    return 0

if __name__ == "__main__":
    sys.exit(main())