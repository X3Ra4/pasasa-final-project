from django.contrib import admin
from django import forms

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
    SpotUserRating,
    SpotMedia,
    SpotFeaturesPvp,
    TypePve,
    TypePvp,
)

MAP_ADMIN_GROUPS = {
    "MAP": {"Map"},
    "PVP": {
        "BestDinoForRaidPvp",
        "ExitQnttPvp",
        "SlPvp",
        "SpotFeaturesPvp",
        "SpotMedia",
        "SpotUserRating",
        "Spot",
        "TypePvp",
    },
    "PVE": {
        "TypePve",
        "PlaceMedia",
        "SpotFeaturesPve",
        "Place",
        "PlaceUserRating",
    },
}

PVP_MODEL_LABELS = {
    "BestDinoForRaidPvp": {"en": "Best dino for raid", "ru": "Лучшие дино для рейда"},
    "ExitQnttPvp": {"en": "Exit quantity", "ru": "Кол-во входов"},
    "SlPvp": {"en": "Sea line", "ru": "Линия во"},
    "SpotFeaturesPvp": {"en": "Features", "ru": "Фишки"},
    "SpotMedia": {"en": "Media", "ru": "Медиа"},
    "SpotUserRating": {"en": "User rating", "ru": "Рейтинг пользователей"},
    "Spot": {"en": "Spots", "ru": "Споты"},
    "TypePvp": {"en": "Types", "ru": "Типы"},
}


class MapAdminForm(forms.ModelForm):
    class Meta:
        model = Map
        fields = "__all__"
        widgets = {
            "head_img": forms.ClearableFileInput(attrs={"accept": ".avif,image/avif"}),
            "map_img": forms.ClearableFileInput(attrs={"accept": ".jpg,.jpeg,image/jpeg"}),
        }


@admin.register(Map)
class MapAdmin(admin.ModelAdmin):
    form = MapAdminForm
    list_display = ("id", "slug", "name", "name_ru")
    search_fields = ("slug", "name", "name_ru")
    prepopulated_fields = {"slug": ("name",)}
    fields = ("slug", "name", "name_ru", "head_img", "map_img")


@admin.register(TypePvp)
class TypePvpAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "name_ru")
    search_fields = ("slug", "name", "name_ru")


@admin.register(SlPvp)
class SlPvpAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "name_ru")
    search_fields = ("slug", "name", "name_ru")


@admin.register(BestDinoForRaidPvp)
class BestDinoForRaidPvpAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "dino")
    search_fields = ("slug", "dino")


@admin.register(ExitQnttPvp)
class ExitQnttPvpAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "quantity")
    search_fields = ("slug",)


@admin.register(SpotFeaturesPvp)
class SpotFeaturesPvpAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "name_ru")
    search_fields = ("slug", "name", "name_ru")


class SpotMediaInline(admin.TabularInline):
    model = SpotMedia
    extra = 1
    fields = ("sort_order", "media_type", "title", "file", "preview")
    ordering = ("sort_order", "id")


@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "slug",
        "name",
        "map_location",
        "player",
        "coordsx",
        "coordsy",
        "type",
        "sl",
        "best_dino_for_raid",
        "exit_qntt",
        "raiting",
        "user_rating",
        "count_likes",
        "features_preview",
    )
    list_filter = ("map_location", "player", "type", "sl", "best_dino_for_raid", "exit_qntt", "raiting")
    search_fields = ("slug", "name", "name_ru")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("map_location", "player", "type", "sl", "best_dino_for_raid", "exit_qntt")
    filter_horizontal = ("spotfeature",)
    inlines = (SpotMediaInline,)
    readonly_fields = ("user_rating", "count_likes")
    list_per_page = 50
    ordering = ("id",)
    fieldsets = (
        ("Main", {"fields": ("name", "name_ru", "slug", "map_location", "player")}),
        ("Coords", {"fields": ("coordsx", "coordsy")}),
        ("Classification", {"fields": ("type", "sl", "best_dino_for_raid", "exit_qntt", "raiting", "user_rating", "count_likes")}),
        ("Features", {"fields": ("spotfeature",)}),
    )

    @admin.display(description="Features")
    def features_preview(self, obj):
        return ", ".join(obj.spotfeature.values_list("name", flat=True)) or "-"


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "slug",
        "name",
        "map_location",
        "player",
        "coordsx",
        "coordsy",
        "type",
        "resources",
        "rating",
        "user_rating",
        "count_likes",
        "features_preview",
    )
    list_filter = ("map_location", "player", "type", "resources", "rating")
    search_fields = ("slug", "name", "name_ru")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("map_location", "player", "type")
    filter_horizontal = ("spotfeature",)
    readonly_fields = ("user_rating", "count_likes")
    list_per_page = 50
    ordering = ("id",)
    fieldsets = (
        ("Main", {"fields": ("name", "name_ru", "slug", "map_location", "player")}),
        ("Coords", {"fields": ("coordsx", "coordsy")}),
        ("Classification", {"fields": ("type", "resources", "rating", "user_rating", "count_likes")}),
        ("Features", {"fields": ("spotfeature",)}),
    )

    @admin.display(description="Features")
    def features_preview(self, obj):
        return ", ".join(obj.spotfeature.values_list("name", flat=True)) or "-"


