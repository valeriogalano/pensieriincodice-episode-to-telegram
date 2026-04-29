import logging
import os
import re
import xml.etree.ElementTree as ET

import requests

from github_state import update_github_variable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram")

ITUNES_NS = 'http://www.itunes.com/dtds/podcast-1.0.dtd'


def fetch_last_episode(feed_url: str) -> dict:
    response = requests.get(feed_url)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    item = root.find('./channel/item')

    if item is None:
        raise Exception("Nessun episodio trovato nel feed")

    title = item.findtext('title', '').strip()
    link = item.findtext('link', '').strip()

    if not link:
        enclosure = item.find('enclosure')
        if enclosure is not None:
            link = enclosure.get('url', '').split('?')[0]

    if not title or not link:
        raise Exception(f"Titolo o link mancante: {title=} {link=}")

    keywords_el = item.find(f'{{{ITUNES_NS}}}keywords')
    hashtags = ''
    if keywords_el is not None and keywords_el.text:
        hashtags = ' '.join(
            '#' + re.sub(r'\s+', '', kw.strip())
            for kw in keywords_el.text.split(',')
            if kw.strip()
        )

    return {'title': title, 'link': link, 'hashtags': hashtags}


def escape_markdown_v2(text: str) -> str:
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(r'([' + re.escape(escape_chars) + r'])', r'\\\1', text)


def normalize_template(template: str) -> str:
    return template.replace('\\r\\n', '\n').replace('\\n', '\n')


def is_published(link: str, last_published_url: str) -> bool:
    return last_published_url == link


def publish_to_telegram(episode: dict, api_key: str, chat_id: str, template: str) -> None:
    content = template \
        .replace('{title}', escape_markdown_v2(episode['title'])) \
        .replace('{link}', episode['link']) \
        .replace('{hashtags}', escape_markdown_v2(episode['hashtags']))

    logger.info(f"Pubblicazione su Telegram: {content[:80]}...")

    response = requests.post(
        f"https://api.telegram.org/bot{api_key}/sendMessage",
        json={
            'chat_id': chat_id,
            'text': content,
            'parse_mode': 'MarkdownV2',
            'disable_notification': True,
            'link_preview_options': {'url': episode['link']},
        }
    )

    data = response.json()
    if not data.get('ok'):
        raise Exception(f"Errore Telegram API: {data.get('description', 'errore sconosciuto')}")

    logger.info("Post pubblicato con successo!")


if __name__ == "__main__":
    api_key = os.environ['TELEGRAM_BOT_API_KEY']
    chat_id = os.environ['CHAT_ID']
    feed_url = os.environ['RSS_URL']
    template = normalize_template(os.environ['TEMPLATE'])
    last_published_url = os.environ.get('LAST_PUBLISHED_URL', '')

    episode = fetch_last_episode(feed_url)
    logger.info(f"Ultimo episodio: {episode['link']}")

    if is_published(episode['link'], last_published_url):
        logger.info("Episodio già pubblicato, skip.")
    else:
        publish_to_telegram(episode, api_key, chat_id, template)
        update_github_variable('LAST_PUBLISHED_URL', episode['link'])
        logger.info("Variabile di stato aggiornata.")
