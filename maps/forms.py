from django import forms
from .models import Map, Spot, Place


class MapForm(forms.ModelForm):
    class Meta:
        model = Map
        fields = ['name', 'name_ru', 'slug', 'head_img', 'map_img']
        labels = {'name': 'Назва', 'name_ru': 'Назва російською (необов’язково)', 'slug': 'Адреса (латиницею)', 'head_img': 'Обкладинка (.avif)', 'map_img': 'Зображення карти (.jpg)'}


class LocationForm(forms.ModelForm):
    coordsx = forms.DecimalField(label='Широта', min_value=0, max_value=100, decimal_places=1, max_digits=5)
    coordsy = forms.DecimalField(label='Довгота', min_value=0, max_value=100, decimal_places=1, max_digits=5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['name', 'slug', 'map_location']:
            self.fields[name].required = True
        labels = {'name': 'Назва', 'name_ru': 'Назва російською', 'slug': 'Адреса (латиницею)', 'map_location': 'Карта', 'type': 'Тип локації', 'spotfeature': 'Особливості', 'sl': 'Розташування відносно води', 'best_dino_for_raid': 'Динозавр для рейду', 'exit_qntt': 'Кількість входів', 'raiting': 'Оцінка локації', 'rating': 'Оцінка локації', 'resources': 'Доступність ресурсів'}
        for name, label in labels.items():
            if name in self.fields:
                self.fields[name].label = label


class SpotForm(LocationForm):
    class Meta:
        model = Spot
        fields = ['name', 'name_ru', 'slug', 'map_location', 'coordsx', 'coordsy', 'type', 'sl', 'best_dino_for_raid', 'exit_qntt', 'spotfeature', 'raiting']


class PlaceForm(LocationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['type', 'resources', 'rating']:
            self.fields[name].required = True

    class Meta:
        model = Place
        fields = ['name', 'name_ru', 'slug', 'map_location', 'coordsx', 'coordsy', 'type', 'spotfeature', 'rating', 'resources']
