# Cyberwatch
Keeping track of cyberattacks

This project consists in a few Python scripts that help monitor news to discover mentions of cyberattacks in the media around the globe. 

*rss.py* collects news feeds on the topic from Google, removes duplicates, and translates news headlines into English, using DeepL's API.
The resulting RSS feed is ready to consume with your favorite RSS reader. It's frequently updated using GitHub Actions. 
*TODO*: add results from Bing News Search's API. Extend detection of duplicates.

*review-week.py* uses data from *cyberattacks.json* to produce a weekly cyberattacks digest. It's run by GitHub Actions. 

*review-monthly.py* uses data from *cyberattacks.json* to produce a weekly cyberattacks digest. It's run by GitHub Actions.

Now, what's in *cyberattacks.json*?
A set of cyberattacks mentionned in the media and spotted thanks to the meta cyberattacks RSS feed. 
You'll find there the name of the victim, the country, the date, a short description of the situation, and a link to the original news story. 
That data is extracted from the original news story with the help of ChatGPT, using OpenIA's developers API. 
The output is checked manually.

Enjoy and feel free to contribute any improvements ideas!
