# -*- coding: utf-8 -*-
from django import forms
from django.forms import ModelForm
from django.core.validators import MinLengthValidator
# from django.forms.extras.widgets import SelectDateWidget
from django.contrib.auth.models import User, Group
from users.models import UserProfile

# from layers.models import Metadatos, Atributo, Capa, Categoria
# from users.models import PermisoDeCapa, PermisoDeCapaPorGrupo


class UserForm(ModelForm):
    is_superuser = forms.BooleanField(label='¿Es superusuario?', required=False)
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all().order_by('name'), required=False)

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['username'].widget.attrs['readonly'] = 'True'
            # self.fields['first_name'].widget.attrs['readonly'] = 'True'
            # self.fields['last_name'].widget.attrs['readonly'] = 'True'
            # self.fields['date_joined'].widget.attrs['readonly'] = 'True'
            # self.fields['last_login'].widget.attrs['readonly'] = 'True'
            # self.fields['groups'].widget.attrs['rows']= 1
            # self.fields['groups'].widget.attrs['cols']= 20

    class Meta:
        model = User
        # fields = ['username', 'groups', 'first_name', 'last_name', 'email', 'is_superuser', 'date_joined', 'last_login',]
        fields = ['username', 'groups', 'is_superuser']

        widgets = {
            # 'groups': forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=Group.objects.all())
        }


class GroupForm(ModelForm):
    name = forms.CharField(label='Nombre', validators=[MinLengthValidator(4)])

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = 'Nombre de grupo'

    class Meta:
        model = Group
        fields = ['name']


class UserProfileForm(ModelForm):
    # 'usuario' es un field inventado: si uso 'user' pasa lo mismo que con ArchivoSLD:
    # me muestra el usuario pero con un combo seleccionable, por mas que sea readonly
    # y si lo fuerzo a disabled, me renderiza el pk del usuario.
    # La solucion es poner un campo de referencia
    usuario = forms.CharField()
    # user = forms.CharField(label='Nombre de usuario', disabled=True)

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['puede_subir_capas'].label = '¿Puede subir capas?'
        self.fields['usuario'].widget.attrs['readonly'] = True
        self.fields['usuario'].widget.attrs['value'] = str(self.instance.user.username)

    class Meta:
        model = UserProfile
        fields = ['usuario', 'puede_subir_capas']
