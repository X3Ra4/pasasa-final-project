from django.core.management.base import BaseCommand
from django.db import transaction
from maps.models import Map, Spot, Place, TypePvp, TypePve, SlPvp, BestDinoForRaidPvp, ExitQnttPvp, SpotFeaturesPvp, SpotFeaturesPve


class Command(BaseCommand):
    help = 'Create fictional demonstration locations and map catalog; preserve existing records.'

    @transaction.atomic
    def handle(self, *args, **options):
        map_specs = [
            ('the-island', 'The Island', 'ISLANDpr.avif', 'The_Island_map_ASA.jpg'),
            ('scorched-earth', 'Scorched Earth', 'SEpr.avif', 'Scorched_Earth_map_ASA.jpg'),
            ('aberration', 'Aberration', 'ABERpr.avif', 'Aberration_map_ASA.jpg'),
            ('the-center', 'The Center', 'CENTERpr.avif', 'The_Center_map_ASA.jpg'),
            ('ragnarok', 'Ragnarok', 'RAGpr.avif', 'Ragnarog_map_ASA.jpg'),
            ('extinction', 'Extinction', 'EXTpr.avif', 'Extinction_map_ASA.jpg'),
            ('astraeos', 'Astraeos', 'ASTERpr.avif', 'Astraeos_Map_ASA.jpg'),
            ('valguero', 'Valguero', 'VALGpr.avif', 'Valguero_map_ASA.jpg'),
            ('lost-colony', 'Lost Colony', 'LOSTpr.avif', 'Lost_Colony_Map_ASA.jpg'),
        ]
        maps = []
        for slug, name, cover, image in map_specs:
            obj, _ = Map.objects.get_or_create(slug=slug, defaults={'name': name, 'head_img': f'maps/{cover}', 'map_img': f'maps/{image}'})
            maps.append(obj)
        cave, _ = TypePvp.objects.get_or_create(slug='cave', defaults={'name': 'Cave', 'name_ru': 'Пещера'})
        land, _ = SlPvp.objects.get_or_create(slug='land', defaults={'name': 'Land', 'name_ru': 'Суша'})
        dino, _ = BestDinoForRaidPvp.objects.get_or_create(slug='rex', defaults={'dino': 'Rex'})
        exits, _ = ExitQnttPvp.objects.get_or_create(slug='one', defaults={'quantity': 1})
        defend, _ = SpotFeaturesPvp.objects.get_or_create(slug='shelter', defaults={'name': 'Shelter', 'name_ru': 'Укрытие'})
        plain, _ = TypePve.objects.get_or_create(slug='plain', defaults={'name': 'Plain', 'name_ru': 'Равнина'})
        water, _ = SpotFeaturesPve.objects.get_or_create(slug='water', defaults={'name': 'Near water', 'name_ru': 'Рядом с водой'})
        for i, map_obj in enumerate(maps[:3]):
            for j, (spot_name, place_name) in enumerate([('Hidden cave', 'Quiet beach'), ('Cliff shelter', 'Forest clearing')]):
                spot, created = Spot.objects.get_or_create(slug=f'demo-{map_obj.slug}-pvp-{j}', defaults={
                    'name': f'{spot_name} · {map_obj.name}', 'map_location': map_obj, 'coordsx': 25 + i * 10 + j * 18,
                    'coordsy': 35 + i * 8 + j * 15, 'type': cave, 'sl': land, 'best_dino_for_raid': dino,
                    'exit_qntt': exits, 'raiting': 4 + j,
                })
                if created:
                    spot.spotfeature.add(defend)
                place, created = Place.objects.get_or_create(slug=f'demo-{map_obj.slug}-pve-{j}', defaults={
                    'name': f'{place_name} · {map_obj.name}', 'map_location': map_obj, 'coordsx': 30 + i * 12 + j * 15,
                    'coordsy': 40 + i * 7 + j * 16, 'type': plain, 'rating': 4, 'resources': 3 + j,
                })
                if created:
                    place.spotfeature.add(water)
        self.stdout.write(self.style.SUCCESS('Demo catalog ready. Locations are fictional; no user accounts or passwords were created.'))
