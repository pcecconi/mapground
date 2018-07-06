# -*- coding: utf-8 -*-
from django.conf import settings
# from mapcache.settings import MAPSERVER_URL
import os
import mapscript

MAPA_DEFAULT_SRS = 3857
MAPA_DEFAULT_SIZE = (110, 150)
MAPA_DEFAULT_EXTENT = (-20037508.3427892480, -20037508.3427892480, 20037508.3427892480, 20037508.3427892480) #3857 whole world
MAPA_DEFAULT_IMAGECOLOR = '#C6E2F2' # debe ser formato Hexa

MAPA_FONTSET_FILENAME = os.path.join(settings.MAPAS_PATH, 'fonts.txt')
MAPA_SYMBOLSET_FILENAME = os.path.join(settings.MAPAS_PATH, 'symbols.txt')
MAPA_DATA_PATH = '../data'
MAPA_ERRORFILE = os.path.join(settings.MAPAS_PATH, 'map-error.log')

class MS_LAYER_TYPE: 
    MS_LAYER_POINT, MS_LAYER_LINE, MS_LAYER_POLYGON, MS_LAYER_RASTER, MS_LAYER_ANNOTATION, MS_LAYER_QUERY, MS_LAYER_CIRCLE, MS_LAYER_TILEINDEX, MS_LAYER_CHART = range(9)

def __agregar_simbologia_basica__(layer):
    class1 = mapscript.classObj(layer)
    class1.name = 'Default'
    style = mapscript.styleObj(class1)
    if layer.type==mapscript.MS_LAYER_POINT:
        style.symbolname='circle'
        style.size=8
        style.minsize=8
        style.maxsize=10
        style.maxwidth=2
        style.outlinecolor.setRGB(30, 30, 30)
        style.color.setRGB(31, 120, 180)
    elif layer.type==mapscript.MS_LAYER_POLYGON:
        style.outlinecolor.setRGB(126, 109, 83)
        style.color.setRGB(210, 182, 138)
    elif layer.type==mapscript.MS_LAYER_LINE:
        style.color.setRGB(76, 38, 0)
        style.width=4
        style.minwidth=4
        style.maxwidth=6
        style2 = mapscript.styleObj(class1)
        style2.color.setRGB(255, 206, 128)
        style2.width=2
        style2.minwidth=2
        style2.maxwidth=4

