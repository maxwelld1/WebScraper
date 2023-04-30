import _thread
import threading

from bs4 import BeautifulSoup
import requests, re

class RequestArticleContentList:
## TODO: WARNING
## ##     NO INFINITE RECURSION

    def crawl_js_load_more(offset_api_call, articles_crawl, session):
        session_lock = threading.Lock()
        ## Interrupt
        with session_lock:
            print("\n\n Threading has Acquired Lock. === ")
            article_list_data = threading.local()
            print("\n\t\t ---Request: Article Content-List - offset: " + offset_api_call)
            article_list_data.response_blog_list = session.get("https://themusicmermaid.com" + offset_api_call + "&format=main-content")

            blog_list = article_list_data.response_blog_list

            soup = BeautifulSoup(blog_list.text, 'html.parser')

            # Qualify the reponse contained the correct blog-list
            if (not soup.find('article')):
                print(" \n\t\t ---Article Content-List --Response Empty " + offset_api_call)
                return
            if (not soup.find("a", class_="load-more")): ## TODO: Move this check outside of Thread Lock?
                print("\n\t\t ---No further Requests for Article page lists. (Offset URL or anchor, load-more not found)\n")
                return

            for article in soup.find_all('article'):
                article_list_data.article_link = article.a

                link = article_list_data.article_link
                # sitemap.append(link.get('href'))
                ## Append Articles -
                articles_crawl.append("https://themusicmermaid.com" + link.get('href'))

        ## Find offset:

        ## Soup the results for load more anchor ##thread local data?
        article_list_data.offset = soup.find("a", class_="load-more").get('href')

        offset_id = article_list_data.offset

        if offset_id:

            offset_id = offset_id.rsplit('/', 1)[
            -1 ].split('&', 1)[-1]

            if re.compile("\?offset=\d+$").search(offset_id): ## Replace __contains__
                RequestArticleContentList.crawl_js_load_more(offset_id, articles_crawl, session)
                return

            print("\n\t\t ---Offset ID is invalid, within hyperlink to load-more.\n") ## Error: offset ID
        print("\n\t\t ---No further Requests for Article page lists. (Offset URL or anchor, load-more not found)\n")

        _thread.exit()