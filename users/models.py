# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.db.models import Count

from layers.models import Capa, Categoria, Metadatos, Escala, AreaTematica
from maps.models import Mapa, ManejadorDeMapas

# signals
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver

PERMISOS_ENUM = (
    ('read', 'read'),
    ('write', 'write'),
)


class PermisoDeCapa(models.Model):
    user = models.ForeignKey(User, null=False,blank=False, verbose_name='Usuario')
    capa = models.ForeignKey(Capa, null=False,blank=False)
    permiso = models.CharField('Permiso', choices=PERMISOS_ENUM, max_length=10, null=False, blank=False)
    class Meta:
        unique_together=(('user', 'capa'),)
        verbose_name = u'Permiso de Capa'
        verbose_name_plural = u'Permisos de Capas'
        ordering = ['user__username']
    def __unicode__(self):
        return '%s - %s - %s'%(unicode(self.user), unicode(self.permiso), unicode(self.capa))

class PermisoDeMapa(models.Model):
    user = models.ForeignKey(User, null=False,blank=False, verbose_name='Usuario')
    mapa = models.ForeignKey(Mapa, null=False,blank=False)
    permiso = models.CharField('Permiso', choices=PERMISOS_ENUM, max_length=10, null=False, blank=False)    
    class Meta:
        unique_together=(('user', 'mapa'),)
        verbose_name = u'Permiso de Mapa'
        verbose_name_plural = u'Permisos de Mapas'
    def __unicode__(self):
        return '%s - %s - %s'%(unicode(self.user), unicode(self.permiso), unicode(self.capa))

class PermisoDeCapaPorGrupo(models.Model):
    group = models.ForeignKey(Group, null=False,blank=False, verbose_name='Grupo')
    capa = models.ForeignKey(Capa, null=False,blank=False)
    permiso = models.CharField('Permiso', choices=PERMISOS_ENUM, max_length=10, null=False, blank=False)    
    class Meta:
        unique_together=(('group', 'capa'),)
        verbose_name = u'Permiso de Capa por Grupo'
        verbose_name_plural = u'Permisos de Capas por Grupos'
        ordering = ['group__name']
    def __unicode__(self):
        return '%s - %s - %s'%(unicode(self.group), unicode(self.permiso), unicode(self.capa))


