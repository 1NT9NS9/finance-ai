"""
News endpoints: fetch and parse finance news via RSS and return normalized JSON.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
import re
import requests
from xml.etree import ElementTree as ET

from api.auth import auth_required
from config.settings import APP_ENV


logger = logging.getLogger('financial_data_ml.api.news')

news_bp = Blueprint('news', __name__)


RSS_SOURCES = {
    # Russian business/finance news RSS feeds
    'rbc': 'https://rssexport.rbc.ru/rbcnews/news/20/full.rss',
    'interfax': 'https://www.interfax.ru/rss.asp',
    'vedomosti': 'https://www.vedomosti.ru/rss/rubrics/finance',
    # Investing.com popular news page (HTML)
    'investing': 'https://ru.investing.com/news/most-popular-news',
}


def _clean_html(text: str) -> str:
    if not text:
        return ''
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_rss(url: str, limit: int = 20):
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; FinanceApp/1.0; +https://example.local)'
    }
    resp = requests.get(url, timeout=10, headers=headers)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []

    # Try RSS 2.0
    channel = root.find('channel')
    if channel is not None:
        for item in channel.findall('item')[:limit]:
            title_el = item.find('title')
            desc_el = item.find('description')
            link_el = item.find('link')
            date_el = item.find('pubDate')
            items.append({
                'title': (title_el.text or '').strip() if title_el is not None else '',
                'description': _clean_html(desc_el.text or '') if desc_el is not None else '',
                'link': (link_el.text or '').strip() if link_el is not None else '',
                'published_at': (date_el.text or '').strip() if date_el is not None else '',
            })
        return items

    # Try Atom
    ns = {
        'atom': 'http://www.w3.org/2005/Atom'
    }
    for entry in root.findall('atom:entry', ns)[:limit]:
        title_el = entry.find('atom:title', ns)
        summary_el = entry.find('atom:summary', ns) or entry.find('atom:content', ns)
        link_el = entry.find('atom:link', ns)
        updated_el = entry.find('atom:updated', ns) or entry.find('atom:published', ns)
        link_href = ''
        if link_el is not None:
            link_href = link_el.attrib.get('href', '')
        items.append({
            'title': (title_el.text or '').strip() if title_el is not None else '',
            'description': _clean_html(summary_el.text or '') if summary_el is not None else '',
            'link': link_href,
            'published_at': (updated_el.text or '').strip() if updated_el is not None else '',
        })
    return items


def parse_investing_popular(url: str, limit: int = 20):
    """Parse popular news from Investing.com Russian page (HTML scraping)."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36'
    }
    resp = requests.get(url, timeout=10, headers=headers)
    resp.raise_for_status()
    html = resp.text

    # Very simple extraction: find article blocks with titles and links
    # Titles typically inside <a class="title" ...> ... </a> or similar
    # We avoid heavy dependencies; use regex carefully
    item_regex = re.compile(r'<a[^>]+href="(?P<link>/news/[^"#?]+)"[^>]*>(?P<title>[^<]{10,200})</a>', re.IGNORECASE)
    items = []
    seen = set()
    for m in item_regex.finditer(html):
        link = m.group('link')
        title = _clean_html(m.group('title'))
        if not title or link in seen:
            continue
        seen.add(link)
        full_link = f"https://ru.investing.com{link}"
        items.append({
            'title': title,
            'description': '',
            'link': full_link,
            'published_at': ''
        })
        if len(items) >= limit:
            break
    return items


@news_bp.route('/news', methods=['GET'])
def get_news():
    """
    Get latest news from configured RSS sources.

    Query params:
      - source: one of RSS_SOURCES keys (default: 'rbc')
      - limit: max number of items (default: 20)
    """
    try:
        source = request.args.get('source', 'rbc').lower()
        limit = request.args.get('limit', default=20, type=int)
        if source not in RSS_SOURCES:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': f"Unsupported source: {source}",
                'supported_sources': list(RSS_SOURCES.keys())
            }), 400

        if source == 'investing':
            items = parse_investing_popular(RSS_SOURCES[source], limit=limit)
        else:
            items = parse_rss(RSS_SOURCES[source], limit=limit)
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'count': len(items),
            'items': items
        }), 200
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        payload = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': 'Internal error'
        }
        if APP_ENV != 'production':
            payload['detail'] = str(e)
        return jsonify(payload), 500