def create_mapfile(data, save=True):
    mapa = mapscript.mapObj()
    mapa.name='mapa_'+unicode(data['idMapa'])

    try:
        if data['imageColor']['type'] == 'hex':
            mapa.imagecolor.setHex(data['imageColor']['color'])
        else:
            mapa.imagecolor.setRGB(*(data['imageColor']['color']))
    except:
        mapa.imagecolor.setHex(MAPA_DEFAULT_IMAGECOLOR)
    
    mapa.setSymbolSet(MAPA_SYMBOLSET_FILENAME)
    mapa.setFontSet(MAPA_FONTSET_FILENAME)
    mapa.shapepath=MAPA_DATA_PATH

    mapa.outputformat.transparent=True
        
    mapa.setProjection('epsg:%s'%(data['srid']))
    if data['srid']=='4326':
        mapa.units=mapscript.MS_DD
    else:
        mapa.units=mapscript.MS_METERS

    mapa.legend.updateFromString('LEGEND\n  KEYSIZE 20 10\n  KEYSPACING 5 5\n  LABEL\n    SIZE 10\n    OFFSET 0 0\n    SHADOWSIZE 1 1\n    TYPE TRUETYPE\n  FONT "Swz721lc"\nEND # LABEL\n  STATUS OFF\nEND # LEGEND\n\n')
    # primero seteamos extent, luego size. sino hay un comportamiento extranio y el extent no se respeta, quizas para igualar relaciones de aspecto entre ambos
    try:
        mapa.setExtent(*(data['mapFullExtent'])) # si tiene un extent overrideado
    except:
        if data['mapType'] in ('user', 'public_layers'): # en estos casos no los calculamos
            mapa.setExtent(*(MAPA_DEFAULT_EXTENT))
        else:
            try:
                mapa.setExtent(*(data['mapBoundingBox']))
            except:
                mapa.setExtent(*(MAPA_DEFAULT_EXTENT))
    try:
        mapa.setSize(*(data['mapSize']))
    except:
        mapa.setSize(*(MAPA_DEFAULT_SIZE))
                
    output_geojson=mapscript.outputFormatObj('OGR/GEOJSON', 'GeoJson')
    output_geojson.setMimetype('application/json; subtype=geojson')
    output_geojson.setOption('STORAGE', 'stream')
    output_geojson.setOption('FORM', 'SIMPLE')
    mapa.appendOutputFormat(output_geojson)

    output_shapefile=mapscript.outputFormatObj('OGR/ESRI Shapefile', 'ShapeZip')
    output_shapefile.setMimetype('application/shapefile')
    output_shapefile.setOption('STORAGE', 'filesystem')
    output_shapefile.setOption('FORM', 'zip')
    output_shapefile.setOption('FILENAME', data['fileName']+'.zip')
    mapa.appendOutputFormat(output_shapefile)

    output_csv=mapscript.outputFormatObj('OGR/CSV', 'CSV')
    output_csv.setMimetype('text/csv')
    # output_csv.setOption('LCO:GEOMETRY', 'AS_WKT')
    output_csv.setOption('STORAGE', 'filesystem')
    output_csv.setOption('FORM', 'simple')
    output_csv.setOption('FILENAME', data['fileName']+'.csv')
    mapa.appendOutputFormat(output_csv)

    mapa.setConfigOption('MS_ERRORFILE',MAPA_ERRORFILE) 
    mapa.setConfigOption('PROJ_LIB',settings.PROJ_LIB)
    mapa.setConfigOption('MS_OPENLAYERS_JS_URL',settings.MS_OPENLAYERS_JS_URL)

    mapa.legend.template = 'templates/legend.html' # TODO: general o solo WMS?
    # mapa.web.validation.set('TEMPLATE', '[a-z/.]+') # TODO: general o solo WMS?
    mapa.web.template = 'templates/mapa-interactivo.html' # TODO: general o solo WMS?
    
    mapa.web.imagepath = settings.MAP_WEB_IMAGEPATH
    mapa.web.imageurl = settings.MAP_WEB_IMAGEURL

    # mapa.web.template = 'blank.html' # siempre?
    try:
        for k, v in data['metadata'].iteritems():
            mapa.setMetaData(k, v)
    except:
        pass # No metadata

    try:
        for layer_def in data['layers']:
            mapa.insertLayer(create_ms_layer(layer_def))
    except:
        print "Failed to insert layers on mapfile"
    
    if save:
        mapa.save(os.path.join(settings.MAPAS_PATH, data['idMapa']+'.map'))
        print "......mapa guardado %s"%(data['idMapa']+'.map')

    return mapa

