"""Sitemap — tells Google exactly which pages to index.
Submitted once in Google Search Console; Google re-reads it automatically."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class PublicPagesSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'weekly'

    # (url name, priority)
    pages = [
        ('home', 1.0),
        ('rates_page', 0.9),
        ('public_track_search', 0.8),
        ('terms_page', 0.5),
        ('signup', 0.4),
        ('login', 0.3),
    ]

    def items(self):
        return self.pages

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]


sitemaps = {'pages': PublicPagesSitemap}
