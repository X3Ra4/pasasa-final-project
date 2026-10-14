from django.db import transaction
from django.db.models import Avg, Count, Prefetch
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils.translation import get_language
from django.contrib.auth.decorators import login_required

from accounts.forms import AccountPasswordForm, AccountProfileForm

from .models import (
    BestDinoForRaidPvp,
    ExitQnttPvp,
    Map,
    Place,
    PlaceMedia,
    PlaceUserRating,
    SlPvp,
    Spot,
    SpotFeaturesPve,
    SpotFeaturesPvp,
    SpotMedia,
    SpotUserRating,
    TypePve,
    TypePvp,
)
from .services.news import get_news_payload

VALID_MODES = {"PVP", "PVE"}


def get_localized_name(obj):
    lang = (get_language() or "en").lower()
    if lang.startswith("ru") and hasattr(obj, "name_ru") and obj.name_ru:
        return obj.name_ru
    return obj.name


def root_redirect(request):
    return redirect("maps:maps_home", mode="PVP")


def maps_home(request, mode):
    mode = mode.upper()
    if mode not in VALID_MODES:
        return not_found_page(request)

    if mode == "PVE":
        maps_queryset = Map.objects.annotate(
            total_spots=Count("places", distinct=True),
            avg_spot_rating=Avg("places__rating"),
        ).order_by("id")
    else:
        maps_queryset = Map.objects.annotate(
            total_spots=Count("spots", distinct=True),
            avg_spot_rating=Avg("spots__raiting"),
        ).order_by("id")

    context = {
        "current_mode": mode,
        "maps": [
            {
                "obj": map_obj,
                "display_name": get_localized_name(map_obj),
                "total_spots": map_obj.total_spots or 0,
                "avg_spot_rating": round(float(map_obj.avg_spot_rating or 0), 2),
            }
            for map_obj in maps_queryset
        ],
    }
    return render(request, "maps/home.html", context)


