# -*- coding: utf-8 -*-

from django.conf import settings
import sys, os
import xml.etree.ElementTree as ET
from os.path import isfile
from string import Template

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
MAPCACHE_CONFIG = os.path.join(settings.MAPCACHE_CONFIG_ROOT, 'mapcache.xml')
MAPFILES_DIR = os.path.join(settings.MAPCACHE_CONFIG_ROOT, 'mapfiles')
TEMPLATES_DIR = os.path.join(CURR_DIR, 'templates')
DEFAULT_SRID = '3857'

def __build_map_name(map_id, sld_id):
    return (map_id+'$'+str(sld_id) if str(sld_id)!='' else map_id)

def remove_map(map_id, sld_id=''):
    map_name = __build_map_name(map_id, sld_id)
    print '\nMapCache: - '+map_name+'\n'
    try:
        tree = ET.parse(MAPCACHE_CONFIG)
        root = tree.getroot()
        elems = root.findall("*[@name='"+map_name+"']")
        if len(elems) > 0:
            for child in elems:
                root.remove(child)
            
            tree.write(MAPCACHE_CONFIG, encoding='utf-8')
            tileset = os.path.join(settings.MAPCACHE_CACHE_ROOT, map_name+'.mbtiles')
            if isfile(tileset):
                try:
                    os.remove(tileset)
                except:
                    print '\nMapCache: Failed to remove tileset for "%s"'%(map_name)
            else:
                print '\nMapCache: Tileset "%s" was not found.'%(map_name)
        else:
            print '\nMapCache: %s no existia.\n'%map_name
    except:
		print "MapCache: Failed to remove map '%s'"%(map_name)

def add_map(map_id, layers='default', srid=DEFAULT_SRID, sld_id='', sld=''):
    tree = ET.parse(MAPCACHE_CONFIG)
    root = tree.getroot()
    map_name = __build_map_name(map_id, sld_id)
    if len(root.findall("*[@name='"+map_name+"']")) == 0:
        if isfile(os.path.join(MAPFILES_DIR, map_id+'.map')):
            d=dict(mapname=map_name, cache_path=settings.MAPCACHE_CACHE_ROOT, map_path=MAPFILES_DIR)
            with open(os.path.join(TEMPLATES_DIR, 'cache.template'), 'r') as file:
                template=Template(file.read())
                root.append(ET.fromstring(template.substitute(d)))

            src_template = 'source_sld.template' if sld != '' else 'source.template'
            with open(os.path.join(TEMPLATES_DIR, src_template), 'r') as file:
                template=Template(file.read())
                d['mapfile'] = map_id
                d['layers'] = layers
                d['sld'] = sld
                d['mapserver_url'] = settings.MAPSERVER_URL
                root.append(ET.fromstring(template.substitute(d)))
        
            with open(os.path.join(TEMPLATES_DIR, 'tileset_%s.template'%srid), 'r') as file:
                template=Template(file.read())
                root.append(ET.fromstring(template.substitute(d)))    	
            
            try:
                tree.write(MAPCACHE_CONFIG, encoding='utf-8')
            except: 
                print ('\nMapCache: No se pudo escribir %s')%(MAPCACHE_CONFIG)

            print ('\nMapCache: + %s\n')%(map_name)
        else:
            print '\nMapCache: Error: No se encontro el mapa: %s\n'%map_name
    else:
        print '\nMapCache: Error: %s ya existe.\n'%map_name