def create_ms_layer(data):
    layer = mapscript.layerObj()
    layer.name = data['layerName']
    layer.status = mapscript.MS_ON
    layer.group = 'default' #siempre        
    layer.template = 'blank.html' 
            
    if data['connectionType']=='WMS':
        layer.type=mapscript.MS_LAYER_RASTER
        layer.connectiontype = mapscript.MS_WMS
        layer.connection = data['layerConnection']
        
        layer.setMetaData('wms_srs', 'epsg:3857')
        layer.setMetaData('wms_name', data['layerName'])
        layer.setMetaData('wms_server_version', '1.1.1')
        layer.setMetaData('wms_format', 'image/png')
        if data['sldUrl'] is not None:
            layer.setMetaData('wms_sld_url', data['sldUrl'])
    
    elif data['connectionType']=='POSTGIS':
        layer.type=eval('mapscript.MS_LAYER_'+data['layerType'])
        
        # layer.sizeunits = mapscript.MS_INCHES
        layer.addProcessing('LABEL_NO_CLIP=ON') 
        layer.addProcessing('CLOSE_CONNECTION=DEFER')
        layer.connectiontype = mapscript.MS_POSTGIS
        layer.connection = data['layerConnection']

        srid = data['srid']
        layer.data = data['layerData']
        #proj='epsg:%s'%(unicode(srid)) if srid!=None else self.capa.dame_projection

        layer.setProjection('epsg:%s'%(unicode(srid)))

        layer.setMetaData('ows_title', data['layerTitle'])
        layer.setMetaData('gml_types', 'auto')
        #layer.setMetaData('ows_srs','%s epsg:4326'%(proj)) # este campo lo llena el mapa 
        layer.setMetaData('gml_include_items','all') # por ahora queda asi, y ademas se suman los campos especificos
        layer.setMetaData('gml_featureid','gid') 
        layer.setMetaData('wms_enable_request', '*')
        layer.setMetaData('wfs_enable_request', '*')

        if len(data['metadataIncludeItems'])>0:
            layer.setMetaData('gml_include_items',','.join(data['metadataIncludeItems']))
        for alias in data['metadataAliases']:
            layer.setMetaData('gml_%s_alias'%(alias[0]),alias[1])
        
        if data['layerDefinitionOverride']!='':
            try:
                layer.updateFromString(data['layerDefinitionOverride'])
            except:
                pass
        else:
            __agregar_simbologia_basica__(layer)
            
    try:
        for k, v in data['metadata'].iteritems():
            layer.setMetaData(k, v)
    except:
        pass # No metadata

    return layer

def get_wms_url(map_id):
    return '%s?map=%s.map'%(
        settings.MAPSERVER_URL, # url mapserver cgi
        os.path.join(settings.MAPAS_PATH, map_id) # absolute mapfile path
    )

def get_wms_request_url(map_id, layers, srs, width, height, extent, sld_url=''):
    wms_req_url = '%s&LAYERS=%s&SRS=epsg:%s&MAP_RESOLUTION=96&SERVICE=WMS&FORMAT=image/png&REQUEST=GetMap&HEIGHT=%d&FORMAT_OPTIONS=dpi:96&WIDTH=%d&VERSION=1.1.1&BBOX=%s&STYLES=&TRANSPARENT=TRUE&DPI=96'
    url = wms_req_url%(
        get_wms_url(map_id),
        layers,
        srs,
        height,
        width,
        extent
    )
    if sld_url!='':
        url += '&sld='+sld_url
    print "get_wms_request_url: %s"%url
    return url

def get_legend_graphic_url(map_id, layer_name, sld_url=''):
    legend_url = '%s&SERVICE=WMS&VERSION=1.3.0&SLD_VERSION=1.1.0&REQUEST=GetLegendGraphic&FORMAT=image/png&LAYER=%s&STYLE='
    url = legend_url%(
        get_wms_url(map_id),
        layer_name
    )
    if sld_url and sld_url!='':
        url += '&sld='+sld_url
    return url

def get_map_browser_url(map_id):
    return '%s&mode=browse&layers=all'%(
        get_wms_url(map_id)
    )

def get_featureinfo_url(map_id, bbox, width, height, query_layers, i, j):
    req_url = '%s&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetFeatureInfo&BBOX=%s&CRS=epsg:3857&WIDTH=%s&HEIGHT=%s&LAYERS=default&STYLES=&FORMAT=image/png&QUERY_LAYERS=%s&INFO_FORMAT=application/vnd.ogc.gml&I=%s&J=%s'
    return req_url%(
        get_wms_url(map_id),
        bbox,
        width,
        height,
        query_layers,
        i,
        j
    )

def get_feature_url(map_id, typename, outputformat):
    req_url = '%s&SERVICE=WFS&VERSION=1.0.0&REQUEST=getfeature&TYPENAME=%s&outputformat=%s'
    return req_url%(
        get_wms_url(map_id),
        typename,
        outputformat
    )