class ManejadorDePermisos():
    @staticmethod
    def capas_de_usuario(user, caso_de_uso, qset_capas_inicial=None):
        if type(user) in (str,unicode):
            try:
                user = User.objects.get(username=user)
            except:
                return None
        # decidimos si partimos de todas las capas o un subset inicial
        if qset_capas_inicial is None:
            q = Capa.objects.all()
        else:
            q = qset_capas_inicial
        # sea quien sea el usuario, si no esta autenticado fuerzo el caso publico
        if not user.is_authenticated():
            caso_de_uso='public'
        # armamos el queryset filtrando segun el caso    
        if   caso_de_uso=='public': # capas publicas
            q = q.filter(wxs_publico=True)
        elif   caso_de_uso=='own':  # capas propias
            q = q.filter(owner=user)
        elif caso_de_uso=='all':    # todas las que tiene acceso
            if not user.is_superuser: # si es superuser no filtro, sino filtro
                q = (q.filter(owner=user)|                                          # propias
                     q.filter(permisodecapa__user=user)|                            # algun permiso personal
                     q.filter(permisodecapaporgrupo__group__in=user.groups.all())|  # algun permiso de grupo
                     q.filter(wxs_publico=True))                                    # todas las publicas
                q = q.distinct()
        else:
            q = Capa.objects.none()
            
        return q

    @staticmethod
    def mapas_de_usuario(user, caso_de_uso, qset_mapas_inicial=None):
        if type(user) in (str,unicode):
            try:
                user = User.objects.get(username=user)
            except:
                return None
        # decidimos si partimos de todos los mapas o un subset inicial
        if qset_mapas_inicial is None:
            q = Mapa.objects.all().filter(tipo_de_mapa='general')
        else:
            q = qset_mapas_inicial
        # sea quien sea el usuario, si no esta autenticado fuerzo el caso publico
        if not user.is_authenticated():
            caso_de_uso='public'
        # armamos el queryset filtrando segun el caso    
        if caso_de_uso=='public': # mapas publicos
            q = q.filter(publico=True)
        elif caso_de_uso=='own':  # mapas propios
            q = q.filter(owner=user)
        elif caso_de_uso=='all':    # todos los que tiene acceso
            if not user.is_superuser: # si es superuser no filtro, sino filtro
                q = (q.filter(owner=user)|                                      # propios
                     q.filter(publico=True))                                    # todos los publicos
                q = q.distinct()
        else:
            q = Mapa.objects.none()
            
        return q

    @staticmethod
    def permiso_de_capa(user, capa):
        """ Devuelve alguno de estos casos en orden: owner|superuser|(read|write)|None"""
        if type(user) in (str,unicode):
            try:
                user = User.objects.get(username=user)
            except:
                return None
        if type(capa) in (str,unicode):
            try:
                capa = Capa.objects.get(id_capa=capa)
            except:
                return None

        if capa.owner==user:
            return 'owner'
        if user.is_superuser:
            return 'superuser'
        try:
            p=PermisoDeCapa.objects.get(user=user, capa=capa)
            return p.permiso # si existe, esto devuelve read o write
        except:              # si no existe, verificamos si hay algun grupo write, y sino, luego algun grupo read
            for g in user.groups.all():
                if len(PermisoDeCapaPorGrupo.objects.filter(group=g, capa=capa, permiso='write')) > 0:
                    return 'write'
            for g in user.groups.all():
                if len(PermisoDeCapaPorGrupo.objects.filter(group=g, capa=capa, permiso='read')) > 0:
                    return 'read'
            if capa.wxs_publico:
                return 'read'
            return None

    @staticmethod
    def permiso_de_mapa(user, mapa):
        """ Devuelve alguno de estos casos en orden: owner|superuser|read|None"""
        if type(user) in (str,unicode):
            try:
                user = User.objects.get(username=user)
            except:
                return None
        if type(mapa) in (str,unicode):
            try:
                mapa = Mapa.objects.get(id_mapa=mapa)
            except:
                return None
        
        if mapa.tipo_de_mapa=='layer':
            return ManejadorDePermisos.permiso_de_capa(user, mapa.capas.first())
        elif mapa.tipo_de_mapa=='general':
            if mapa.owner==user:
                return 'owner'
            if user.is_superuser:
                return 'superuser'
            try:
                p=PermisoDeMapa.objects.get(user=user, mapa=mapa) # por el momento no implementamos permisos a nivel de mapa, lo simplificamos a mapa publico o privado
                return p.permiso # si existe, esto devuelve read o write
            except:              # si no existe, verificamos si hay algun grupo write, y sino, luego algun grupo read
                if mapa.publico:
                    return 'read'
        return None

    @classmethod
    def anotar_permiso_a_queryset_de_capas(cls, user, qs):
        for capa in qs:         
            capa.permiso=cls.permiso_de_capa(user, capa)
            capa.borrable=len(capa.mapa_set.filter(tipo_de_mapa='general'))==0
            
    @classmethod
    def anotar_permiso_a_queryset_de_mapas(cls, user, qs):
        for mapa in qs:         
            mapa.permiso=cls.permiso_de_mapa(user, mapa)

    @classmethod
    def anotar_permiso_a_capa(cls, user, capa):
        capa.permiso=cls.permiso_de_capa(user, capa)
        capa.borrable=len(capa.mapa_set.filter(tipo_de_mapa='general'))==0

    @classmethod
    def anotar_permiso_a_mapa(cls, user, mapa):
        mapa.permiso=cls.permiso_de_mapa(user, mapa)
    
    @classmethod
    def usuarios_con_permiso_a_capa(cls, capa):
