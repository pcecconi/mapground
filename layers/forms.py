# -*- coding: utf-8 -*-
from django import forms
from django.forms import ModelForm, ValidationError
from django.core.validators import MinLengthValidator
# from django.forms.extras.widgets import SelectDateWidget
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import InMemoryUploadedFile

from layers.models import Metadatos, Atributo, Capa, Categoria, ArchivoSLD, Escala, AreaTematica
from users.models import PermisoDeCapa, PermisoDeCapaPorGrupo
from maps.models import MapServerLayer
from utils.commons import normalizar_texto

import xml.etree.ElementTree as ET
import os


class MetadatosForm(ModelForm):
    # fecha_de_relevamiento = forms.DateField(widget=SelectDateWidget(),required=False)
    # fecha_de_actualizacion = forms.DateField(widget=SelectDateWidget(),required=False)
    categorias = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=Categoria.objects.all().order_by('nombre'), required=False)
    titulo = forms.CharField(label='Título', validators=[MinLengthValidator(5)])

    class Meta:
        model = Metadatos
        fields = ['titulo', 'descripcion', 'fuente', 'contacto', 'escala', 'area_tematica', 'palabras_claves', 'fecha_de_relevamiento', 'fecha_de_actualizacion', 'frecuencia_de_actualizacion', 'categorias']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
            'fuente': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
            'contacto': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
            'palabras_claves': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
        }


class AtributoForm(ModelForm):
    class Meta:
        model = Atributo
        fields = ['nombre_del_campo', 'tipo', 'alias', 'descripcion', 'publicable']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
        }

    def __init__(self, *args, **kwargs):
        super(AtributoForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['nombre_del_campo'].widget.attrs['readonly'] = 'True'
            self.fields['tipo'].widget.attrs['readonly'] = 'True'


# este modelform no se usa mas, lo reemplazamos por la funcion a continuacion que crea un modelform dinamico filtrando el usuario actual del listado de opciones posibles
# class PermisoDeCapaForm(ModelForm):
#     class Meta:
#         model = PermisoDeCapa
#         fields = ['capa', 'user', 'permiso']


def make_permisodecapa_form(usuario):
    class PermisoDeCapaForm(ModelForm):
        user = forms.ModelChoiceField(label='Usuario', queryset=User.objects.exclude(pk=usuario.pk).exclude(username='admin').exclude(username='mapground').order_by('username'))

        class Meta:
            model = PermisoDeCapa
            fields = ['capa', 'user', 'permiso']
    return PermisoDeCapaForm


class CapaForm(ModelForm):
    class Meta:
        model = Capa
        fields = ['wxs_publico']


class CategoriaForm(ModelForm):
    nombre = forms.CharField(label='Nombre', validators=[MinLengthValidator(5)])

    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }


class EscalaForm(ModelForm):
    nombre = forms.CharField(label='Nombre', validators=[MinLengthValidator(5)])

    class Meta:
        model = Escala
        fields = ['nombre']


class AreaTematicaForm(ModelForm):
    nombre = forms.CharField(label='Nombre', validators=[MinLengthValidator(5)])

    class Meta:
        model = AreaTematica
        fields = ['nombre', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }


class PermisoDeCapaPorGrupoForm(ModelForm):
    group = forms.ModelChoiceField(label='Grupo', queryset=Group.objects.all().order_by('name'))

    class Meta:
        model = PermisoDeCapaPorGrupo
        fields = ['capa', 'group', 'permiso']


