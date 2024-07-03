#!/usr/bin/python3
import flag
import json
import locale
import os
import requests
import tweepy
from atproto import Client, models
from datetime import datetime
from mastodon import Mastodon

json_file = './assessments.json'

consumer_key =    os.environ['CONS_KEY']
consumer_secret = os.environ['CONS_SECRET']
access_token =    os.environ['ACC_TOKEN']
access_token_secret = os.environ['ACC_TK_SECRET']
bearer_token = os.environ['BEARER_TK']

MASTODON_TOKEN=    os.environ['MAST_TK']
MASTODON_INSTANCE= 'https://infosec.exchange'

def post_to_mastodon(message):
    mastodon = Mastodon(
        access_token = MASTODON_TOKEN,
        api_base_url = MASTODON_INSTANCE
    )
    mastodon.status_post(message, language='fr', visibility='public')

def post_to_telegram(message):
    chatid = os.environ['CHAT_ID']
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

def post_to_twitter(message):
    tweetbot = tweepy.Client(bearer_token, consumer_key, consumer_secret, access_token, access_token_secret)
    tweetbot.create_tweet(text=message)
    
def post_to_bluesky(text):
    client = Client()
    client.login(os.environ['BS_LOGIN'],os.environ['BS_PWD'])
    
    facets = [
        models.models.app.bsky.richtext.facet.Main(
            features=[models.AppBskyRichtextFacet.Link(uri='https://www.ransomware.live/#/recentcyberattacks')],
            # we should pass when our link starts and ends in the text
            # the example below selects all the text
            index=models.AppBskyRichtextFacet.ByteSlice(byte_start=len(text.encode('UTF-8')), byte_end=48+len(text.encode('UTF-8'))),
        )
    ]

    post_with_link_card = client.com.atproto.repo.create_record(
        models.ComAtprotoRepoCreateRecord.Data(
            repo=client.me.did,  # or any another DID
            collection=models.ids.AppBskyFeedPost,
            record=models.AppBskyFeedPost.Record(
                created_at=client.get_current_time_iso(), text=text+'https://www.ransomware.live/#/recentcyberattacks', langs=["fr"], facets=facets
            ),
        )
    )
    
def get_claim(group, victim_name, victim_domain):
    url = 'https://api.ransomware.live/groupvictims/'+group
    headers = {
        'accept': 'application/json'
        }

    response = requests.get(url, headers=headers)
    claims = response.json()
    
    for claim in claims:
        if claim.get("website") == victim_domain or claim.get("post_title") == victim_name:
            claimed = datetime.strptime(claim.get("published"), "%Y-%m-%d %H:%M:%S.%f")
            return(datetime.strftime(claimed, '%d %B %Y'))

def main():
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    story = json_data[0]
    
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    date_obj   = datetime.strptime(story['date'], '%Y-%m-%d')
    date_tweet = date_obj.strftime('%d %B %Y')
    country    = story['country']
    
    date_claim = get_claim(story['group'], story['victim'], story['domain'])

    tweet = '📆 la #cyberattaque revendiquée le '+date_claim+' ('+story['group']+') contre '+flag.flag(country)+' '+story['victim']+' ('+story['domain']+')'+' semble survenue ~'+date_tweet+' 🧐'
    post_to_twitter(tweet)
    post_to_telegram(tweet)
    post_to_mastodon(tweet)
    post_to_bluesky(tweet)
    
#    discord_msg = flag.flag(countryISO[country])+' '+story['victim']+' a été victime d\'une cyberattaque autour du '+date_tweet+'.\n👉 '+story['url']
#    post_to_discord(webhook_url, discord_msg)

if __name__ == '__main__':
    main()
