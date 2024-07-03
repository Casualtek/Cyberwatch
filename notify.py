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

json_file = './cyberattacks.json'

consumer_key =    os.environ['CONS_KEY']
consumer_secret = os.environ['CONS_SECRET']
access_token =    os.environ['ACC_TOKEN']
access_token_secret = os.environ['ACC_TK_SECRET']
bearer_token = os.environ['BEARER_TK']

MASTODON_TOKEN=    os.environ['MAST_TK']
MASTODON_INSTANCE= 'https://infosec.exchange'

countryISO = {
    'AFG' : 'AF', 'ALA' : 'AX', 'ALB' : 'AL', 'DZA' : 'DZ', 'ASM' : 'AS', 'AND' : 'AD', 'AGO' : 'AO', 'AIA' : 'AI', 'ATA' : 'AQ', 'ATG' : 'AG', 'ARG' : 'AR', 'ARM' : 'AM', 'ABW' : 'AW', 'AUS' : 'AU', 'AUT' : 'AT', 'AZE' : 'AZ', 'BHS' : 'BS', 'BHR' : 'BH', 'BGD' : 'BD', 'BRB' : 'BB', 'BLR' : 'BY', 'BEL' : 'BE', 'BLZ' : 'BZ', 'BEN' : 'BJ', 'BMU' : 'BM', 'BTN' : 'BT', 'BOL' : 'BO', 'BES' : 'BQ', 'BIH' : 'BA', 'BWA' : 'BW', 'BVT' : 'BV', 'BRA' : 'BR', 'VGB' : 'VG', 'IOT' : 'IO', 'BRN' : 'BN', 'BGR' : 'BG', 'BFA' : 'BF', 'BDI' : 'BI', 'KHM' : 'KH', 'CMR' : 'CM', 'CAN' : 'CA', 'CPV' : 'CV', 'CYM' : 'KY', 'CAF' : 'CF', 'TCD' : 'TD', 'CHL' : 'CL', 'CHN' : 'CN', 'HKG' : 'HK', 'MAC' : 'MO', 'CXR' : 'CX', 'CCK' : 'CC', 'COL' : 'CO', 'COM' : 'KM', 'COG' : 'CG', 'COD' : 'CD', 'COK' : 'CK', 'CRI' : 'CR', 'CIV' : 'CI', 'HRV' : 'HR', 'CUB' : 'CU', 'CUW' : 'CW', 'CYP' : 'CY', 'CZE' : 'CZ', 'DNK' : 'DK', 'DJI' : 'DJ', 'DMA' : 'DM', 'DOM' : 'DO', 'ECU' : 'EC', 'EGY' : 'EG', 'SLV' : 'SV', 'GNQ' : 'GQ', 'ERI' : 'ER', 'EST' : 'EE', 'ETH' : 'ET', 'FLK' : 'FK', 'FRO' : 'FO', 'FJI' : 'FJ', 'FIN' : 'FI', 'FRA' : 'FR', 'GUF' : 'GF', 'PYF' : 'PF', 'ATF' : 'TF', 'GAB' : 'GA', 'GMB' : 'GM', 'GEO' : 'GE', 'DEU' : 'DE', 'GHA' : 'GH', 'GIB' : 'GI', 'GRC' : 'GR', 'GRL' : 'GL', 'GRD' : 'GD', 'GLP' : 'GP', 'GUM' : 'GU', 'GTM' : 'GT', 'GGY' : 'GG', 'GIN' : 'GN', 'GNB' : 'GW', 'GUY' : 'GY', 'HTI' : 'HT', 'HMD' : 'HM', 'VAT' : 'VA', 'HND' : 'HN', 'HUN' : 'HU', 'ISL' : 'IS', 'IND' : 'IN', 'IDN' : 'ID', 'IRN' : 'IR', 'IRQ' : 'IQ', 'IRL' : 'IE', 'IMN' : 'IM', 'ISR' : 'IL', 'ITA' : 'IT', 'JAM' : 'JM', 'JPN' : 'JP', 'JEY' : 'JE', 'JOR' : 'JO', 'KAZ' : 'KZ', 'KEN' : 'KE', 'KIR' : 'KI', 'PRK' : 'KP', 'KOR' : 'KR', 'KWT' : 'KW', 'KGZ' : 'KG', 'LAO' : 'LA', 'LVA' : 'LV', 'LBN' : 'LB', 'LSO' : 'LS', 'LBR' : 'LR', 'LBY' : 'LY', 'LIE' : 'LI', 'LTU' : 'LT', 'LUX' : 'LU', 'MKD' : 'MK', 'MDG' : 'MG', 'MWI' : 'MW', 'MYS' : 'MY', 'MDV' : 'MV', 'MLI' : 'ML', 'MLT' : 'MT', 'MHL' : 'MH', 'MTQ' : 'MQ', 'MRT' : 'MR', 'MUS' : 'MU', 'MYT' : 'YT', 'MEX' : 'MX', 'FSM' : 'FM', 'MDA' : 'MD', 'MCO' : 'MC', 'MNG' : 'MN', 'MNE' : 'ME', 'MSR' : 'MS', 'MAR' : 'MA', 'MOZ' : 'MZ', 'MMR' : 'MM', 'NAM' : 'NA', 'NRU' : 'NR', 'NPL' : 'NP', 'NLD' : 'NL', 'ANT' : 'AN', 'NCL' : 'NC', 'NZL' : 'NZ', 'NIC' : 'NI', 'NER' : 'NE', 'NGA' : 'NG', 'NIU' : 'NU', 'NFK' : 'NF', 'MNP' : 'MP', 'NOR' : 'NO', 'OMN' : 'OM', 'PAK' : 'PK', 'PLW' : 'PW', 'PSE' : 'PS', 'PAN' : 'PA', 'PNG' : 'PG', 'PRY' : 'PY', 'PER' : 'PE', 'PHL' : 'PH', 'PCN' : 'PN', 'POL' : 'PL', 'PRT' : 'PT', 'PRI' : 'PR', 'QAT' : 'QA', 'REU' : 'RE', 'ROU' : 'RO', 'RUS' : 'RU', 'RWA' : 'RW', 'BLM' : 'BL', 'SHN' : 'SH', 'KNA' : 'KN', 'LCA' : 'LC', 'MAF' : 'MF', 'SPM' : 'PM', 'VCT' : 'VC', 'WSM' : 'WS', 'SMR' : 'SM', 'STP' : 'ST', 'SAU' : 'SA', 'SEN' : 'SN', 'SRB' : 'RS', 'SYC' : 'SC', 'SLE' : 'SL', 'SGP' : 'SG', 'SXM' : 'SX', 'SVK' : 'SK', 'SVN' : 'SI', 'SLB' : 'SB', 'SOM' : 'SO', 'ZAF' : 'ZA', 'SGS' : 'GS', 'SSD' : 'SS', 'ESP' : 'ES', 'LKA' : 'LK', 'SDN' : 'SD', 'SUR' : 'SR', 'SJM' : 'SJ', 'SWZ' : 'SZ', 'SWE' : 'SE', 'CHE' : 'CH', 'SYR' : 'SY', 'TWN' : 'TW', 'TJK' : 'TJ', 'TZA' : 'TZ', 'THA' : 'TH', 'TLS' : 'TL', 'TGO' : 'TG', 'TKL' : 'TK', 'TON' : 'TO', 'TTO' : 'TT', 'TUN' : 'TN', 'TUR' : 'TR', 'TKM' : 'TM', 'TCA' : 'TC', 'TUV' : 'TV', 'UGA' : 'UG', 'UKR' : 'UA', 'ARE' : 'AE', 'GBR' : 'GB', 'USA' : 'US', 'UMI' : 'UM', 'URY' : 'UY', 'UZB' : 'UZ', 'VUT' : 'VU', 'VEN' : 'VE', 'VNM' : 'VN', 'VIR' : 'VI', 'WLF' : 'WF', 'ESH' : 'EH', 'YEM' : 'YE', 'ZMB' : 'ZM', 'ZWE' : 'ZW', 'XKX' : 'XK'
}

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
    