def map_detail(request, mode, map_slug):
    mode = mode.upper()
    if mode not in VALID_MODES:
        return not_found_page(request)

    map_obj = get_object_or_404(Map, slug=map_slug)
    user = request.user if request.user.is_authenticated else None

    if mode == "PVE":
        places = (
            Place.objects.filter(
                map_location=map_obj,
                slug__isnull=False,
                type__isnull=False,
                coordsx__isnull=False,
                coordsy__isnull=False,
            )
            .select_related("type", "player")
            .prefetch_related(
                "spotfeature",
                Prefetch("media_items", queryset=PlaceMedia.objects.all().order_by("sort_order", "id")),
            )
            .order_by("id")
        )

        user_rating_by_place_id = {}
        if user:
            user_rating_by_place_id = {
                row["place_id"]: row["rating"]
                for row in PlaceUserRating.objects.filter(user=user, place__in=places).values("place_id", "rating")
            }

        spot_payload = {}
        for place in places:
            place_name = get_localized_name(place)
            type_name = get_localized_name(place.type)
            features = [get_localized_name(feature) for feature in place.spotfeature.all()]
            spot_payload[place.slug] = {
                "kind": "place",
                "title": place_name,
                "coords": f"{place.coordsy} / {place.coordsx}",
                "type_name": type_name,
                "resources": place.resources,
                "features": features,
                "admin_rating": place.rating,
                "user_rating": float(place.user_rating or 0),
                "my_rating": user_rating_by_place_id.get(place.id, 0),
                "likes_count": place.count_likes(),
                "is_liked": bool(user and place.likes.filter(id=user.id).exists()),
                "player": place.player.username if place.player else "-",
                "media": [
                    {
                        "type": media.media_type,
                        "src": media.file.url if media.file else "",
                        "thumb": media.preview.url if media.preview else (media.file.url if media.media_type == PlaceMedia.MEDIA_IMAGE and media.file else ""),
                        "title": media.title or f"{place_name} #{media.pk}",
                    }
                    for media in place.media_items.all()
                ],
            }

        resources_values = sorted({value for value in places.values_list("resources", flat=True) if value is not None})

        context = {
            "current_mode": mode,
            "map_obj": map_obj,
            "spots": places,
            "map_display_name": get_localized_name(map_obj),
            "type_options": [
                {"slug": item.slug, "display_name": get_localized_name(item)}
                for item in TypePve.objects.filter(places__in=places).distinct().order_by("name")
            ],
            "sl_options": [],
            "best_dino_for_raid_options": [],
            "exit_options": [{"slug": f"res-{value}", "quantity": value} for value in resources_values],
            "feature_options": [
                {"slug": item.slug, "display_name": get_localized_name(item)}
                for item in SpotFeaturesPve.objects.filter(places__in=places).distinct().order_by("name")
            ],
            "spot_payload": spot_payload,
        }
        return render(request, "maps/map_detail.html", context)

    spots = (
        Spot.objects.filter(map_location=map_obj)
        .select_related("type", "sl", "best_dino_for_raid", "exit_qntt", "player")
        .prefetch_related(
            "spotfeature",
            Prefetch("media_items", queryset=SpotMedia.objects.all().order_by("sort_order", "id")),
        )
        .order_by("id")
    )

    user_rating_by_spot_id = {}
    if user:
        user_rating_by_spot_id = {
            row["spot_id"]: row["rating"]
            for row in SpotUserRating.objects.filter(user=user, spot__in=spots).values("spot_id", "rating")
        }

    spot_payload = {}
    for spot in spots:
        spot_name = get_localized_name(spot)
        type_name = get_localized_name(spot.type)
        sl_name = get_localized_name(spot.sl)
        features = [get_localized_name(feature) for feature in spot.spotfeature.all()]
        spot_payload[spot.slug] = {
            "kind": "spot",
            "title": spot_name,
            "coords": f"{spot.coordsy} / {spot.coordsx}",
            "type_name": type_name,
            "sl_name": sl_name,
            "dino_name": spot.best_dino_for_raid.dino,
            "exit_quantity": spot.exit_qntt.quantity,
            "features": features,
            "admin_rating": spot.raiting,
            "user_rating": float(spot.user_rating or 0),
            "my_rating": user_rating_by_spot_id.get(spot.id, 0),
            "likes_count": spot.count_likes(),
            "is_liked": bool(user and spot.likes.filter(id=user.id).exists()),
            "player": spot.player.username if spot.player else "-",
            "media": [
                {
                    "type": media.media_type,
                    "src": media.file.url if media.file else "",
                    "thumb": media.preview.url if media.preview else (media.file.url if media.media_type == SpotMedia.MEDIA_IMAGE and media.file else ""),
                    "title": media.title or f"{spot_name} #{media.pk}",
                }
                for media in spot.media_items.all()
            ],
        }

    context = {
        "current_mode": mode,
        "map_obj": map_obj,
        "spots": spots,
        "map_display_name": get_localized_name(map_obj),
        "type_options": [
            {"slug": item.slug, "display_name": get_localized_name(item)}
            for item in TypePvp.objects.filter(spots__in=spots).distinct().order_by("name")
        ],
        "sl_options": [
            {"slug": item.slug, "display_name": get_localized_name(item)}
            for item in SlPvp.objects.filter(spots__in=spots).distinct().order_by("name")
        ],
        "best_dino_for_raid_options": BestDinoForRaidPvp.objects.filter(spots__in=spots).distinct().order_by("dino"),
        "exit_options": ExitQnttPvp.objects.filter(spots__in=spots).distinct().order_by("quantity"),
        "feature_options": [
            {"slug": item.slug, "display_name": get_localized_name(item)}
            for item in SpotFeaturesPvp.objects.filter(spots__in=spots).distinct().order_by("name")
        ],
        "spot_payload": spot_payload,
    }
    return render(request, "maps/map_detail.html", context)


@require_POST
def spot_like_api(request, spot_slug):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "auth_required"}, status=403)
    spot = get_object_or_404(Spot, slug=spot_slug)
    user = request.user
    if spot.likes.filter(id=user.id).exists():
        spot.likes.remove(user)
        is_liked = False
    else:
        spot.likes.add(user)
        is_liked = True

    return JsonResponse(
        {
            "ok": True,
            "spot": spot.slug,
            "is_liked": is_liked,
            "likes_count": spot.count_likes(),
        }
    )


@require_POST
def spot_rate_api(request, spot_slug):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "auth_required"}, status=403)
    spot = get_object_or_404(Spot, slug=spot_slug)
    try:
        rating = int(request.POST.get("rating", "0"))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "invalid_rating"}, status=400)

    if rating < 1 or rating > 5:
        return JsonResponse({"ok": False, "error": "invalid_rating"}, status=400)

    with transaction.atomic():
        SpotUserRating.objects.update_or_create(
            spot=spot,
            user=request.user,
            defaults={"rating": rating},
        )
        spot.recalculate_user_rating()

    return JsonResponse(
        {
            "ok": True,
            "spot": spot.slug,
            "my_rating": rating,
            "user_rating": float(spot.user_rating or 0),
        }
    )


@require_POST
def place_like_api(request, place_slug):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "auth_required"}, status=403)
    place = get_object_or_404(Place, slug=place_slug)
    user = request.user
    if place.likes.filter(id=user.id).exists():
        place.likes.remove(user)
        is_liked = False
    else:
        place.likes.add(user)
        is_liked = True

    return JsonResponse(
        {
            "ok": True,
            "spot": place.slug,
            "is_liked": is_liked,
            "likes_count": place.count_likes(),
        }
    )


