# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import CreateView, DeleteView, ListView
from .models import Archivo
from .response import JSONResponse, response_mimetype
from .serialize import serialize


class ArchivoCreateView(CreateView):
    model = Archivo
    fields = ['file']

    def form_valid(self, form):
        form.instance.owner = self.request.user
        super(ArchivoCreateView, self).form_valid(form)
        self.object = form.save()
        files = [serialize(self.object)]
        data = {'files': files}
        response = JSONResponse(data, mimetype=response_mimetype(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response

class ArchivoActualizacionCreateView(CreateView):
    template_name = 'archivo_update_form.html'
    model = Archivo
    fields = ['file']

    def get_context_data(self, *args, **kwargs):
        context = super(ArchivoActualizacionCreateView, self).get_context_data(*args, **kwargs)
        context['id_capa'] = self.kwargs['id_capa']
        return context

    def form_valid(self, form):
        form.instance.owner = self.request.user
        super(ArchivoActualizacionCreateView, self).form_valid(form)
        self.object = form.save()
        files = [serialize(self.object)]
        data = {'files': files}
        response = JSONResponse(data, mimetype=response_mimetype(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response


class ArchivoDeleteView(DeleteView):
    model = Archivo

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        response = JSONResponse(True, mimetype=response_mimetype(request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response


class ArchivoListView(ListView):
    model = Archivo

    def get_queryset(self):
        return Archivo.objects.owned_by(self.request.user).order_by('slug')

    def render_to_response(self, context, **response_kwargs):
        files = [serialize(p) for p in self.get_queryset()]
        data = {'files': files}
        response = JSONResponse(data, mimetype=response_mimetype(self.request))
        response['Content-Disposition'] = 'inline; filename=files.json'
        return response
