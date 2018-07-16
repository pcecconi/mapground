from background_task import background
from django.utils import timezone
from mapcache import mapcache


@background(schedule=timezone.now())
def add_tileset(map_id, layers='default', srid='3857', sld_id='', sld=''):
    mapcache.add_map(map_id, layers, srid, sld_id, sld)


@background(schedule=timezone.now())
def add_or_replace_tileset(map_id, layers='default', srid='3857', sld_id='', sld=''):
    mapcache.add_or_replace_map(map_id, layers, srid, sld_id, sld)


@background(schedule=timezone.now())
def rm_tileset(map_id, sld_id=''):
    mapcache.remove_map(map_id, sld_id)