class ArchivoSLDForm(ModelForm):
    # filename= forms.FileField(label='Seleccione un archivo', help_text='Seleccione un archivo'),
    class Meta:
        model = ArchivoSLD
        fields = ['filename', 'descripcion', 'default', 'user_alta', 'user_modificacion', 'timestamp_alta', 'timestamp_modificacion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'cols': 30}),
            # 'filename': forms.FileInput(attrs={'value': 'Seleccione un archivo'}),#, help_text='Seleccione un archivo'),
            # 'id_archivo_sld': forms.TextInput(attrs={'size': 120}),
        }

    def clean_filename(self):   # nombre por convencion: clean_<campo>
        filename = self.cleaned_data.get('filename', False)
        if isinstance(filename, InMemoryUploadedFile):
            uploaded_filename = normalizar_texto(os.path.splitext(filename.name)[0])
            id_archivo_sld = (self.instance.capa.id_capa + '_' if not uploaded_filename.startswith(self.instance.capa.id_capa) else '') + uploaded_filename + '.sld'
            if ArchivoSLD.objects.filter(id_archivo_sld=id_archivo_sld).exclude(id=self.instance.id):
                raise ValidationError("Ya existe un archivo SLD con el nombre %s para esta capa" % (filename))
            try:
                tree = ET.parse(filename)
                root = tree.getroot()
                if root.tag.find('StyledLayerDescriptor') == -1:
                    raise ValidationError("Archivo SLD inválido %s" % (filename))
            except:
                raise ValidationError("Archivo SLD inválido %s" % (filename))
        return self.cleaned_data.get('filename', False)

    def __init__(self, *args, **kwargs):
        super(ArchivoSLDForm, self).__init__(*args, **kwargs)
        self.fields['user_alta'].widget.attrs['readonly'] = 'True'
        self.fields['user_modificacion'].widget.attrs['readonly'] = 'True'
        self.fields['timestamp_alta'].widget.attrs['readonly'] = 'True'
        self.fields['timestamp_modificacion'].widget.attrs['readonly'] = 'True'
        self.fields['user_alta'].widget = forms.HiddenInput()
        self.fields['user_modificacion'].widget = forms.HiddenInput()
        self.fields['timestamp_alta'].widget = forms.HiddenInput()
        self.fields['timestamp_modificacion'].widget = forms.HiddenInput()


def make_band_sld_form(capa):

    class BandSLDForm(ModelForm):
        archivo_sld = forms.ModelChoiceField(label='Nombre de archivo SLD', queryset=ArchivoSLD.objects.filter(capa=capa).order_by('filename'), required=False)
        banda = forms.CharField()

        class Meta:
            model = MapServerLayer
            fields = ['capa', 'banda', 'archivo_sld']

            # Nota sobre este Form:
            # La idea es poder editar la relacion entre un mapa de tipo layer_raster_band y un archivo_sld de la capa en cuestion.
            # La definicion original a continuacion, que seria la mas logica y directa, no funciona porque al renderizar el campo 'mapa' para mostrar la banda no es posible ajustar exactamente
            # el comportamiento como queremos: si mantengo forms.ModelChoiceFiel renderiza un FK que no puedo deshabilitar del todo, y permite cambios que rompen relaciones core,
            # y si lo paso a TextField me renderiza el PK del objeto (los ids) y no el nombre de la banda.
            # Ver: https://stackoverflow.com/questions/39073885/template-displays-foreign-key-instead-of-charfield-for-disabled-field
            # Encotre otra forma de renombrar este campo que no sea mostrando el PK pero es volviendo a ModelChoiceField, y tampoco funciona con nuestros
            # modelos, ya que habria que definir un modelo intermedio entre ambos:
            # https://stackoverflow.com/questions/37922287/django-multichoicefield-to-field-name-and-selected
            # Con lo cual, la solucion fue sacar el campo 'mapa' del form, y definir un nuevo campo 'banda' con el str de la banda que sirva simplemente para mostrar la banda actual:
            # fields = ['capa', 'mapa', 'archivo_sld']

        def __init__(self, *args, **kwargs):
            super(BandSLDForm, self).__init__(*args, **kwargs)
            self.fields['banda'].widget.attrs['value'] = str(self.instance.mapa.titulo)
            self.fields['banda'].widget.attrs['readonly'] = True

    return BandSLDForm
