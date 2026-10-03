from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Domain, Tutorial


class HomeSitemap(Sitemap):
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return ["home"]

    def location(self, item):
        return reverse(item)


class DomainSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Domain.objects.filter(tutorials__is_published=True).distinct()

    def location(self, domain):
        return reverse("domain_detail", args=[domain.slug])


class TutorialSitemap(Sitemap):
    priority = 0.6
    changefreq = "monthly"

    def items(self):
        return Tutorial.objects.filter(is_published=True).select_related("domain")

    def location(self, tutorial):
        return reverse("tutorial_detail", args=[tutorial.slug])


sitemaps = {"home": HomeSitemap, "domains": DomainSitemap, "tutorials": TutorialSitemap}
