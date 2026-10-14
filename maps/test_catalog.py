from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from .models import Map, Place, Spot, TypePvp, TypePve, SlPvp, BestDinoForRaidPvp, ExitQnttPvp


class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user('owner', password='Example-pass-493!')
        cls.other = get_user_model().objects.create_user('other', password='Example-pass-493!')
        cls.staff = get_user_model().objects.create_user('staff', password='Example-pass-493!', is_staff=True)
        cls.map = Map.objects.create(slug='island', name='The Island')
        cls.pve_type = TypePve.objects.create(slug='plain', name='Plain')
        cls.place = Place.objects.create(slug='beach', name='Beach', map_location=cls.map, player=cls.owner, coordsx=20, coordsy=30, rating=4)
        cls.spot_fields = dict(type=TypePvp.objects.create(slug='cave', name='Cave'), sl=SlPvp.objects.create(slug='land', name='Land'), best_dino_for_raid=BestDinoForRaidPvp.objects.create(slug='rex', dino='Rex'), exit_qntt=ExitQnttPvp.objects.create(slug='one', quantity=1))

    def test_public_catalog_and_details(self):
        for url in ['/catalog/maps/', '/catalog/spots/', '/catalog/places/', f'/catalog/maps/{self.map.pk}/', f'/catalog/places/{self.place.pk}/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_anonymous_and_nonstaff_cannot_manage_maps(self):
        self.assertEqual(self.client.get('/catalog/maps/new/').status_code, 302)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post('/catalog/maps/new/', {'name': 'Bad', 'slug': 'bad'}).status_code, 403)
        self.assertFalse(Map.objects.filter(slug='bad').exists())

    def test_staff_map_crud_and_protected_delete(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post('/catalog/maps/new/', {'name': 'New map', 'slug': 'new-map'}).status_code, 302)
        obj = Map.objects.get(slug='new-map')
        self.assertEqual(self.client.post(f'/catalog/maps/{obj.pk}/edit/', {'name': 'Changed', 'slug': obj.slug}).status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.name, 'Changed')
        self.assertEqual(self.client.get(f'/catalog/maps/{obj.pk}/delete/').status_code, 200)
        self.assertTrue(Map.objects.filter(pk=obj.pk).exists())
        self.assertEqual(self.client.post(f'/catalog/maps/{obj.pk}/delete/').status_code, 302)
        self.assertFalse(Map.objects.filter(pk=obj.pk).exists())
        response = self.client.post(f'/catalog/maps/{self.map.pk}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Спочатку')
        self.assertTrue(Map.objects.filter(pk=self.map.pk).exists())

    def test_owner_place_crud(self):
        self.client.force_login(self.owner)
        data = {'name': 'Forest', 'slug': 'forest', 'map_location': self.map.pk, 'coordsx': '40.5', 'coordsy': '50', 'rating': 4, 'resources': 3, 'type': self.pve_type.pk, 'player': self.other.pk}
        self.assertEqual(self.client.post('/catalog/places/new/', data).status_code, 302)
        obj = Place.objects.get(slug='forest')
        self.assertEqual(obj.player, self.owner)
        data['name'] = 'Green forest'
        self.assertEqual(self.client.post(f'/catalog/places/{obj.pk}/edit/', data).status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.name, 'Green forest')
        self.assertContains(self.client.get(f'/catalog/places/{obj.pk}/'), 'Green forest')
        self.assertEqual(self.client.post(f'/catalog/places/{obj.pk}/delete/').status_code, 302)
        self.assertFalse(Place.objects.filter(pk=obj.pk).exists())

    def test_owner_spot_crud(self):
        self.client.force_login(self.owner)
        data = {'name': 'Cave', 'slug': 'cave', 'map_location': self.map.pk, 'coordsx': '40', 'coordsy': '50', 'raiting': 4, **{k: v.pk for k, v in self.spot_fields.items()}}
        self.assertEqual(self.client.post('/catalog/spots/new/', data).status_code, 302)
        obj = Spot.objects.get(slug='cave')
        self.assertEqual(obj.player, self.owner)
        data['name'] = 'Hidden cave'
        self.assertEqual(self.client.post(f'/catalog/spots/{obj.pk}/edit/', data).status_code, 302)
        self.assertContains(self.client.get(f'/catalog/spots/{obj.pk}/'), 'Hidden cave')
        self.assertEqual(self.client.post(f'/catalog/spots/{obj.pk}/delete/').status_code, 302)
        self.assertFalse(Spot.objects.filter(pk=obj.pk).exists())

    def test_ownership_and_staff_override(self):
        self.client.force_login(self.other)
        for action in ['edit', 'delete']:
            self.assertEqual(self.client.post(f'/catalog/places/{self.place.pk}/{action}/', {}).status_code, 403)
        self.assertTrue(Place.objects.filter(pk=self.place.pk).exists())
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(f'/catalog/places/{self.place.pk}/edit/').status_code, 200)

    def test_invalid_coordinates_and_required_fields(self):
        self.client.force_login(self.owner)
        data = {'name': 'Bad', 'slug': 'bad', 'map_location': self.map.pk, 'coordsx': 101, 'coordsy': -1}
        response = self.client.post('/catalog/places/new/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Place.objects.filter(slug='bad').exists())
        self.assertTrue(response.context['form'].errors.get('coordsx'))
        self.assertTrue(response.context['form'].errors.get('coordsy'))

    def test_pve_form_requires_interactive_map_fields(self):
        self.client.force_login(self.owner)
        response = self.client.post('/catalog/places/new/', {'name': 'Incomplete', 'slug': 'incomplete', 'map_location': self.map.pk, 'coordsx': 20, 'coordsy': 30})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Place.objects.filter(slug='incomplete').exists())
        for field in ['type', 'resources', 'rating']:
            self.assertIn(field, response.context['form'].errors)

    def test_pve_map_handles_legacy_null_resources(self):
        self.place.type = self.pve_type
        self.place.save()
        Place.objects.create(slug='complete', name='Complete', map_location=self.map, type=self.pve_type, coordsx=10, coordsy=10, resources=4)
        response = self.client.get('/PVE/maps/island/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('beach', response.context['spot_payload'])
        self.assertEqual(response.context['exit_options'], [{'slug': 'res-4', 'quantity': 4}])

    def test_search_filter_sort_and_invalid_filter(self):
        another = Map.objects.create(slug='other', name='Other')
        Place.objects.create(slug='another-beach', name='Another beach', map_location=another, coordsx=1, coordsy=1)
        response = self.client.get('/catalog/places/', {'q': 'beach', 'map': self.map.pk, 'sort': '-name'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['page_obj']), [self.place])
        response = self.client.get('/catalog/places/', {'map': 'bad', 'sort': 'invalid', 'page': 'oops'})
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/catalog/places/', {'sort': '-name'})
        self.assertEqual([obj.name for obj in response.context['page_obj']], ['Beach', 'Another beach'])

    def test_registration_login_and_post_logout(self):
        response = self.client.post('/accounts/signup/', {'username': 'newplayer', 'password1': 'Unique-pass-8491!', 'password2': 'Unique-pass-8491!'})
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username='newplayer')
        self.assertFalse(user.is_staff)
        self.client.logout()
        self.assertEqual(self.client.post('/accounts/login/', {'username': 'newplayer', 'password': 'Unique-pass-8491!'}).status_code, 302)
        self.assertEqual(self.client.get('/accounts/logout/').status_code, 405)
        self.assertEqual(self.client.post('/accounts/logout/').status_code, 302)

    def test_seed_is_repeatable_and_preserves_edits(self):
        call_command('seed_demo', verbosity=0)
        counts = (Map.objects.count(), Spot.objects.count(), Place.objects.count())
        obj = Map.objects.get(slug='the-island')
        obj.name = 'Edited by user'
        obj.save()
        call_command('seed_demo', verbosity=0)
        self.assertEqual(counts, (Map.objects.count(), Spot.objects.count(), Place.objects.count()))
        obj.refresh_from_db()
        self.assertEqual(obj.name, 'Edited by user')
