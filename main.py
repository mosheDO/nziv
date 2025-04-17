import feedparser
import json
import time
import os
import article_parser
import asyncio
from telegram import Bot
import requests
from bs4 import BeautifulSoup
from telegraph import Telegraph
from markdownify import markdownify as md


PROCESSED_LINKS_FILE = 'processed_links.json'
TOKEN = ''  # Use token from @BotFather
RSS_FEED_URL = 'https://nziv.net/feed' # Replace with your RSS feed URL
CHANNEL_ID = ''   # Use the username of your target channel (with @)
INSTANT_BOT = '@@chotamreaderbot'

BOT = Bot(token=TOKEN)
telegraph = Telegraph()
telegraph.create_account(short_name='Nziv')
    
    
def fetch_article(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract title and content - adjust these selectors
    title = soup.find('h1').get_text()
    
    # Find the <article> tag
    article = soup.find('article')
    if not article:
        return "No article found."

    # Replace <a> tags with a text representation
    for a in article.find_all('a'):
        link_text = a.get_text(strip=True) or "[link]"
        href = a.get('href')
        a.replace_with(f"{link_text} [{href}]")  # Link text followed by URL

    # Replace <img> tags with a text representation
    for img in article.find_all('img'):
        alt_text = img.get('alt', 'Image')
        img.replace_with(f"[Image: {alt_text}]")  # Image representation

    # Get the plain text from the article
    plain_text = article.get_text(separator="\n", strip=True)


    return title, plain_text


def create_telegra_ph_post(title, content):
    url = 'https://telegra.ph/createPage'
    data = {
        'title': title,
        'author_name': 'Nziv',  # Optional
        'content': [[content]],  # Content needs to be a nested list
        'access': 'public'  # You can set it to 'public', 'private', or 'password'
    }

    response = requests.post(url, data=data)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()['result']['url']  # Return the URL of the created post



def load_processed_links(filename):
    try:
        with open(filename, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_processed_links(filename, processed_links):
    with open(filename, 'w') as f:
        json.dump(list(processed_links), f)

def fetch_new_articles(rss_url, processed_links):
    feed = feedparser.parse(rss_url)
    new_articles = []
    
    for entry in feed.entries:
        if entry.link not in processed_links:
            new_articles.append(entry)
            processed_links.add(entry.link)  # Add to the set
    
    return new_articles


async def send_message(text, chat_id):
    async with BOT:
        await BOT.send_message(text=text, chat_id=chat_id)

      
      
      
def remove_specific_tag(html, tag_to_remove):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find and unwrap the specified tag
    for tag in soup.find_all(tag_to_remove):
        tag.unwrap()  # This removes the tag but keeps its content
    
    return str(soup)

def test():
    
    if os.path.exists(PROCESSED_LINKS_FILE):
        try:
            os.remove(PROCESSED_LINKS_FILE)  # Remove the file
            print(f"Successfully deleted {PROCESSED_LINKS_FILE}")
        except Exception as e:
            print(f"Error deleting file: {e}")
        
  
async def main():
    
    # test()
    processed_links = load_processed_links(PROCESSED_LINKS_FILE)

    # while True:
    new_articles = fetch_new_articles(RSS_FEED_URL, processed_links)
    for article in new_articles:
        article.link = article.link.split('?')[0]
        title, text = fetch_article(article.link)
        markdown_content = md(text)

        # response = telegraph.create_page(
        #     title,
        #     html_content=text
        # )
        # print(response['url'])
        # a = article_parser.parse(url=article.link, output='markdown')
        #     # url='',               # The URL of the article.
        #     # html='',              # The HTML of the article.
        #     # threshold=0.9,        # The ratio of text to the entire document, default 0.9.
        #     # output='html',        # Result output format, support ``markdown`` and ``html``, default ``html``.
        #     # **kwargs              # Optional arguments that `request` takes. optional
        #     # ),
        # response = telegraph.create_page(
        #     title,
        #     content=a
        # )
        # await send_message(chat_id=CHANNEL_ID, text=)
        await send_message(chat_id=CHANNEL_ID, text=article.link)
        # await send_message(chat_id=CHANNEL_ID, text=response['url'])
        print(f"Sent: {title}")  # Log the sent message
    save_processed_links(PROCESSED_LINKS_FILE, processed_links)
        # time.sleep(3600)  # Check for new articles every hour

if __name__ == '__main__':
    asyncio.run(main())
