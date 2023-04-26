import openai
import os
import json
from datetime import datetime
from newspaper import Article

openai.api_key = os.environ['OPENAI_API']
article_url    = os.environ['URL']

def main(url):
    article = Article(url)
    article.download()
    article.parse()
    news_content = article.text
    return news_content

if __name__ == "__main__":
    story = main(article_url)
    print(story)
