from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.db import models



class Map(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    name_ru = models.CharField(max_length=255, null=True, blank=True)
    head_img = models.FileField(
        upload_to="maps/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["avif"])],
    )
    map_img = models.FileField(
        upload_to="maps/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg"])],
    )

    def __str__(self):
        return self.name

#PVP
class TypePvp(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    name_ru = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return self.name


class SlPvp(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    name_ru = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return self.name


class BestDinoForRaidPvp(models.Model):
    slug = models.SlugField(unique=True)
    dino = models.CharField(max_length=120)

    def __str__(self):
        return self.dino


class ExitQnttPvp(models.Model):
    slug = models.SlugField(unique=True)
    quantity = models.PositiveSmallIntegerField()

    def __str__(self):
        return str(self.quantity)


class SpotFeaturesPvp(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    name_ru = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return self.name


class Spot(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    name_ru = models.CharField(max_length=255, null=True, blank=True)
    coordsx = models.DecimalField(max_digits=5, decimal_places=1)
    coordsy = models.DecimalField(max_digits=5, decimal_places=1)

    type = models.ForeignKey(TypePvp, on_delete=models.PROTECT, related_name="spots")
    sl = models.ForeignKey(SlPvp, on_delete=models.PROTECT, related_name="spots")
    best_dino_for_raid = models.ForeignKey(BestDinoForRaidPvp, on_delete=models.PROTECT, related_name="spots")
    exit_qntt = models.ForeignKey(ExitQnttPvp, on_delete=models.PROTECT, related_name="spots")
    spotfeature = models.ManyToManyField(SpotFeaturesPvp, related_name="spots", blank=True)
    map_location = models.ForeignKey(
        Map,
        on_delete=models.PROTECT,
        related_name="spots",
        null=True,
        blank=True,
    )
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_spots",
    )
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="liked_spots",
    )
    user_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    raiting = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    def count_likes(self):
        return self.likes.count()

    def recalculate_user_rating(self):
        values = list(self.user_ratings.values_list("rating", flat=True))
        if not values:
            self.user_rating = 0
        else:
            self.user_rating = round(sum(values) / len(values), 2)
        self.save(update_fields=["user_rating"])

    def __str__(self):
        return self.name


class SpotUserRating(models.Model):
    spot = models.ForeignKey(Spot, on_delete=models.CASCADE, related_name="user_ratings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="spot_ratings")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("spot", "user")

    def __str__(self):
        return f"{self.user} -> {self.spot}: {self.rating}"


class SpotMedia(models.Model):
    MEDIA_IMAGE = "image"
    MEDIA_VIDEO = "video"
    MEDIA_TYPE_CHOICES = (
        (MEDIA_IMAGE, "Image"),
        (MEDIA_VIDEO, "Video"),
    )

    spot = models.ForeignKey(Spot, on_delete=models.CASCADE, related_name="media_items")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default=MEDIA_IMAGE)
    file = models.FileField(upload_to="spots/media/")
    preview = models.ImageField(upload_to="spots/previews/", null=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.title or f"{self.get_media_type_display()} #{self.pk}"

#PVE
class TypePve(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    name_ru = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return self.name


class SpotFeaturesPve(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    name_ru = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return self.name


class Place(models.Model):
    slug = models.SlugField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    name_ru = models.CharField(max_length=255, null=True, blank=True)
    coordsx = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    coordsy = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    type = models.ForeignKey(TypePve, on_delete=models.PROTECT, related_name="places", null=True, blank=True)
    resources = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    spotfeature = models.ManyToManyField(SpotFeaturesPve, related_name="places", blank=True)
    map_location = models.ForeignKey(
        Map,
        on_delete=models.PROTECT,
        related_name="places",
        null=True,
        blank=True,
    )
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_places",
    )
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="liked_places",
    )
    user_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
    )

    def count_likes(self):
        return self.likes.count()

    def recalculate_user_rating(self):
        values = list(self.user_ratings.values_list("rating", flat=True))
        if not values:
            self.user_rating = 0
        else:
            self.user_rating = round(sum(values) / len(values), 2)
        self.save(update_fields=["user_rating"])

    def __str__(self):
        return self.name


class PlaceUserRating(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="user_ratings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="place_ratings")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("place", "user")

    def __str__(self):
        return f"{self.user} -> {self.place}: {self.rating}"


class PlaceMedia(models.Model):
    MEDIA_IMAGE = "image"
    MEDIA_VIDEO = "video"
    MEDIA_TYPE_CHOICES = (
        (MEDIA_IMAGE, "Image"),
        (MEDIA_VIDEO, "Video"),
    )

    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="media_items")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default=MEDIA_IMAGE)
    file = models.FileField(upload_to="places/media/")
    preview = models.ImageField(upload_to="places/previews/", null=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.title or f"{self.get_media_type_display()} #{self.pk}"
