# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from mapcache import mapcache

class Command(BaseCommand):
    help = 'Agrega un set de tiles a MapCache para los mapas indicados'

    def add_arguments(self, parser):
        parser.add_argument('mapfile', nargs='+', help="Nombre del mapa sin extension")

    def handle(self, *args, **options):
        for mapfile in options['mapfile']:
            try:
                mapcache.add_map(mapfile)
            except:
                raise CommandError('Se produjo un error al intentar agregar un tileset para "%s"' % mapfile)

            self.stdout.write(self.style.SUCCESS('Se agrego un tileset para el mapa "%s"' % mapfile))