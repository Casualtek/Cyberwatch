import argparse
from newspaper import Article

def main(url):
    article = Article(url)
    article.download()
    article.parse()
    news_content = article.text
    return news_content

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze the content of a news story")
    parser.add_argument("url", help="The URL of the webpage to analyze.")
    args = parser.parse_args()
    story = main(args.url)
    print(story)
