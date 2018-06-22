# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404

from django.conf import settings
from proxy import views
from layers.views import logged_in_or_basicauth
from mapcache.settings import MAPSERVER_URL
from django.contrib.auth.models import User, Group
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.forms.models import modelformset_factory
from users.forms import UserForm, GroupForm
from django.http import HttpResponse,HttpResponseRedirect
from django.core.urlresolvers import reverse
from layers.models import Capa
from maps.models import Mapa, ManejadorDeMapas

import os


@logged_in_or_basicauth()
def wxs(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        return HttpResponseForbidden()
    
    extra_requests_args = {}
    mapfile=ManejadorDeMapas.get_mapfile(username)
    remote_url = MAPSERVER_URL+'?map='+mapfile # +'&mode=browse&layers=all&template=openlayers'
    return views.proxy_view(request, remote_url, extra_requests_args)

@login_required
def usuarios(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('layers:index'))

    UserFormSet = modelformset_factory(User, form=UserForm, can_delete=False, extra=0)

    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:index'))
        formset = UserFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            for f in formset:
                if 'groups' in f.changed_data or 'is_superuser' in f.changed_data:
                    ManejadorDeMapas.delete_mapfile(f.instance.username)
            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('users:usuarios'))
            return HttpResponseRedirect(reverse('layers:index'))
    else:
        formset = UserFormSet(queryset=User.objects.exclude(username__in=['admin','mapground']).order_by('username'))

    return render(request, 'users/usuarios.html', {'formset': formset})

@login_required
def grupos(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('layers:index'))

    GroupFormSet = modelformset_factory(Group, form=GroupForm, can_delete=True, extra=2)

    if request.method == 'POST':
        if '_cancel' in request.POST:
            return HttpResponseRedirect(reverse('layers:index'))
        formset = GroupFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            if '_save_and_continue' in request.POST:
                return HttpResponseRedirect(reverse('users:grupos'))
            return HttpResponseRedirect(reverse('layers:index'))
    else:
        formset = GroupFormSet(queryset=Group.objects.all().order_by('name'))

    return render(request, 'users/usuarios.html', {'formset': formset})