# imposible resolver esta consulta con querysets como sigue porque aparecen repetidos en ambos grupos read y write
# tampoco se pueden agregar objetos a un queryset, la solucion es convertir a listas          
#             return (User.objects.filter(permisodecapa__permiso=permiso, permisodecapa__capa=capa)|
#                     User.objects.filter(groups__permisodecapaporgrupo__permiso=permiso,groups__permisodecapaporgrupo__capa=capa)).order_by('username')
        # armamos listas iniciales con permisos de usuarios especificos 
        read = list(User.objects.filter(permisodecapa__permiso='read', permisodecapa__capa=capa))
        write = list(User.objects.filter(permisodecapa__permiso='write', permisodecapa__capa=capa))
        # appendeamos permisos de grupos
        for u in User.objects.filter(groups__permisodecapaporgrupo__permiso='write',groups__permisodecapaporgrupo__capa=capa):
            if u not in read and u not in write: 
                write.append(u)
        for u in User.objects.filter(groups__permisodecapaporgrupo__permiso='read',groups__permisodecapaporgrupo__capa=capa):
            if u not in read and u not in write: 
                read.append(u)
        # sacamos owner si aparece en los grupos
        if capa.owner in read:
            read.remove(capa.owner)
        if capa.owner in write:
            write.remove(capa.owner)
        # ordenamos
        read.sort(key=lambda x:x.username)
        write.sort(key=lambda x:x.username)
                                
        return {'owner': capa.owner, 'read': read, 'write': write}            

    @classmethod
    def capas_agrupadas_por_categoria(cls):
        categorias=Categoria.objects.annotate(total=Count('metadatos')).order_by('nombre')
        sin_categoria=len(Metadatos.objects.filter(categorias=None))
        return {'categorias': categorias, 'sin_categoria': sin_categoria }

    @classmethod
    def mapas_agrupados_por_categoria(cls):
        categorias=Categoria.objects.annotate(total=Count('mapa')).order_by('nombre')
        sin_categoria=len(Mapa.objects.filter(tipo_de_mapa='general',categorias=None))
        return {'categorias': categorias, 'sin_categoria': sin_categoria }

    @classmethod
    def capas_agrupadas_por_escala(cls):
        escalas=Escala.objects.annotate(total=Count('metadatos')).order_by('nombre')
        sin_escala=len(Metadatos.objects.filter(escala=None))
        return {'escalas': escalas, 'sin_escala': sin_escala }

    @classmethod
    def capas_agrupadas_por_area_tematica(cls):
        areas_tematicas=AreaTematica.objects.annotate(total=Count('metadatos')).order_by('nombre')
        sin_area_tematica=len(Metadatos.objects.filter(area_tematica=None))
        return {'areas_tematicas': areas_tematicas, 'sin_area_tematica': sin_area_tematica }

    @classmethod
    def mapas_agrupados_por_escala(cls):
        escalas=Escala.objects.annotate(total=Count('mapa')).order_by('nombre')
        sin_escala=len(Mapa.objects.filter(tipo_de_mapa='general', escala=None))
        return {'escalas': escalas, 'sin_escala': sin_escala }
    

#    @classmethod
#     def capas_de_usuario_agrupadas_por_categoria(cls, user, caso_de_uso, qset_capas_inicial=None):
#         capas=ManejadorDePermisos.capas_de_usuario(user, caso_de_uso, qset_capas_inicial).order_by('nombre')
#         if capas is None:
#             return {'categorias': {}, 'sin_categoria': {} }
#         
#         # inicializo las estructuras resultantes
#         categorias={}
#         sin_categoria={'capas':[]}
#         for c in Categoria.objects.all().order_by('nombre'):
#             categorias[c]={'capas':[]}
#         # itero las capas del usuario y completo las estructuras
#         for c in capas:
#             cats = c.metadatos.categorias.all()
#             if len(cats) > 0:
#                 for cat in cats: 
#                     #categorias[cat]['capas'].append(c.dame_titulo)
#                     categorias[cat]['capas'].append(c)
#             else:
#                 #sin_categoria['capas'].append(c.dame_titulo)
#                 sin_categoria['capas'].append(c)
#         # completo los totales
#         for cat, capas in categorias.iteritems():
#             categorias[cat]['total']=len(capas['capas'])
#         sin_categoria['total']=len(sin_categoria['capas'])
#         return {'categorias': categorias, 'sin_categoria': sin_categoria }

    # método específico que genera la estructura necesaria para armar el árbol de capas en el cliente del visor, ordenado por categoría (OBSOLETO)
    @classmethod
    def capas_de_usuario_para_el_visor_por_categoria(cls, user):
        capas=ManejadorDePermisos.capas_de_usuario(user, 'all').order_by('metadatos__titulo','nombre')
        if capas is None:
            return []
        
        categorias={}
        sin_categoria=[]

        # itero las capas del usuario y completo las estructuras por categoría
        for c in capas:
            cats = c.metadatos.categorias.all().order_by('nombre')
            if len(cats) > 0:
                for cat in cats:
                    if cat.nombre not in categorias:
                        categorias[cat.nombre]=[]
                    categorias[cat.nombre].append(c)
            else:
                sin_categoria.append(c)
        
        res=[]
        for cat, capas in sorted(categorias.iteritems()):
            nodes=[]
            for c in capas:
                nodes.append({'text':c.dame_titulo, 'layerId': c.id_capa})
            #categoriaNode={'text': cat.nombre, 'checkable': False, 'nodes': nodes, 'total': len(nodes)}
            categoriaNode={'text': '%s (%s)'%(cat, str(len(nodes))), 'checkable': False, 'nodes': nodes}
            res.append(categoriaNode)
        if len(sin_categoria) > 0: #si hay capas sin categoría
            nodes=[]
            for c in sin_categoria:
                nodes.append({'text':c.dame_titulo, 'layerId': c.id_capa})
            #categoriaNode={'text': u'Sin categoría', 'checkable': False, 'nodes': nodes, 'total': len(nodes)}
            categoriaNode={'text': u'Sin categoría (%s)'%(str(len(nodes))), 'checkable': False, 'nodes': nodes}
            res.append(categoriaNode)
                
        return res
        
    # método específico que genera la estructura necesaria para armar el árbol de capas en el cliente del visor, ordenado por área temática
    @classmethod
    def capas_de_usuario_para_el_visor_por_area_tematica(cls, user):
        capas=ManejadorDePermisos.capas_de_usuario(user, 'all').order_by('metadatos__titulo','nombre')
        if capas is None:
            return []
        
        areas_tematicas={}
        sin_area_tematica=[]

        # itero las capas del usuario y completo la estructuras por área temática
        for c in capas:
            at = c.metadatos.area_tematica
            if at is not None:
                if at.nombre not in areas_tematicas:
                    areas_tematicas[at.nombre]=[]
                areas_tematicas[at.nombre].append(c)
            else:
                sin_area_tematica.append(c)
        
        res=[]
        for cat, capas in sorted(areas_tematicas.iteritems()):
            nodes=[]
            for c in capas:
                nodes.append({'text':c.dame_titulo, 'layerId': c.id_capa})
            #areaTematicaNode={'text': cat.nombre, 'checkable': False, 'nodes': nodes, 'total': len(nodes)}
            areaTematicaNode={'text': '%s (%s)'%(cat, str(len(nodes))), 'checkable': False, 'nodes': nodes}
            res.append(areaTematicaNode)
        if len(sin_area_tematica) > 0: #si hay capas sin área temática
            nodes=[]
            for c in sin_area_tematica:
                nodes.append({'text':c.dame_titulo, 'layerId': c.id_capa})
            #areaTematicaNode={'text': u'Sin área temática', 'checkable': False, 'nodes': nodes, 'total': len(nodes)}
            areaTematicaNode={'text': u'Sin área temática (%s)'%(str(len(nodes))), 'checkable': False, 'nodes': nodes}
            res.append(areaTematicaNode)
                
        return res
    