def post_to_bluesky(text,url):
    client = Client()
    client.login(os.environ['BS_LOGIN'],os.environ['BS_PWD'])
    
    embed_external = models.app.bsky.embed.external.Main(
        external=models.AppBskyEmbedExternal.External(
            title='Source',
            description='',
            uri=url,
        )
    )

    facets = [
        models.app.bsky.richtext.facet.Main(
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
                created_at=client.get_current_time_iso(), text=text+'https://www.ransomware.live/#/recentcyberattacks', embed=embed_external, langs=["fr"], facets=facets
            ),
        )
    )

def main():
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    story = json_data[0]
    
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    date_obj   = datetime.strptime(story['date'], '%Y-%m-%d')
    date_tweet = date_obj.strftime('%d %B %Y')
    country    = story['country']

    telegram_msg = flag.flag(countryISO[country])+' '+story['victim']+' ('+story['domain']+')'+' a été victime d\'une cyberattaque autour du '+date_tweet+'.\n\n'+story['summary']+'\n\n👉 [source]('+story['url']+')'
    post_to_telegram(telegram_msg)

    mastodon_msg = flag.flag(countryISO[country])+' '+story['victim']+' ('+story['domain']+')'+' a été victime d\'une cyberattaque autour du '+date_tweet+'.\n\n'+story['summary']+'\n\n👉 '+story['url']
    post_to_mastodon(mastodon_msg)

    tweet = flag.flag(countryISO[country])+' '+story['victim']+' ('+story['domain']+')'+' a été victime d\'une #cyberattaque autour du '+date_tweet+'.\n⏭️ https://t.ly/t23z2\n👉 '+story['url']+' cc @ransomwaremap @cyber_etc'
    post_to_twitter(tweet)

    post = flag.flag(countryISO[country])+' '+story['victim']+' ('+story['domain']+')'+' a été victime d\'une cyberattaque autour du '+date_tweet+'.\n👉 '
    post_to_bluesky(post,story['url'])

if __name__ == '__main__':
    main()
