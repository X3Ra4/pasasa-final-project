from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import MapForm, SpotForm, PlaceForm
from .models import Map, Spot, Place

CATALOGS = {
    'maps': (Map, MapForm, 'Карти'),
    'spots': (Spot, SpotForm, 'PvP-локації'),
    'places': (Place, PlaceForm, 'PvE-локації'),
}


def config(kind):
    if kind not in CATALOGS:
        raise Http404
    model, form_class, title = CATALOGS[kind]
    return model, form_class, {'kind': kind, 'catalog_title': title}


def can_manage(user, kind, obj=None):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return kind != 'maps' and (obj is None or obj.player_id == user.pk)


def catalog_list(request, kind):
    model, _, context = config(kind)
    queryset = model.objects.all()
    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(Q(name__icontains=query) | Q(name_ru__icontains=query) | Q(slug__icontains=query))
    map_id = request.GET.get('map', '')
    if kind != 'maps':
        queryset = queryset.select_related('map_location', 'player')
        if map_id.isascii() and map_id.isdecimal() and len(map_id) < 10:
            queryset = queryset.filter(map_location_id=int(map_id))
    sort = request.GET.get('sort', 'name')
    if sort not in ('name', '-name', '-id'):
        sort = 'name'
    page = Paginator(queryset.order_by(sort, 'pk'), 12).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    context.update(page_obj=page, query=query, selected_map=map_id, sort=sort,
                   maps=Map.objects.order_by('name'), query_string=params.urlencode(),
                   can_create=can_manage(request.user, kind))
    return render(request, 'catalog/list.html', context)


def catalog_detail(request, kind, pk):
    model, _, context = config(kind)
    obj = get_object_or_404(model, pk=pk)
    context.update(obj=obj, can_edit=can_manage(request.user, kind, obj))
    if kind == 'maps':
        context.update(spots=obj.spots.order_by('name'), places=obj.places.order_by('name'))
    else:
        context.update(features=obj.spotfeature.all(), media_items=obj.media_items.all(),
                       location_rating=obj.raiting if kind == 'spots' else obj.rating,
                       mode='PVP' if kind == 'spots' else 'PVE')
    return render(request, 'catalog/detail.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def catalog_edit(request, kind, pk=None):
    model, form_class, context = config(kind)
    obj = get_object_or_404(model, pk=pk) if pk is not None else None
    if not can_manage(request.user, kind, obj):
        raise PermissionDenied
    form = form_class(request.POST if request.method == 'POST' else None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        saved = form.save(commit=False)
        if kind != 'maps' and obj is None:
            saved.player = request.user
        saved.save()
        form.save_m2m()
        messages.success(request, 'Зміни збережено.')
        return redirect('catalog:detail', kind=kind, pk=saved.pk)
    context.update(form=form, obj=obj)
    return render(request, 'catalog/form.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def catalog_delete(request, kind, pk):
    model, _, context = config(kind)
    obj = get_object_or_404(model, pk=pk)
    if not can_manage(request.user, kind, obj):
        raise PermissionDenied
    context['obj'] = obj
    if request.method == 'POST':
        try:
            obj.delete()
        except ProtectedError:
            context['error'] = 'Спочатку видаліть або перенесіть усі локації цієї карти.'
        else:
            messages.success(request, 'Запис видалено.')
            return redirect('catalog:list', kind=kind)
    return render(request, 'catalog/delete.html', context)
