#!/usr/bin/env python3
"""
Unified Breach Notification Monitor
Supports multiple states through pluggable state-specific modules.
Usage: python breach_monitor.py <state>
Where <state> is: maine, washington, vermont
"""

import requests
import json
import sys
import os
import argparse
import logging
from datetime import datetime
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
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

def check_existing_urls(cyberattacks_data, notification_url):
    """Check if notification URL already exists in cyberattacks.json"""
    if not cyberattacks_data:
        return False
        
    for attack in cyberattacks_data:
        if isinstance(attack, dict) and 'url' in attack:
            if attack['url'] == notification_url:
                return True
    return False

def save_notification_to_file(notification, state_name, filename=None):
    """Save a single notification to JSON file, appending to existing data"""
    try:
        # Generate state-specific filename if not provided
        if filename is None:
            filename = f'new_notification_{state_name.lower()}.json'
        
        # Load existing notifications if file exists
        existing_notifications = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_notifications = json.load(f)
                if not isinstance(existing_notifications, list):
                    existing_notifications = []
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Error reading existing {filename}, starting fresh: {e}")
                existing_notifications = []
        
        # Append new notification
        existing_notifications.append(notification)
        
        # Save updated list
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_notifications, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Successfully saved notification to {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving notification to {filename}: {e}")
        return False

def send_telegram_notification(new_notifications, state_name, telegram_prefix):
    """Send Telegram notification about new breach notifications"""
    try:
        bot_token = os.environ.get('TG_TK')
        chat_id = os.environ.get('TG_CHAT_ID')
        
        if not bot_token or not chat_id:
            logger.warning("Telegram bot token or chat ID not found in environment variables")
            return False
        
        # Format message
        message = telegram_prefix
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
        
        message += f"All details saved to `new_notification_{state_name.lower()}.json`"
        
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

def load_state_config(state_name):
    """Load state-specific configuration module"""
    try:
        if state_name.lower() == 'maine':
            from states.maine import MaineConfig
            return MaineConfig
        elif state_name.lower() == 'washington':
            from states.washington import WashingtonConfig
            return WashingtonConfig
        elif state_name.lower() == 'vermont':
            from states.vermont import VermontConfig
            return VermontConfig
        elif state_name.lower() == 'newhampshire':
            from states.newhampshire import NewHampshireConfig
            return NewHampshireConfig
        elif state_name.lower() == 'idaho':
            from states.idaho import IdahoConfig
            return IdahoConfig
        elif state_name.lower() == 'california':
            from states.california import CaliforniaConfig
            return CaliforniaConfig
        elif state_name.lower() == 'iowa':
            from states.iowa import IowaConfig
            return IowaConfig
        else:
            raise ValueError(f"Unsupported state: {state_name}")
    except ImportError as e:
        logger.error(f"Error importing state configuration for {state_name}: {e}")
        return None

def process_state(state_name):
    """Process breach notifications for a single state"""
    logger.info(f"{'='*60}")
    logger.info(f"PROCESSING STATE: {state_name.upper()}")
    logger.info(f"{'='*60}")
    
    # Load state-specific configuration
    state_config = load_state_config(state_name)
    if not state_config:
        logger.error(f"Failed to load state configuration for {state_name}")
        return False
    
    logger.info(f"Starting {state_config.STATE_NAME} breach notification monitor")
    
    # Handle different state data sources
    if state_name.lower() == 'vermont':
        return process_vermont_rss(state_config)
    elif state_name.lower() == 'newhampshire':
        return process_newhampshire_json(state_config)
    else:
        return process_html_table_state(state_config, state_name)

def process_vermont_rss(state_config):
    """Process Vermont's RSS feed"""
    # Fetch RSS feed
    logger.info(f"Fetching {state_config.STATE_NAME} RSS feed")
    rss_content = fetch_webpage(state_config.RSS_URL)
    if not rss_content:
        logger.error("Failed to fetch RSS feed")
        return False
    
    # Parse RSS feed using state-specific parser
    logger.info("Parsing RSS feed")
    rss_items = state_config.parse_rss_feed(rss_content)
    logger.info(f"Found {len(rss_items)} RSS items")
    
    if not rss_items:
        logger.warning("No RSS items found - check RSS feed structure")
        return False
    
    # Load existing cyberattacks data
    logger.info("Loading existing cyberattacks.json data")
    cyberattacks_data = load_cyberattacks_json()
    logger.info(f"Loaded {len(cyberattacks_data)} existing cyberattack records")
    
    # Process each RSS item
    new_breaches = 0
    new_notifications = []
    
    for item in rss_items:
        title = item['title']
        link = item['link']
        pubdate = item['pubdate']
        
        logger.info(f"Checking RSS item: {title} ({pubdate})")
        
        # Check if notification URL already exists
        if check_existing_urls(cyberattacks_data, link):
            logger.info(f"Notification URL '{link}' already exists in cyberattacks.json")
            logger.info("Found already processed notification - stopping processing (assuming chronological order)")
            break
        
        # New breach found
        logger.info(f"New breach found: {title}")
        new_breaches += 1
        
        logger.info(f"Processing link: {link}")
        # Use state-specific processing
        extracted_data = state_config.process_breach(item, fetch_webpage)
        if extracted_data:
            logger.info(f"Successfully processed new breach: {title}")
            new_notifications.append(extracted_data)
            # Save immediately after processing each notification
            save_notification_to_file(extracted_data, state_config.STATE_NAME)
        else:
            logger.info(f"No data extracted for {title} (likely filtered out or error)")
    
    # Send Telegram notification if there are new notifications
    if new_notifications:
        logger.info("Sending Telegram notification")
        telegram_prefix = state_config.get_telegram_message_prefix()
        send_telegram_notification(new_notifications, state_config.STATE_NAME, telegram_prefix)
        logger.info(f"Processing complete. All {len(new_notifications)} notifications have been saved incrementally to new_notification_vermont.json")
    else:
        logger.info("No new notifications found")
    
    logger.info(f"{state_config.STATE_NAME} processing complete. Found {new_breaches} new breaches, {len(new_notifications)} saved to file")
    return True

def process_newhampshire_json(state_config):
    """Process New Hampshire's JSON API"""
    # Fetch JSON API
    logger.info(f"Fetching {state_config.STATE_NAME} JSON API")
    json_content = state_config.fetch_json_api()
    if not json_content:
        logger.error("Failed to fetch JSON API")
        return False
    
    # Parse JSON API using state-specific parser
    logger.info("Parsing JSON API response")
    json_items = state_config.parse_json_api(json_content)
    logger.info(f"Found {len(json_items)} JSON items")
    
    if not json_items:
        logger.warning("No JSON items found - check API response structure")
        return False
    
    # Load existing cyberattacks data
    logger.info("Loading existing cyberattacks.json data")
    cyberattacks_data = load_cyberattacks_json()
    logger.info(f"Loaded {len(cyberattacks_data)} existing cyberattack records")
    
    # Process each JSON item
    new_breaches = 0
    new_notifications = []
    
    for item in json_items:
        title = item['title']
        pdf_url = item['pdf_url']
        date = item['date']
        
        logger.info(f"Checking JSON item: {title} ({date})")
        
        # Check if notification URL already exists
        if check_existing_urls(cyberattacks_data, pdf_url):
            logger.info(f"Notification URL '{pdf_url}' already exists in cyberattacks.json")
            logger.info("Found already processed notification - stopping processing (assuming chronological order)")
            break
        
        # New breach found
        logger.info(f"New breach found: {title}")
        new_breaches += 1
        
        logger.info(f"Processing PDF: {pdf_url}")
        # Use state-specific processing
        extracted_data = state_config.process_breach(item, fetch_webpage)
        if extracted_data:
            logger.info(f"Successfully processed new breach: {title}")
            new_notifications.append(extracted_data)
            # Save immediately after processing each notification
            save_notification_to_file(extracted_data, state_config.STATE_NAME)
        else:
            logger.info(f"No data extracted for {title} (likely filtered out or error)")
    
    # Send Telegram notification if there are new notifications
    if new_notifications:
        logger.info("Sending Telegram notification")
        telegram_prefix = state_config.get_telegram_message_prefix()
        send_telegram_notification(new_notifications, state_config.STATE_NAME, telegram_prefix)
        logger.info(f"Processing complete. All {len(new_notifications)} notifications have been saved incrementally to new_notification_newhampshire.json")
    else:
        logger.info("No new notifications found")
    
    logger.info(f"{state_config.STATE_NAME} processing complete. Found {new_breaches} new breaches, {len(new_notifications)} saved to file")
    return True

def process_html_table_state(state_config, state_name):
    """Process states that use HTML table parsing (Maine, Washington, Idaho, California, Iowa)"""
    # Fetch webpage - handle Iowa's dynamic URL
    if state_name.lower() == 'iowa':
        url = state_config.get_current_year_url()
        logger.info(f"Fetching {state_config.STATE_NAME} breach notification page (year-specific): {url}")
    else:
        url = state_config.URL
        logger.info(f"Fetching {state_config.STATE_NAME} breach notification page")
    
    html_content = fetch_webpage(url)
    if not html_content:
        logger.error("Failed to fetch webpage")
        return False
    
    # Parse breach table using state-specific parser
    logger.info("Parsing breach notification table")
    breaches = state_config.parse_breach_table(html_content)
    logger.info(f"Found {len(breaches)} breach notifications")
    
    if not breaches:
        logger.warning("No breaches found - check page structure")
        return False
    
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
        
        # Convert relative URL to absolute URL for comparison if needed
        if link.startswith('/'):
            full_url = urljoin(state_config.URL, link)
        else:
            full_url = link
        
        # Check if notification URL already exists
        if check_existing_urls(cyberattacks_data, full_url):
            logger.info(f"Notification URL '{full_url}' already exists in cyberattacks.json")
            logger.info("Found already processed notification - stopping processing (assuming chronological order)")
            break
        
        # New breach found
        logger.info(f"New breach found: {org_name}")
        new_breaches += 1
        
        logger.info(f"Processing link: {full_url}")
        # Use state-specific processing
        extracted_data = state_config.process_breach(full_url, fetch_webpage)
        if extracted_data:
            logger.info(f"Successfully processed new breach: {org_name}")
            new_notifications.append(extracted_data)
            # Save immediately after processing each notification
            save_notification_to_file(extracted_data, state_config.STATE_NAME)
        else:
            logger.info(f"No data extracted for {org_name} (likely filtered out or error)")
    
    # Send Telegram notification if there are new notifications
    if new_notifications:
        logger.info("Sending Telegram notification")
        telegram_prefix = state_config.get_telegram_message_prefix()
        send_telegram_notification(new_notifications, state_config.STATE_NAME, telegram_prefix)
        logger.info(f"Processing complete. All {len(new_notifications)} notifications have been saved incrementally to new_notification_{state_name.lower()}.json")
    else:
        logger.info("No new notifications found")
    
    logger.info(f"{state_config.STATE_NAME} processing complete. Found {new_breaches} new breaches, {len(new_notifications)} saved to file")
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Unified breach notification monitor')
    parser.add_argument('state', nargs='?', choices=['maine', 'washington', 'vermont', 'newhampshire', 'idaho', 'california', 'iowa'], 
                       help='State to monitor (if not specified, processes all states)')
    args = parser.parse_args()
    
    # Determine which states to process
    if args.state:
        states_to_process = [args.state]
        logger.info(f"Processing single state: {args.state}")
    else:
        states_to_process = ['maine', 'washington', 'vermont', 'newhampshire', 'idaho', 'california', 'iowa']
        logger.info("No specific state provided - processing all states")
    
    # Process each state
    successful_states = 0
    total_states = len(states_to_process)
    
    for state in states_to_process:
        try:
            success = process_state(state)
            if success:
                successful_states += 1
            else:
                logger.error(f"Failed to process {state}")
        except Exception as e:
            logger.error(f"Error processing {state}: {e}")
    
    # Final summary
    logger.info(f"{'='*60}")
    logger.info(f"FINAL SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Successfully processed {successful_states}/{total_states} states")
    
    if successful_states == total_states:
        logger.info("All states processed successfully!")
        return 0
    else:
        logger.warning(f"{total_states - successful_states} state(s) failed to process")
        return 1

if __name__ == "__main__":
    sys.exit(main())
