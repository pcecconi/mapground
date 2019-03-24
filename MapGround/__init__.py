class MapGroundException(Exception):
	"""Clase base para manejar excepciones"""
	pass

class LayerNotFound(MapGroundException):
	"""Capa importable no encontrada"""
	pass

class LayerAlreadyExists(MapGroundException):
	"""Capa ya existente"""
	pass

class LayerImportError(MapGroundException):
	"""Error al importar capa"""
	pass
