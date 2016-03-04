// Definicion del namespace
var mg = mg || {};

mg.MapApp = (function() {
	var mapa = null, layers = [], contextMarker, enableContextInfo=true;

    function redimensionarMapa() {
        $('#mapa').css('width', $(window).width()).css('height', $(window).height()).css('margin', 0);        
        if (mapa) {
            mapa.invalidateSize();            
        }
    }

    function getQueryParameters(str) {
        str = str || document.location.search;
        return (!str && {}) || str.replace(/(^\?)/,'').split("&").map(function(n){return n = n.split("="),this[n[0]] = decodeURIComponent(n[1].replace(/\+/g, ' ')),this}.bind({}))[0];
    }    
    
    function stopPropagation(ev) {
        if (ev.stopPropagation) {
            ev.stopPropagation();
        } else {
            ev.cancelBubble = true;
        }            
    }

    function removeContextMarker() {
        contextMarker.off('popupclose');
        contextMarker.unbindPopup();
        try {
            mapa.removeLayer(contextMarker);
        } catch(e) {
            console.log(e);
        }
        contextMarker = undefined;
    }

    function onContextMenu(ev) {
        if (contextMarker) {
            removeContextMarker();
        }
        var marker = L.marker(ev.latlng).addTo(mapa),
            self = this;
        var ne = L.CRS.EPSG3857.project(mapa.getBounds()._northEast), 
            sw = L.CRS.EPSG3857.project(mapa.getBounds()._southWest),
            sz = mapa.getSize();
        marker.id = '_'+(new Date().getTime());
        if (enableContextInfo) {
            $.ajax({
                url: '/maps/getfeatureinfo/'+mg.map.config.mapid+'/',
                dataType: 'json',
                data: {
                    BBOX: sw.x+','+sw.y+','+ne.x+','+ne.y,
                    I: ev.containerPoint.x,
                    J: ev.containerPoint.y,
                    WIDTH: sz.x,
                    HEIGHT: sz.y
                },
                success: function(data) {
                    if (marker.id == contextMarker.id) {
                        if (data.count > 0) {
                            var content='<h3>'+data.layers[0].name+'</h3><ul>';
                            $.each(data.layers[0].items[0], function(k, v) {
                                content+='<li><b>'+k+': </b>'+v+'</li>';
                            });
                            content+='</ul>';
                            marker.getPopup().setContent(content);
                            // marker.getPopup().setContent(self.templateMarkersMenu({ titulo: data.resultados[0].objetos[0].nombre, subtitulo: data.resultados[0].clase, markerClass: 'context', id: -2, latlng: ev.latlng.lat+','+ev.latlng.lng }));
                        } else {
                            marker.getPopup().setContent('<p>No se halló información para este punto.</p>');
                        }
                    }
                },
                timeout: 10000,
                error: function(e) { 
                    marker.getPopup().setContent('<p>Se produjo un error al intentar acceder a la información contextual.</p>');                      
                }
            });     
            
            marker.bindPopup('Buscando información...').openPopup();
        }
        marker.on('popupclose', removeContextMarker, this);
        marker.on('click', removeContextMarker, this);
        contextMarker = marker;
    }

	return {
		init: function(divId, config) { 
            var mapDivId = $('.mg-map')[0].id;

            // Elimino el "Cargando..."
            $('#'+mapDivId).empty();

            // El div del mapa tiene que ocupar toda la ventana
            redimensionarMapa();

            $(window).on('resize', function() {
                redimensionarMapa();
            });

            var params = getQueryParameters();

            if (mg.map && mg.map.config) {
                var c = mg.map.config,
                    ext = c.extent.split(' ').map(parseFloat);
                try {
                    mapa = L.map(mapDivId, {
                        continuousWorld: true,
                        worldCopyJump: false,
                        attributionControl: false,
                        minZoom: 2
                    }).fitBounds(
                        L.latLngBounds(
                            L.latLng(ext[1], ext[0]),
                            L.latLng(ext[3], ext[2])
                        )
                    ); 
                    var attribution = L.control.attribution({
                        prefix: ''
                    }).addTo(mapa);

                    var base_layer = L.tileLayer(c.baselayerurl, {
                        tms: c.tmsbaselayer=='False'?false:true,
                        continuousWorld: true
                    }).addTo(mapa);

                    var ref_layer = L.tileLayer(c.baselayerurl, {
                        tms: true,
                        continuousWorld: true
                    });

                    var layer = L.tileLayer(c.onlineresource, {
                        attribution: '<b>Fuente:</b> '+c.attribution,
                        tms: true,
                        continuousWorld: true
                    }).addTo(mapa);

                    L.control.scale({imperial: false}).addTo(mapa);

                    mapa.addControl(new mg.Abstract(c, '<p class="legend_title">Referencias</p>\
<img src="/media/'+c.mapid+'_legend.png?t='+Math.floor(Math.random()*100001)+'"/>', { abstract: (params.abstract && params.abstract != 0), title: (params.title && params.title != 0), minimized: (params.refs && params.refs == 0) }));

                    var miniMap = new L.Control.MiniMap(ref_layer, { toggleDisplay: true, minimized: true }).addTo(mapa);
                    
                    mapa.on('click', onContextMenu, this);

                    // Esto es para evitar que los clicks sobre los elementos flotantes sobre el
                    // mapa sean capturados por el mapa y generen movimientos no previstos        
                    $('.leaflet-control')
                        .on('mousedown', stopPropagation)
                        .on('dblclick', stopPropagation);

                } catch(e) {
                    console.log('Se produjo un error al inicializar el mapa. Revise la configuración.');
                }

            } else {
                console.log('Missing configuration mg.map.config');
            }
		}
	};
})();