@receiver(post_save, sender=PermisoDeCapa)
def onPermisoDeCapaPostSave(sender, instance, created, **kwargs):
    print 'onPermisoDeCapaPostSave %s'%(str(instance))
    ManejadorDeMapas.delete_mapfile(instance.user.username)

@receiver(post_delete, sender=PermisoDeCapa)
def onPermisoDeCapaPostDelete(sender, instance, **kwargs):
    print 'onPermisoDeCapaPostDelete %s'%(str(instance))
    ManejadorDeMapas.delete_mapfile(instance.user.username)

@receiver(post_save, sender=PermisoDeCapaPorGrupo)
def onPermisoDeCapaPorGrupoPostSave(sender, instance, created, **kwargs):
    print 'onPermisoDeCapaPorGrupoPostSave %s'%(str(instance))
    for u in instance.group.user_set.all():
    	ManejadorDeMapas.delete_mapfile(u.username)

@receiver(post_delete, sender=PermisoDeCapaPorGrupo)
def onPermisoDeCapaPorGrupoPostDelete(sender, instance, **kwargs):
    print 'onPermisoDeCapaPorGrupoPostDelete %s'%(str(instance))
    for u in instance.group.user_set.all():
    	ManejadorDeMapas.delete_mapfile(u.username)

@receiver(post_save, sender=User)
def onUserPostSave(sender, instance, created, **kwargs):
    print 'onUserPostSave %s'%(str(instance))
    if created:
        mapa_usuario = Mapa.objects.create(owner=instance,nombre=instance.username,id_mapa=instance.username, tipo_de_mapa='user')
        ManejadorDeMapas.regenerar_mapas_de_usuarios([instance])

@receiver(post_save, sender=Group)
def onGroupPostSave(sender, instance, created, **kwargs):
    print 'onGroupPostSave %s'%(str(instance))
    #aca no iria nada: una creacion de grupo ni un rename de grupo recalculan nada
    
@receiver(post_delete, sender=Group)
def onGroupPostDelete(sender, instance, **kwargs):
    print 'onGroupPostDelete %s'%(str(instance))
    #aca no iria nada porque antes ejecuta la senial onPermisoDeCapaPorGrupoPostDelete  
