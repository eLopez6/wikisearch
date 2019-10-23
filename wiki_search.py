from flask import Flask, jsonify
import requests
import pprint
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

API_WIKIPEDIA_URL = 'https://en.wikipedia.org/w/api.php'
WIKIPEDIA_URL = "https://en.wikipedia.org"
SEARCH_RESULT = 0

def __find_related_articles(page_content):
    """Find the articles within the disambiguation page."""
    article_links = []

    link_area = page_content.find("div", {"class" : "mw-parser-output"})

    links = link_area.find_all("li", class_=None)

    for link in links:
        article = __find_article_within_link(link)
        if article is not None:
            article_links.append(article)

    return article_links


def __find_article_within_link(link):
    """Extract the article from the page."""
    if __full_article_reference(link.__str__()):
        href = link.find_next("a", href=True)
        print(WIKIPEDIA_URL + href['href'])
        return WIKIPEDIA_URL + href['href']


def __full_article_reference(point):
    """
    Validate that the item referenced is an article, and not a submember of another article.

    On a dismabiguation page, you might see things like 'Church, a cat in Stephen King's novel Pet Sematary'.
    However, this Church does not have an article, _Pet Sematary_ does. Thus, it should not be included. 

    The simplest way to determine if the topic being disambiguated is an article is to look for a link. 
    """
    return point[:6][4:] == "<a"


@app.route('/', subdomain = "<search_term>")
def search(search_term):
    """Perform the Wikipedia search."""
    request_params = {
        'action'   : 'query',
        'list'     : 'search',
        'srsearch' : search_term,
        'format'   : 'json'
    }

    # Getting several articles
    response = requests.get(API_WIKIPEDIA_URL, request_params)

    if response.status_code != 200:
        return("failed to query wikipedia search")
    
    response = response.json()
    search_result_dict = response['query']['search'][SEARCH_RESULT]

    formatted_title = search_result_dict['title'].replace(" ", "_")

    page_url = WIKIPEDIA_URL + '/wiki/' + formatted_title
    soup = BeautifulSoup(requests.get(page_url).content, 'html.parser')

    links_json = {"links" : []}

    # There will be multiple links if it's a disambiguation page...
    if "(disambiguation)" in page_url or soup.find("table", {"id" : "disambigbox"}) is not None:
        links_json["links"].extend(__find_related_articles(soup))
    else:
        # not a disambiguation
        links_json["links"].append(page_url)

    # return (json.dumps(links_json))
    return jsonify(links_json)


if __name__ == "__main__":
    website_url = 'localhost:8080'
    app.config['SERVER_NAME'] = website_url
    app.run()
