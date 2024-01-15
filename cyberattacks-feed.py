#!/usr/bin/python3
import json
import locale
from datetime import datetime
from feedgenerator import Rss201rev2Feed
 
# Load data from JSON file
with open('cyberattacks.json', 'r') as f:
    data = json.load(f)
 
# Create a new RSS feed
feed = Rss201rev2Feed(
    title="Cyberattaques | Casualtek",
    link="https://raw.githubusercontent.com/Casualtek/Cyberwatch/main/cyberattaques.xml",
    language="fr",
    description="Flux RSS de suivi, en Français, des cyberattaques rapportées dans la presse internationale. Maintenu par Valéry Rieß-Marchive (LeMagIT).", )

locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
sorted_items = sorted(data, key=lambda x: x['date'], reverse=True)

# Add items to the feed
for item in sorted_items[:20]:
    date = datetime.strptime(item['date'], '%Y-%m-%d')
    feed.add_item(
        title=item['victim']+' ('+item['country']+') autour du '+date.strftime('%d %B %Y')+'.',
        link=item['url'],
        description=item['summary'],
    )

# Write the feed to a file
with open('cyberattaques.xml', 'w') as f:
    feed.write(f, 'utf-8')
