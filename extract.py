import os
from newspaper import Article

OPENAI_API_KEY = os.environ['OPENAI_API']
ARTICLE_URL    = os.environ['URL']

def main(url):
    article = Article(url)
    article.download()
    article.parse()
    news_content = article.text
    return news_content

if __name__ == "__main__":
    story = main(ARTICLE_URL)
    print(story)
