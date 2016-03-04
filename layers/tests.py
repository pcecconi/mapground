from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from layers.models import Capa

def crear_capa(owner_id=1, tipo_de_geometria_id=1, nombre='prueba'):
    return Capa.objects.create(owner_id=owner_id, tipo_de_geometria_id=tipo_de_geometria_id,nombre=nombre,esquema='esquema',tabla=nombre)

class CapaMethodTests(TestCase):

    def test_crear_capa_crea_dependencias_1a1(self):
        """
        Toda Capa debe tener un Metadatos y un MapServerLayer
        """
        capa=crear_capa()
        self.assertEqual(capa.metadatos is not None, True)
        self.assertEqual(capa.mapserverlayer is not None, True)

    def test_detalle_capa_por_id(self):
        ''' Detalle Capa por id'''
        c = Client()
        response = c.get(reverse('layers:detalle_capa_por_id', args=(1,)))
        self.assertEqual(response.status_code, 404)
        capa=crear_capa(nombre='prueba333')
        response = c.get(reverse('layers:detalle_capa_por_id', args=(capa.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Esquema')
        self.assertEqual(response.context['capa'].nombre, 'prueba333')
        
    def test_ultimas(self):
        ''' Test de ultimas '''
        c = Client()
        response = c.get(reverse('layers:ultimas'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['lista_capas'], [])
        
        capa=crear_capa(nombre='prueba333')
        capa=crear_capa(nombre='prueba444')
        response = c.get(reverse('layers:ultimas'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['lista_capas']), 2)

    def test_buscar_algo(self):
         '''Tengo que poder buscar algo '''
#         #self.assertEqual(7, User.objects.all().count())
         c = Client()
         response = c.get(reverse('layers:buscar'))
         self.assertEqual(response.content, '[]')
         
         capa=crear_capa(nombre='prueba333')
         response = c.get(reverse('layers:buscar'))
         self.assertEqual(response.content, '[]')
         #response = c.get(reverse('layers:buscar',kwargs={'texto':'prueba333'})) #ESTO NO ESTA SOPORTADO!
         response = c.get(reverse('layers:buscar')+'?texto=prueba333')
         self.assertEqual(response.content == '[]', False)

         
#         #raise Exception (response)
#         # Since we are not authenticated, we should not be able to access it
#         #self.failUnlessEqual(response.status_code, 302)
#         # but if we log in ...
#         #c.login(username='admin', password='admin')
#         # ... all should be good
#         #response = c.get(reverse('layer_metadata', args=('base:CA',)))
#         #self.failUnlessEqual(response.status_code, 200)
        