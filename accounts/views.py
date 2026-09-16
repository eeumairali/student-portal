import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import StudentProfile

VALID_PALETTE_KEYS = {
    "nature", "modern-blue", "ai-purple", "teal", "dark-tech",
    "green", "warm-modern", "pastel", "elegant", "soft-creative",
    "rainbow", "candy", "unicorn", "bubblegum", "sunshine",
    "art-class", "toy-box", "dino", "mermaid", "space",
    "watermelon", "ice-cream", "balloon", "flower", "ocean",
    "bumblebee", "peachy", "frog", "neon-fun", "cupcake",
}


@login_required
@require_POST
def set_theme_palette(request):
    """Persist the student's chosen site color palette so it follows them
    across devices/browsers, not just the one that made the choice
    (localStorage is still the source of truth for instant, no-flash
    apply — this just keeps it backed up server-side)."""
    try:
        data = json.loads(request.body or "{}")
    except ValueError:
        return JsonResponse({"ok": False}, status=400)

    key = data.get("key", "")
    if key and key not in VALID_PALETTE_KEYS:
        return JsonResponse({"ok": False}, status=400)

    profile = getattr(request.user, "student_profile", None)
    if profile is not None:
        StudentProfile.objects.filter(pk=profile.pk).update(theme_palette=key)

    return JsonResponse({"ok": True})
