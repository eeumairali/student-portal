from django.shortcuts import get_object_or_404, render

from .models import Domain, Tutorial


def home(request):
    domains = [d for d in Domain.objects.all() if d.published_tutorial_count() > 0]
    return render(request, "tutorials/home.html", {"domains": domains})


def domain_detail(request, slug):
    domain = get_object_or_404(Domain, slug=slug)
    tutorials = domain.tutorials.filter(is_published=True)
    return render(request, "tutorials/domain_detail.html", {"domain": domain, "tutorials": tutorials})


def tutorial_detail(request, slug):
    tutorial = get_object_or_404(Tutorial, slug=slug, is_published=True)
    return render(request, "tutorials/tutorial_detail.html", {"tutorial": tutorial})
