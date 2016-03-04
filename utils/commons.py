# -*- coding: utf-8 -*-
import re
import unicodedata
import urllib2
# from django.conf import settings
# from django.contrib.gis.geos import Point, Polygon
# from UsigGml import *
# from itertools import izip
# from util.unicode_csv import UnicodeWriter
# from api.settings import *
# import time, datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import Point

nombre_de_funcion_de_javascript_valido = re.compile(r"^[$A-Z_][0-9A-Z_$]*$", re.IGNORECASE)

def es_un_nombre_de_funcion_de_javascript_valido(nombre_de_funcion_de_javascript):
    if nombre_de_funcion_de_javascript == '':
        return False
    if not isinstance(nombre_de_funcion_de_javascript, str) and not isinstance(nombre_de_funcion_de_javascript, unicode):
        return False
    if ((re.match(nombre_de_funcion_de_javascript_valido, nombre_de_funcion_de_javascript)) is None):
        return False
    return True    

# dados un string de dato y un string de callback, aplica el callback si tiene un nombre de función javascript válido
def aplicar_callback(data, callback):
    # TODO: ver si conviene agregar el chequeo de string de data 
    if es_un_nombre_de_funcion_de_javascript_valido(callback):
        return callback+'('+data+')'
    return data
    
# normaliza un string quitándole acentos y caracteres especiales
def normalizar_texto(texto, to_lower=True):
    if to_lower:
        texto = unicode(texto).lower()
    texto = ''.join((c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')) # reemplazamos ñ y acentos por n y sin acentos
    #texto = re.sub(unicode(r'[^\w\d\sáÁäÄéÉëËíÍïÏóÓöÖúÚüÜÿŸñÑ]','utf-8'),lambda mo: '',texto)

    texto = re.sub(unicode(r'[^\w\d\s]','utf-8'),lambda mo: '', re.sub('([,;:./-])(?!\s)', r'\1 ', re.sub('\.(?!(\S[^. ])|\d)', '', texto))) #separa siglas separadas por . , : . / -
#    texto = re.sub(unicode(r'[^\w\d\s]','utf-8'),lambda mo: ' ',texto) # reemplazamos caracteres especiales por espacios
    texto = re.sub(unicode(r'[\s_]+','utf-8'), lambda mo: '_', texto) # reemplazamos cadenas de espacios o de _ por un _
    texto = texto.strip('_')
    return texto


def paginar_y_elegir_pagina(lista_objetos, pagina, cantidad_por_pagina):
    paginator = Paginator(lista_objetos, cantidad_por_pagina)
    try:
        lista_objetos = paginator.page(pagina)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        lista_objetos = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        lista_objetos = paginator.page(paginator.num_pages)
    return lista_objetos


# convierte un QueryDict a Dict
def queryDictToDict(request, omitir_callback=True):
    request_dict=dict()
    for item in request.GET.items():
        if not (omitir_callback and (item[0]=='callback' or item[0]=='_')):
            request_dict[item[0]]=item[1]
    return request_dict

# parsea un string de tipo 'Comma-Separated-Integers' y devuelve una lista
def parsear_csi_input(texto):
    res=[]
    if texto != '':
        texto = texto.split(',')
        for s in texto:
            try:
                res.append(int(s.strip()))
            except:
                pass
    return res

# parsea un string de tipo 'Comma-Separated-Strings' y devuelve una lista
def parsear_css_input(texto):
    res=[]
    if texto != '':
        texto = texto.split(',')
        for s in texto:
            try:
                res.append(s.strip())
            except:
                pass
    return res

# parsea un string que representa un bbox separado por comas y devuelve None o una 4-upla
def parsear_bbox(str_bbox):
    try:
        vals=str_bbox.split(',')
        if len(vals) != 4:
            return None
        for v in vals:
            v= float(v)
        return vals
    except:
        return None

def urlToFile(url, filename):
    try:
        proxy = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)

        with open(filename,'wb') as f:
            f.write(urllib2.urlopen(url).read())
            f.close()
    except:
        print "Error saving url %s to file %s"%(url, filename)
        return False
    return True


def coordConvert(lat, lng, sridFrom, sridTo):
    fromCoord = SpatialReference(sridFrom)
    toCoord = SpatialReference(sridTo)
    trans = CoordTransform(fromCoord, toCoord)
    
    pnt = Point(lat, lng, srid=sridFrom)
    pnt.transform(trans)
    return pnt
