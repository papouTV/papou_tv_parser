#!/usr/local/bin/python3
"""papou_tv_parser.py
Description:
    - Parses Skai News, Skai Live TV and ERT for .m3u8 playlist links.
    - Generates papoutv.github.io page using jinja2 template
Usage:
    'python3 papou_tv_parser.py'
"""


import requests
import datetime
import json
import re
import pathlib
from bs4 import BeautifulSoup as bs
from jinja2 import Environment, FileSystemLoader


def parse_skai_news(skai_news_url, skai_playlist_base_url, today, skai_base_url):
    """
    :param skai_news_url: URL to skai news page
    :param skai_playlist_base_url: base URL for playlists
    :param today: datetime object for today
    :param skai_base_url: base URL for skai tv
    :return: playlist_link (the link to the .m3u8 playlist for today's news episode.
    """
    date_string = today.strftime("%Y-%m-%d-14")
    # start by parsing the page with all news epsiodes
    news_page = requests.get(skai_news_url)
    news_soup = bs(news_page.content, "html.parser")
    # News Links have CSS class "resio"
    news_links = news_soup.find_all("a", class_="resio", href=True)
    # use list comprehension to get the first news link that ends with the date string
    todays_news = [_link["href"] for _link in news_links if _link["href"].endswith(date_string)][0]
    # start parsing the page with the news player
    todays_news_link = "{}{}".format(skai_base_url, todays_news)
    todays_page = requests.get(todays_news_link)
    # .m3u8 playlist link inside of a JSON object called data
    todays_soup = bs(todays_page.content, "html.parser")
    todays_html = str(todays_soup.html)
    todays_js_string = re.search(r"var data = ({.+})", str(todays_html)).group(1)
    todays_json_data = json.loads(todays_js_string)
    media_item_file = todays_json_data["episode"][0]["media_item_file"]
    playlist_link = "".join(
        "{}{}/chunklist.m3u8".format(skai_playlist_base_url, media_item_file)
    )
    return playlist_link


def parse_skai_live(skai_live_url):
    """
    :param skai_live_url: URL for skai's live TV page
    :return: live_link (link to .m3u8 playlist for skai's live TV)
    """
    live_page = requests.get(skai_live_url)
    live_soup = bs(live_page.content, "html.parser")
    live_html = str(live_soup.html)
    # .m3u8 playlist link inside of a JSON object called data
    live_js_string = re.search(r"var data = ({.+})", str(live_html)).group(1)
    live_json_data = json.loads(live_js_string)
    live_link = live_json_data["live"]["live"]
    return live_link


def parse_ert_live():
    """
    ERT Live URL does not seem to change so the function is just returning the .m3u8 playlist link.
    :return: .m3u8 playlist link.
    """
    return "https://ert-live-bcbs15228.siliconweb.com/media/ert_world/ert_world.m3u8"


def generate_page(today, generate_page_dict):
    """
    :param today: today's date object
    :param generate_page_dict: a dictionary containing all the variables that need to be inserted into
    the HTML page using jinja2.
    :return: nothing
    """
    date_string = today.strftime("%Y-%m-%d")
    destination_path = "staging/papouTV-{}".format(date_string)
    staging_directory = pathlib.Path(destination_path).mkdir(
        parents=True, exist_ok=True
    )
    # Load list of jinja2 templates in "templates" folder
    jinja2_env = Environment(loader=FileSystemLoader("templates"))
    jinja2_template = jinja2_env.get_template("papoutv.html")
    # render page using the keys-values inside of generate_page_dict
    jinja2_rendered_page = jinja2_template.render(**generate_page_dict)
    destination_path = "{}/index.html".format(destination_path)
    write_file(destination_path, jinja2_rendered_page)


def write_file(destination_path, rendered_page):
    """
    :param destination_path: Path to where the file should be sent.
    :param rendered_page:  String that represents the rendered HTML file.
    :return:  nothing
    """
    with open(destination_path, "w") as f:
        f.write(rendered_page)


if __name__ == "__main__":
    skai_base_url = "https://www.skaitv.gr"
    skai_playlist_base_url = "https://videostream.skai.gr/skaivod/_definst_/mp4:skai/"
    today = datetime.date.today()
    skai_news_url = "https://www.skaitv.gr/show/enimerosi/oi-eidiseis-tou-ska-stis-2/sezon-2021-2022"
    skai_live_url = "https://www.skaitv.gr/live"
    skai_news_link = parse_skai_news(
        skai_news_url, skai_playlist_base_url, today, skai_base_url
    )
    skai_live_link = parse_skai_live(skai_live_url)
    ert_live_link = parse_ert_live()
    generate_page_dict = {
        "skai_news_url": skai_news_link,
        "skai_live_url": skai_live_link,
        "ert_live_url": ert_live_link,
    }
    generate_page(today, generate_page_dict)