@admin.register(SpotMedia)
class SpotMediaAdmin(admin.ModelAdmin):
    list_display = ("id", "spot", "media_type", "title", "sort_order")
    list_filter = ("media_type", "spot__map_location")
    search_fields = ("title", "spot__name", "spot__name_ru", "spot__slug")
    autocomplete_fields = ("spot",)
    ordering = ("spot", "sort_order", "id")


@admin.register(SpotUserRating)
class SpotUserRatingAdmin(admin.ModelAdmin):
    list_display = ("id", "spot", "user", "rating", "updated_at")
    list_filter = ("rating", "spot__map_location")
    search_fields = ("spot__name", "spot__name_ru", "spot__slug", "user__username")
    autocomplete_fields = ("spot", "user")
    ordering = ("-updated_at",)


@admin.register(TypePve)
class TypePveAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "name_ru")
    search_fields = ("slug", "name", "name_ru")


@admin.register(SpotFeaturesPve)
class SpotFeaturesPveAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "name", "name_ru")
    search_fields = ("slug", "name", "name_ru")


@admin.register(PlaceMedia)
class PlaceMediaAdmin(admin.ModelAdmin):
    list_display = ("id", "place", "media_type", "title", "sort_order")
    list_filter = ("media_type", "place__map_location")
    search_fields = ("title", "place__name", "place__name_ru", "place__slug")
    autocomplete_fields = ("place",)
    ordering = ("place", "sort_order", "id")


@admin.register(PlaceUserRating)
class PlaceUserRatingAdmin(admin.ModelAdmin):
    list_display = ("id", "place", "user", "rating", "updated_at")
    list_filter = ("rating", "place__map_location")
    search_fields = ("place__name", "place__name_ru", "place__slug", "user__username")
    autocomplete_fields = ("place", "user")
    ordering = ("-updated_at",)


_original_get_app_list = admin.site.get_app_list


def _grouped_maps_get_app_list(request, app_label=None):
    app_list = _original_get_app_list(request, app_label=app_label)
    maps_app = next((app for app in app_list if app.get("app_label") == "maps"), None)
    if not maps_app:
        return app_list
    is_ru = str(getattr(request, "LANGUAGE_CODE", "") or "").lower().startswith("ru")

    grouped_apps = []
    for group_name, model_names in MAP_ADMIN_GROUPS.items():
        models = []
        for model in maps_app["models"]:
            if model["object_name"] not in model_names:
                continue
            model_item = dict(model)
            if group_name == "PVP":
                labels = PVP_MODEL_LABELS.get(model_item["object_name"])
                if labels:
                    model_item["name"] = labels["ru"] if is_ru else labels["en"]
            models.append(model_item)
        if not models:
            continue
        grouped_apps.append(
            {
                **maps_app,
                "name": f"MAPS - {group_name}",
                "models": sorted(models, key=lambda item: item["name"].lower()),
            }
        )

    other_models = [
        model
        for model in maps_app["models"]
        if not any(model["object_name"] in model_names for model_names in MAP_ADMIN_GROUPS.values())
    ]
    if other_models:
        grouped_apps.append({**maps_app, "name": "MAPS - OTHER", "models": other_models})

    result = [app for app in app_list if app.get("app_label") != "maps"]
    result.extend(grouped_apps)
    return result


admin.site.get_app_list = _grouped_maps_get_app_list
