import re
from datetime import datetime
from hashlib import md5

from django import template
from django.core.cache import cache
from django.conf import settings

from embedly import Embedly
from embeds.models import SavedEmbed
from django.utils.safestring import mark_safe


register = template.Library()

EMBED_REGEX = re.compile(r'https?://[\w\d:#@%/;$()~_?\+\-=\\\.&]+', re.I)
USER_AGENT = 'Mozilla/5.0 (compatible; django-embedly/0.2; ' \
        '+http://github.com/BayCitizen/)'

@register.filter
def embedly(html, arg=None):
    return mark_safe(EMBED_REGEX.sub(lambda x: embed_replace(x, maxwidth=arg), html))


def embed_replace(match, maxwidth=None):
    url = match.group(0)

    key = make_cache_key(url, maxwidth)
    cached_html = cache.get(key)

    if cached_html:
        return cached_html

    # call embedly API
    client = Embedly(key=settings.EMBEDLY_KEY, user_agent=USER_AGENT)
    if maxwidth:
        oembed = client.oembed(url, maxwidth=maxwidth)
    else:
        oembed = client.oembed(url)

    # check database
#    if oembed.error:
#        try:
#            html = SavedEmbed.objects.get(url=url, maxwidth=maxwidth).html
#            cache.set(key, html)
#            return html
#        except SavedEmbed.DoesNotExist:
#            return 'Error embedding %s' % url

    # save result to database
#    row, created = SavedEmbed.objects.get_or_create(url=url, maxwidth=maxwidth,
#                defaults={'type': oembed.type})

    if oembed['type'] == 'photo':
        html = '<img src="%s" width="%s" />' % (oembed['url'],
                oembed['width'])
    elif oembed['type'] == 'link':
        html = '<a href="%s"><img src="%s" />%s - %s</a><span>%s</span>' % (oembed['url'],
                oembed['thumbnail_url'], oembed['title'], oembed['provider_url'], oembed['description'])
    elif oembed.get('html'):
        html = oembed['html']
    else:
        html = url

    #if html:
        #row.html = html
        #row.last_updated = datetime.now()
        #row.save()

    # set cache
    #cache.set(key, html, 86400)
    return html


def make_cache_key(url, maxwidth=None):
    md5_hash = md5(url).hexdigest()
    return "embeds.%s.%s" % (maxwidth if maxwidth else 'default', md5_hash)
