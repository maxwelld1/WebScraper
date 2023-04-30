import threading
import time

from bs4 import BeautifulSoup
import requests, re
import shutil
import os.path

from Request_Offset_articles import RequestArticleContentList

class WebScraper:

    def original_htmldoc(url, s):
        ## Set Cookie header
        cookies = s.cookies.get_dict()

        if 'crumb' in cookies:
            cookie_crumb = cookies['crumb']
            WebScraper.cookie_crumb = cookie_crumb
            print("Crumb cookie+" + cookie_crumb)

        # request_app_cookie = ""
        if 'ss_cvr' in cookies:
            print("ss_cvr=" + cookies['ss_cvr'])

        if 'ss_cvt' in cookies:
            print("ss_cvt=" + cookies['ss_cvt'])
        # s.headers.update({'cookie': 'crumb='+str(cookie_crumb)+';'+str(request_app_cookie)})
        if 'Path' in cookies:
            print("Path=" + cookies['Path'])

        response = s.get(url)  ## the get inbuilt function is used to send access request to the url
        # response = s.cookies.add_cookie_header(requests.Request('GET', url))

        WebScraper.page_status_unchanged = (response.status_code == 304)
        WebScraper.too_many_req = (response.status_code == 429)

        return response.text  ## text function is used to retrieve the text from the response

    def comments_json(articleno, data_item_id, s):
        print("Requesting comments for Article " + str(articleno) +
              " Remote Addr. - https://www.themusicmermaid.com/api/comment/GetComments?crumb="
              +str(WebScraper.cookie_crumb)+"&targetId="+str(data_item_id)+"&targetType=1&page=1")
        response = s.get("https://www.themusicmermaid.com/api/comment/GetComments?crumb="+str(WebScraper.cookie_crumb)+"&targetId="+str(data_item_id)+"&targetType=1&page=1")
        with open(os.path.join("comments", "article" + str(articleno) + "_comments.json"), "w",
                  encoding='utf-8') as file:
            file.write(response.text)
        print("Comments saved, ---\n")


    def download_image(data_url, s):
        response = s.get(data_url, headers=WebScraper.headers_impersonate_ua, stream=True)
        WebScraper.too_many_req = (response.status_code == 429)
        return response  ## Stream from the response

    def download_audio(data_url, s):
        response = s.get(data_url, headers=WebScraper.headers_impersonate_ua, stream=True)
        WebScraper.too_many_req = (response.status_code == 429)
        return response  ## Stream from the response

    def convert_rel_link_struc(link, s):
        global sitemap
        return

    def crawl_nav_pages(links, navigation_titles,  s):
        for nav_orderno, site_page in enumerate(links):
            if os.path.isfile(os.path.join("navigation", str(navigation_titles[nav_orderno]) + "_page.html")):
                print("Web Page found on filesystem: " + "\navigation\\" + str(navigation_titles[nav_orderno]) + "_page.html")
                with open(os.path.join("navigation", str(navigation_titles[nav_orderno]) + "_page.html"), 'r',
                          encoding='utf-8') as file:  ## mismatch article no.
                    nav_page_html = file.read()
                    soup = BeautifulSoup(nav_page_html, 'html.parser')
                    file.close()
                print("Navigation \"" + str(
                    navigation_titles[nav_orderno]) + "\" --- Finished Crawling, downloaded resources. Wait 3 ...\n")  ## No images, links, audio found???
                continue

            nav_page_html = WebScraper.original_htmldoc(site_page, s)  ## TODO: due to order, new article pages don't get their images DL (or anything else after Download)
            print("Page Retrieval for Site page (navigation link) " + str(navigation_titles[nav_orderno]) + " Remote Addr. - " + str(site_page))
            if WebScraper.too_many_req:
                print("bad page too many req. Wait 3...")
                time.sleep(3)
                continue

            print("--REQUEST Complete,", end=" ")
            soup = BeautifulSoup(nav_page_html, 'html.parser')
            WebScraper.dl_flag = True
            if (WebScraper.page_status_unchanged != True | WebScraper.dl_flag) & (not WebScraper.too_many_req):
                with open(os.path.join("navigation", str(navigation_titles[nav_orderno]) + "_page.html"), "w",
                          encoding='utf-8') as file:
                    file.write(str(soup))
                print("page saved, ---", end=" ")
            print("\""+str(navigation_titles[nav_orderno]) + "\" --- Finished Crawling, downloaded resources. Wait 3 ...\n")

    def crawl_article_pages(links, s):

        for page_disp_orderno, link in enumerate(links):

            images = []
            cdn_links = []
            audio_embedded = []
            ##rel_path_to_article = convert_rel_link_struc(link)

            if os.path.isfile(os.path.join("home", "article" + str(page_disp_orderno) + "_page.html")):
                print("Article found on filesystem: " + "\home\\article" + str(page_disp_orderno) + "_page.html")
                with open(os.path.join("home", "article" + str(page_disp_orderno) + "_page.html"), 'r',
                          encoding='utf-8') as file:  ## mismatch article no.
                    article_html = file.read()
                    soup = BeautifulSoup(article_html, 'html.parser')
                    file.close()


                page_id = soup.find("div", class_="blog-wrapper").get("data-item-id")

                ## Qualify Page
                if soup.find("section", class_="blog-item-comments"):
                    print("Comments found")
                    ## Differing internal structure ## SOundcloud Links

                    if soup.find("div", class_="blog-item-banner-image"):
                        print("blog item - banner image found")
                        article_banner_img = soup.find("div", class_="blog-item-banner-image").img
                        images.append(article_banner_img)

                        image_title = article_banner_img.get('data-image').rsplit('/', 1)[
                            -1]  ## Matching data types MIME (Jpegs, .png - other resources CDN)

                        img_filename = os.path.join("images", os.path.splitext(image_title)[0] + ".jpg")

                        if os.path.isfile(img_filename):
                            print("Image found on local filesystem: " + "\images\\" + img_filename)
                            WebScraper.dl_flag = False
                        else:
                            WebScraper.dl_flag = True
                        if (WebScraper.dl_flag):  ## TODO: don't allow multiple methods flag setting
                            print(" \-- Making request for image:" + article_banner_img.get('data-image'))
                            image_res = WebScraper.download_image(article_banner_img.get('data-image'), s)
                            if (WebScraper.too_many_req):  ## TODO: Change this Exception handling.  Request x 2
                                time.sleep(6)
                                print(" \-- Making request for image:" + article_banner_img.get('data-image'))
                                image_res = WebScraper.download_image(article_banner_img.get('data-image'), s)


                            ## Output image to FIle
                            # TODO: Safe copy, w.o. overwrites. Using different filetypes (default is save image response, raw data as jpg)
                            with open(os.path.join(img_filename), 'wb') as out_file:  # TODO: Rest of filetypes / MIME type
                                if WebScraper.too_many_req != True:
                                    shutil.copyfileobj(image_res.raw, out_file)
                            del image_res

                        ## TODO: Ret. Cookie, Request banner image,
                        ## Check CDN domain:
                        if (str(article_banner_img.get('data-image')).__contains__("cdn")):
                            cdn_links.append(article_banner_img.get('data-image'))
                        print(" (CDN Link):    |" + article_banner_img.get('data-image') + "\n\n")

                    ## TODO: Check MP3s ## TODO: refactor logic, checks for both new and local page
                    if soup.find("div", class_="sqs-audio-embed"):

                        for audio_clip in soup.find_all("div", class_="sqs-audio-embed"):

                            article_sqs_audio = audio_clip
                            audio_embedded.append(article_sqs_audio)

                            recording_title = str(article_sqs_audio.get('data-title')).replace('"', '\'') ## Replacing double quotes
                            recording_title= recording_title.replace(':', '')
                            recording_title= recording_title.replace('/', '')

                            recording_title= recording_title.replace('\\', '')

                            recording_title= recording_title.replace('|', '')

                            recording_title= recording_title.replace('?', '')

                            recording_title= recording_title.replace('*', '')
                            print("audio - Squarespace audio found in page")

                            audio_filename = os.path.join("audio", recording_title + ".mp3")
                            print("audio title: " + recording_title + "  audio filename: "+audio_filename)
                            if os.path.isfile(audio_filename):
                                print("MP3 file found on local filesystem: " + "\\audio\\" + audio_filename)
                                WebScraper.dl_flag = False
                            else:
                                WebScraper.dl_flag = True
                            if (WebScraper.dl_flag):  ## TODO: don't allow multiple methods flag setting
                                print(" \-- Making request for mp3 file:" + article_sqs_audio.get('data-url'))
                                audio_in_res = WebScraper.download_audio(article_sqs_audio.get('data-url'), s)  ## audio/mpeg
                                if (WebScraper.too_many_req):  ## TODO: Change this Exception handling.  Request x 2
                                    time.sleep(6)
                                    print(" \-- Making request for mp3 file:" + article_sqs_audio.get('data-url'))
                                    audio_in_res = WebScraper.download_audio(article_sqs_audio.get('data-url'), s)

                                ## Output recording to FIle
                                # TODO: Safe copy, w.o. overwrites. Using different filetypes (default is save image response, raw data as jpg)
                                with open(os.path.join(audio_filename),
                                          'wb') as out_file:  # TODO: Rest of filetypes / MIME type
                                    if WebScraper.too_many_req != True:
                                        shutil.copyfileobj(audio_in_res.raw, out_file)
                                del audio_in_res

                        ## if (soup.find("img", "stop at related tag")):
                        ## if (str(img.get('data-image')).__contains__("cdn"))
                        ## cdn_links.append(article_banner_img.get('data-image'))

                        ## Check CDN domain:
                            if (str(article_sqs_audio.get('data-url')).__contains__("static1")):
                                cdn_links.append(article_sqs_audio.get('data-url'))
                            print(" (CDN Link - static1.squarespace):    |" + article_sqs_audio.get('data-url') + "\n\n")
                    # ## <img's
                    # images = soup.find_all('img')
                    # if (images.len != 0):
                    # for image in images:

                    ## Exclude related post images
                    ## id = releated
                    # ##  = soup.find("section", id="RelatedPostImages")

                    ## Exclude Latest Post images
                    ## latest =

                    ## TODO: Check Soundcloud domain, YouTube

                    ## all images
                    for image_element in soup.find_all('img'):
                        print("\n\t IMAGE link found -", end=" ")
                        if (image_element.text.__contains__("summary-thumbnail-image") | image_element.text.__contains__("blog-item-banner-image")):  ## Class, ignore
                            print("summary image or original blog-item-banner, ignore...")
                        else:

                            image_link = image_element.get('data-image')
                            if (not image_link):
                                image_link = image_element.get('src')
                            if (not image_link):
                                print("image download failed (no src or data-image attribute), ignore...") ## TODO: Never gets called
                                continue
                            image_title = image_link.rsplit('/', 1)[
                                -1]


                            img_filename = os.path.join("images", os.path.splitext(image_title)[0] + ".jpg")

                            if os.path.isfile(img_filename):
                                print("Image found on local filesystem: " + "\images\\" + img_filename)
                                WebScraper.dl_flag = False
                            else:
                                WebScraper.dl_flag = True
                            if (WebScraper.dl_flag):
                                print(" \-- Making request for image: " + str(image_link))
                                image_res = WebScraper.download_image(str(image_link), s)
                                if (WebScraper.too_many_req):
                                    time.sleep(6)
                                    print(" \-- Making request for image: " + str(image_link))
                                    image_res = WebScraper.download_image(str(image_link), s)

                                ## Output image to FIle
                                with open(os.path.join(img_filename),
                                          'wb') as out_file:
                                    if WebScraper.too_many_req != True:
                                        shutil.copyfileobj(image_res.raw, out_file)
                                del image_res

                            ## Request any images
                            ## Check CDN domain:
                            if (str(image_link).__contains__("cdn")):
                                cdn_links.append(image_link)
                            print(" (CDN Link):    |" + str(image_link) + "\n\n")



                    WebScraper.dl_flag = False
                    if (WebScraper.dl_flag):
                        WebScraper.comments_json(page_disp_orderno, page_id, s) ## TODO: refactor logic, checks for both new and local page


                print("Article " + str(
                        page_disp_orderno) + " --- Finished Crawling, downloaded resources.\n")  ## No images, links, audio found???
                continue ## Continue is only at the end, after all items found and saved.

            article_html = WebScraper.original_htmldoc(link, s)    ## TODO: due to order, new article pages don't get their images DL (or anything else after Download)
            print("Page Retrieval for Article " + str(page_disp_orderno) + " Remote Addr. - " + str(link))
            if WebScraper.too_many_req:
                print("bad page too many req. Wait 3...")
                time.sleep(3)
                continue

            print("--REQUEST Complete,", end=" ")
            soup = BeautifulSoup(article_html, 'html.parser')
            WebScraper.dl_flag = True
            if (WebScraper.page_status_unchanged != True | WebScraper.dl_flag) & (not WebScraper.too_many_req):
                with open(os.path.join("home", "article" + str(page_disp_orderno) + "_page.html"), "w",
                          encoding='utf-8') as file:
                    file.write(str(soup))
                print("page saved, ---", end=" ")

            print("Qualify HTML page - comments:")
            ## Qualify Page - for newly requested working page.  ## Throw exception?
            if soup.find("section", class_="blog-item-comments"):
                print("\tComments found")
                ## Differing internal structure ## SOundcloud Links

                print("Qualify HTML page - banner_image:")
                if soup.find("div", class_="blog-item-banner-image"):
                    print("\tblog item - banner image found")
                    article_banner_img = soup.find("div", class_="blog-item-banner-image").img
                    images.append(article_banner_img)

                    image_title = article_banner_img.get('data-image').rsplit('/', 1)[
                        -1]  ## Matching data types MIME (Jpegs, .png - other resources CDN)

                    img_filename = os.path.join("images", os.path.splitext(image_title)[0] + ".jpg")

                    if os.path.isfile(img_filename):
                        print("Image found on local filesystem: " + "\images\\" + img_filename)
                        WebScraper.dl_flag = False
                    else:
                        WebScraper.dl_flag = True
                    if (WebScraper.dl_flag):  ## TODO: don't allow multiple methods flag setting
                        print(" \-- Making request for image:" + article_banner_img.get('data-image'))
                        image_res = WebScraper.download_image(article_banner_img.get('data-image'), s)
                        if (WebScraper.too_many_req):  ## TODO: Change this Exception handling.  Request x 2
                            time.sleep(6)
                            print(" \-- Making request for image:" + article_banner_img.get('data-image'))
                            image_res = WebScraper.download_image(article_banner_img.get('data-image'), s)

                        ## Output image to FIle
                        # TODO: Safe copy, w.o. overwrites. Using different filetypes (default is save image response, raw data as jpg)
                        with open(os.path.join(img_filename), 'wb') as out_file:  # TODO: Rest of filetypes / MIME type
                            if WebScraper.too_many_req != True:
                                shutil.copyfileobj(image_res.raw, out_file)
                        del image_res

                    ## TODO: Ret. Cookie, Request banner image,
                    ## Check CDN domain:
                    if (str(article_banner_img.get('data-image')).__contains__("cdn")):
                        cdn_links.append(article_banner_img.get('data-image'))
                    print(" (CDN Link):    |" + article_banner_img.get('data-image') + "\n\n")

                ## TODO: Doubles audio snippets
                if soup.find("div", class_="sqs-audio-embed"):
                    print("audio - Squarespace audio found in page")
                    article_sqs_audio = soup.find("div", class_="sqs-audio-embed")
                    audio_embedded.append(article_sqs_audio)

                    recording_title = str(article_sqs_audio.get('data-title')).replace('"', '\'')  ## Replacing double quotes
                    recording_title = recording_title.replace(':', '')
                    recording_title = recording_title.replace('/', '')

                    recording_title = recording_title.replace('\\', '')

                    recording_title = recording_title.replace('|', '')

                    recording_title = recording_title.replace('?', '')

                    recording_title = recording_title.replace('*', '')

                    print("audio title: "+recording_title)
                    audio_filename = os.path.join("audio", recording_title + ".mp3")
                    if os.path.isfile(audio_filename):
                        print("MP3 file found on local filesystem: " + "\\audio\\" + audio_filename)
                        WebScraper.dl_flag = False
                    else:
                        WebScraper.dl_flag = True
                    if (WebScraper.dl_flag):  ## TODO: don't allow multiple methods flag setting
                        print(" \-- Making request for mp3 file:" + article_sqs_audio.get('data-url'))
                        audio_in_res = WebScraper.download_audio(article_sqs_audio.get('data-url'), s)  ## audio/mpeg
                        if (WebScraper.too_many_req):  ## TODO: Change this Exception handling.  Request x 2
                            time.sleep(6)
                            print(" \-- Making request for mp3 file:" + article_sqs_audio.get('data-url'))
                            audio_in_res = WebScraper.download_audio(article_sqs_audio.get('data-url'), s)

                        ## Output recording to FIle
                        # TODO: Safe copy, w.o. overwrites. Using different filetypes (default is save image response, raw data as jpg)
                        with open(os.path.join(audio_filename),
                                  'wb') as out_file:  # TODO: Rest of filetypes / MIME type
                            if WebScraper.too_many_req != True:
                                shutil.copyfileobj(audio_in_res.raw, out_file)
                        del audio_in_res
                    ## all images
                    ## if (soup.find("img", "stop at related tag")):
                    ## if (str(img.get('data-image')).__contains__("cdn"))
                    ## cdn_links.append(article_banner_img.get('data-image'))

                    ## Check CDN domain:
                    if (str(article_banner_img.get('data-image')).__contains__("static1")):
                        cdn_links.append(article_sqs_audio.get('data-url'))
                    print(" (CDN Link - static1.squarespace):    |" + article_sqs_audio.get('data-url') + "\n\n")


                print("Article " + str(
                    page_disp_orderno) + " --- Finished Crawling, downloaded resources. Wait 3 ...\n")  ## No images, links, audio found???
                time.sleep(3)
                continue   ## needed?



    def crawl_site(homepage_url, s):
        html_doc = WebScraper.original_htmldoc(homepage_url, s)
        time.sleep(2.5)

        soup = BeautifulSoup(html_doc, 'html.parser')

        ## links, elements - specific site pages. find them based on other attrs? ID article page, meta tag?

        ## Grab entry text, icons & date.
        ## Grab and transform CSS? Grab CSS, extract style and apply to my html?
        ## Verify sitemap relative paths
        ## URLs
        ##for link in soup.find_all('a', attrs={'href': re.compile(".*/home")}):  ## findall is used to obtain a list of various hyperlinks in the mentioned web page in form of a list

        # Searching data
        titles = []
        thumbnail_imgs = []
        links = []
        ## /?offset=1605976748698
        offset_id_load_more_content = 0


        ## Check if html file exists locally
        if (WebScraper.page_status_unchanged != True): ## TODO: Expand this check Homepage
            with open("home_page.html", "w", encoding='utf-8') as file:
                file.write(str(soup))
        ## elif: ## dos not contain links ## Check sshould occurring on local orig. doc
        ## different internal structure

        offset_id_load_more_content = soup.find("a", class_="load-more").get('href').rsplit('/', 1)[
            -1 ].split('&', 1)[-1]

        print("Starting javascript request thread: (load more)")
        threading.Thread(target=RequestArticleContentList.crawl_js_load_more, args=(offset_id_load_more_content,
                                                                                    links, s)).start()
        ## Find Articles
        for article in soup.find_all('article'):
            link = article.a
            # sitemap.append(link.get('href'))
            links.append("https://themusicmermaid.com" + link.get('href'))  ## shouldn't be hardcoded
            thumb_img = link.img
            thumbnail_imgs.append(thumb_img.get('data-src'))

            title = link.find_next("a").get_text()  ## grabs date from child time tag
            titles.append(title)

        WebScraper.crawl_article_pages(links, s)  ## Request Pages


        navigation_links = ["https://www.themusicmermaid.com/soundtrack-to-my-life"]
        nav_titles = ["Soundtrack_to_my_life"]
        navigation_links.append("https://www.themusicmermaid.com/sound-support")
        nav_titles.append("Sound_support")

        navigation_links.append("https://www.themusicmermaid.com/new-events")
        nav_titles.append("New_events")

        navigation_links.append("https://www.themusicmermaid.com/music-we-love-your-turn")
        nav_titles.append("Music_we_love_your_turn")

        navigation_links.append("https://www.themusicmermaid.com/why-people-love-the-music-mermaid")  ## TODO: Images revieww!
        nav_titles.append("Why_people_love_the_music_mermaid")

        navigation_links.append("https://www.themusicmermaid.com/favorite-music-resources")
        nav_titles.append("Favorite_music_resources")

        navigation_links.append("https://www.themusicmermaid.com/about-us")  ## Photo
        nav_titles.append("About_us")

        navigation_links.append("https://www.themusicmermaid.com/contact-us")
        nav_titles.append("Contact_us")

        ## static_content
        # find_images()
        ## fonts() ??
        # find_css_links()

        ## TODO: interrupt when new articles are found
        WebScraper.crawl_nav_pages(navigation_links, nav_titles, s)


        ## Just for Cart
        if os.path.isfile(os.path.join("cart", ".html")):
            print(
                "Web Page found on filesystem: " + "cart.html")
            with open(os.path.join("cart", ".html"), 'r', encoding='utf-8') as file:
                cart_page_html = file.read()
                soup = BeautifulSoup(cart_page_html, 'html.parser')
                file.close()
            print("Cart Page --- Finished Crawling, downloaded resources.\n")
        else:
            article_html = WebScraper.original_htmldoc("https://www.themusicmermaid.com/cart", s)
            print("Page Retrieval for Cart page.  Remote Addr. - https://www.themusicmermaid.com/cart")
            if WebScraper.too_many_req:
                print("bad page too many req. Wait 3...")
                time.sleep(3)

            print("--REQUEST Complete,", end=" ")
            soup = BeautifulSoup(article_html, 'html.parser')
            WebScraper.dl_flag = True
            if (WebScraper.page_status_unchanged != True | WebScraper.dl_flag) & (not WebScraper.too_many_req):
                with open(os.path.join("cart", "cart.html"), 'w', encoding='utf-8') as file:
                    file.write(str(soup))
                print("page saved, ---")
                print("Cart Page --- Finished Crawling, downloaded resources.\n")


                ## PRINTS SECOND



        for i in range(0, len(titles) - 1):
            print(titles[i])
            ##print(blog_content[i])
            print("    |" + thumbnail_imgs[i] + "\n\n")



    sitemap = [[], []]
    page_status_unchanged = False
    too_many_req = False
    dl_flag = True

    cookie_crumb = 0

    # Create local filestructure
    try:
        os.mkdir("home")
    except Exception:
        pass
    try:
        os.mkdir("images")
    except Exception:
        pass
    try:
        os.mkdir("audio")
    except Exception:
        pass
    try:
        os.mkdir("navigation")
    except Exception:
        pass
    try:
        os.mkdir("cart")
    except Exception:
        pass
    try:
        os.mkdir("comments")
    except Exception:
        pass


    s = requests.session()
    headers_impersonate_ua = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, br', 'Accept': '*/*', 'Connection': 'keep-alive'}    # Security headers
    s.headers = headers_impersonate_ua

    print('Enter a url to scrape for links present in it')

    url_to_scrape = input('Enter a website link to extract links')

WebScraper.crawl_site(WebScraper.url_to_scrape, WebScraper.s)

    ## Home Page
    ## While Load More -
    ##while soup.find("a", class_="load-more"):
    ## load_more = soup.find("a", class_="load-more")
    ## load_more_URL = "https://themusicmermaid.com"+load_more.get('href')
    ## If sitemap grows

    ##for link in links:
    ##print(link)
    ##article_page = original_htmldoc(link)
    ##soup = BeautifulSoup(article_page, 'html.parser')
    ##blog_content.append(soup.p.get_text())
    # blog_content.append(soup.find("div", {"data-layout-label": "Post Body"}).get_text())

    ## print(link.get('href'))