@require_POST
def place_rate_api(request, place_slug):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "auth_required"}, status=403)
    place = get_object_or_404(Place, slug=place_slug)
    try:
        rating = int(request.POST.get("rating", "0"))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "invalid_rating"}, status=400)

    if rating < 1 or rating > 5:
        return JsonResponse({"ok": False, "error": "invalid_rating"}, status=400)

    with transaction.atomic():
        PlaceUserRating.objects.update_or_create(
            place=place,
            user=request.user,
            defaults={"rating": rating},
        )
        place.recalculate_user_rating()

    return JsonResponse(
        {
            "ok": True,
            "spot": place.slug,
            "my_rating": rating,
            "user_rating": float(place.user_rating or 0),
        }
    )


def news_api(request):
    payload = get_news_payload(request.GET.get("lang"))
    return JsonResponse(payload)


def _build_account_favorite_items(user):
    favorite_spots = (
        user.liked_spots.select_related("map_location", "type", "sl")
        .prefetch_related(Prefetch("media_items", queryset=SpotMedia.objects.all().order_by("sort_order", "id")))
        .order_by("name")
    )
    favorite_places = (
        user.liked_places.select_related("map_location", "type")
        .prefetch_related(Prefetch("media_items", queryset=PlaceMedia.objects.all().order_by("sort_order", "id")))
        .order_by("name")
    )

    items = []

    for spot in favorite_spots:
        media_item = next(iter(spot.media_items.all()), None)
        items.append(
            {
                "kind": "PVP",
                "title": get_localized_name(spot),
                "map_name": get_localized_name(spot.map_location) if spot.map_location else "-",
                "coords": f"{spot.coordsy} / {spot.coordsx}",
                "type_name": get_localized_name(spot.type),
                "detail_url": reverse("maps:map_detail", kwargs={"mode": "PVP", "map_slug": spot.map_location.slug}) if spot.map_location else "",
                "media_url": media_item.preview.url if media_item and media_item.preview else (media_item.file.url if media_item and media_item.file else ""),
                "rating": spot.raiting,
                "likes_count": spot.count_likes(),
            }
        )

    for place in favorite_places:
        media_item = next(iter(place.media_items.all()), None)
        items.append(
            {
                "kind": "PVE",
                "title": get_localized_name(place),
                "map_name": get_localized_name(place.map_location) if place.map_location else "-",
                "coords": f"{place.coordsy} / {place.coordsx}",
                "type_name": get_localized_name(place.type) if place.type else "-",
                "detail_url": reverse("maps:map_detail", kwargs={"mode": "PVE", "map_slug": place.map_location.slug}) if place.map_location else "",
                "media_url": media_item.preview.url if media_item and media_item.preview else (media_item.file.url if media_item and media_item.file else ""),
                "rating": place.rating,
                "likes_count": place.count_likes(),
            }
        )

    return sorted(items, key=lambda item: (item["kind"], (item["title"] or "").lower()))


@login_required
def profile_page(request, profile_key):
    if profile_key != request.user.username:
        return redirect("maps:profile", profile_key=request.user.username)

    user = request.user
    active_tab = request.GET.get("tab", "account")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile":
            profile_form = AccountProfileForm(request.POST, request.FILES, instance=user)
            password_form = AccountPasswordForm(user=user)
            active_tab = "account"
            if profile_form.is_valid():
                profile_form.save()
                messages.success(
                    request,
                    "Профиль обновлен." if (get_language() or "en").startswith("ru") else "Profile updated.",
                )
                return redirect(f"{reverse('maps:profile', kwargs={'profile_key': user.username})}?tab=account")
        elif action == "password":
            profile_form = AccountProfileForm(instance=user)
            password_form = AccountPasswordForm(user=user, data=request.POST)
            active_tab = "settings"
            if password_form.is_valid():
                changed_user = password_form.save()
                update_session_auth_hash(request, changed_user)
                messages.success(
                    request,
                    "Пароль обновлен." if (get_language() or 'en').startswith("ru") else "Password updated.",
                )
                return redirect(f"{reverse('maps:profile', kwargs={'profile_key': user.username})}?tab=settings")
        else:
            profile_form = AccountProfileForm(instance=user)
            password_form = AccountPasswordForm(user=user)
    else:
        profile_form = AccountProfileForm(instance=user)
        password_form = AccountPasswordForm(user=user)

    context = {
        "current_mode": "PVP",
        "profile_key": user.username,
        "favorite_items": _build_account_favorite_items(user),
        "profile_form": profile_form,
        "password_form": password_form,
        "active_tab": active_tab,
    }
    return render(request, "accounts/profile.html", context)


def not_found_page(request, exception=None):
    return render(request, "404.html", status=404)
