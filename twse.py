#!/usr/bin/python3
import json
import os
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta

def post_to_telegram(message):
    chatid         = os.environ['TG_CHAT_ID']
    telegram_token = os.environ['TG_TK']

    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    data = {
        'chat_id': chatid,
        'disable_web_page_preview': False,
        'disable_notification': False,
        'parse_mode':'MarkDown',
        'text': message
    }
    r = requests.post(url, data)
    # check status code
    if r.status_code != 200:
        print(
            f'Error sending Telegram notification ({r.status_code}): {r.content.decode()}')
        return False            
    return True

def main():
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")

    # Données du formulaire
    form_data = {
        "step": "00",
        "RADIO_CM": "1",
        "TYPEK": "sii",
        "PRO_ITEM": "M26",
        "SDATE": yesterday,
        "lang": "EN",
    }

    with sync_playwright() as p:
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        )

        request = p.request.new_context(
            base_url="https://mopsov.twse.com.tw",
            extra_http_headers={
                "User-Agent": user_agent,
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8,fr;q=0.7",
                "Origin": "https://mopsov.twse.com.tw",
                "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Connection": "keep-alive",
                "Dnt": "1",  # Do Not Track (optional)
            }
        )

        response = request.post(
            "/mops/web/ezsearch_query",
            form=form_data,  # Données du formulaire
        )

        if response.status == 200:
            raw_text = response.text()
            data     = json.loads(raw_text.encode("utf-8").decode("utf-8-sig"))
            try:
                if data.get("status") == "success" and "data" in data:
                    announcements = ("--- TWSE Announcements ---\n")
                    for item in data["data"]:
                        announcements += f"📅 Date: {item['CDATE']}\n"
                        announcements += f"🏢 Company: {item['COMPANY_NAME']} ({item['COMPANY_ID']})\n"
                        announcements += f"🔹 Category: {item['CODE_NAME']}\n"
                        announcements += f"📄 Subject: {item['SUBJECT']}\n"
                        announcements += f"🔗 [Link]({item['HYPERLINK']})\n"
                        announcements += "-" * 26
                        announcements += "\n"
                    post_to_telegram(announcements)
                else:
                    print("No relevant data found.")
            except json.JSONDecodeError:
                print("Error: Could not decode JSON response.")
        else:
            print("Request failed.")
  
if __name__ == '__main__':
    main()
