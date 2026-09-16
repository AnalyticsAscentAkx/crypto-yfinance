"""Recent headline metadata from public RSS feeds; no retired Messari endpoint."""
import datetime
import logging
import re
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

from .cache import ttl_cache
from .http import get_response
from .validation import asset_symbol, positive_int

logger = logging.getLogger('cryptofinance')
_FEEDS = ('https://www.coindesk.com/arc/outboundfeeds/rss/', 'https://cointelegraph.com/rss')
_NAMES = {'BTC': ('bitcoin',), 'ETH': ('ethereum', 'ether'), 'SOL': ('solana',),
          'XRP': ('ripple',), 'DOGE': ('dogecoin',), 'ADA': ('cardano',),
          'BNB': ('binance coin',), 'LTC': ('litecoin',), 'AVAX': ('avalanche',),
          'LINK': ('chainlink',), 'DOT': ('polkadot',), 'USDT': ('tether',),
          'USDC': ('usd coin',), 'BCH': ('bitcoin cash',), 'XLM': ('stellar',)}


@ttl_cache(ttl=900)
def _feed_articles(url):
    response = get_response(url)
    root = ElementTree.fromstring(response.content)
    if root.tag != 'rss' or root.find('channel') is None:
        raise ValueError('News provider did not return an RSS channel')
    articles = []
    for item in root.findall('./channel/item'):
        title, link = item.findtext('title'), item.findtext('link')
        if not title or not link or not link.startswith(('https://', 'http://')):
            continue
        try:
            date = parsedate_to_datetime(item.findtext('pubDate', ''))
            if date.tzinfo is None:
                date = date.replace(tzinfo=datetime.timezone.utc)
            published_at = date.astimezone(datetime.timezone.utc).isoformat()
        except (TypeError, ValueError):
            published_at = None
        articles.append({
            'title': title.strip(), 'published_at': published_at,
            'author': item.findtext('{http://purl.org/dc/elements/1.1/}creator') or item.findtext('author'),
            'url': link.strip(), 'tags': [n.text for n in item.findall('category') if n.text],
        })
    return articles


@ttl_cache(ttl=900)
def get_news(symbol: str, limit: int = 10) -> list:
    """Return recent RSS headlines mentioning an asset in their title or tags.

    Matches use the ticker and known common names. The feeds provide a limited
    recent window, so fewer than limit results (including none) are normal.
    Every result retains the publisher's URL; full article content is not returned.
    """
    base = asset_symbol(symbol)
    positive_int(limit, 'limit')
    terms = (base,) + _NAMES.get(base, ())
    pattern = re.compile(r'\b(?:' + '|'.join(re.escape(t) for t in terms) + r')\b', re.I)
    results, successes, errors = {}, 0, []
    for url in _FEEDS:
        try:
            articles = _feed_articles(url)
            successes += 1
            for article in articles:
                if pattern.search(article['title'] + ' ' + ' '.join(article['tags'])):
                    results[article['url']] = article
        except Exception as exc:
            errors.append(exc)
            logger.warning('News feed %s failed: %s', url, exc)
    if not successes:
        raise ValueError('All news feeds failed; enable cryptofinance logging for details') from errors[-1]
    return sorted(results.values(), key=lambda a: a['published_at'] or '', reverse=True)[:limit]
