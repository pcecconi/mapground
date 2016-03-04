# -*- coding: utf-8 -*-
from django import forms
from django.forms import ModelForm, ValidationError
from django.core.validators import MinLengthValidator
from django.forms.extras.widgets import SelectDateWidget
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import InMemoryUploadedFile

from maps.models import Categoria
from maps.models import Mapa

from utils.commons import normalizar_texto

class MapaForm(ModelForm):
    categorias= forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=Categoria.objects.all().order_by('nombre'), required=False)
    titulo = forms.CharField(label='Título', validators=[MinLengthValidator(5)])
    class Meta:
        model = Mapa
        fields = ['titulo', 'publico', 'descripcion', 'fuente', 'contacto', 'escala', 'palabras_claves', 'categorias']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
            'fuente': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
            'contacto': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
            'palabras_claves': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
        }

