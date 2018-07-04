# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from mapcache import mapcache

class Command(BaseCommand):
    help = 'Borra los set de tiles indicados de MapCache'

    def add_arguments(self, parser):
        parser.add_argument('tileset', nargs='+', help="Nombre del tileset")

    def handle(self, *args, **options):
        for tileset in options['tileset']:
            try:
                mapcache.remove_map(tileset)
            except:
                raise CommandError('Se produjo un error al intentar borrar el tileset "%s":%s' % (tileset))

            self.stdout.write(self.style.SUCCESS('Tileset "%s" borrado.' % tileset))