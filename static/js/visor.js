jQuery.extend(Function.prototype, {
    createDelegate : function(obj, args, appendArgs){
        var method = this;
        return function() {
            var callArgs = args || arguments;
            if(appendArgs === true){
                callArgs = Array.prototype.slice.call(arguments, 0);
                callArgs = callArgs.concat(args);
            }else if(typeof appendArgs == "number"){
                callArgs = Array.prototype.slice.call(arguments, 0); // copy arguments first
                var applyArgs = [appendArgs, 0].concat(args); // create method call params
                Array.prototype.splice.apply(callArgs, applyArgs); // splice them in
            }
            return method.apply(obj || window, callArgs);
        };
    },
    defer : function(millis, obj, args, appendArgs){
        var fn = this.createDelegate(obj, args, appendArgs);
        if(millis){
            return setTimeout(fn, millis);
        }
        fn();
        return 0;
    }
});

jQuery.fn.reverse = [].reverse;

// Definicion del namespace
var mg = mg || {};

mg.Visor = (function() {
    var c, mapa = null, layers = [], baseLayers = {}, overlays, $tree, mapLayers, searchTimeout, layersConfig, contextMarker;

    function redimensionarMapa() {
        $('#mapa').css('height', $(window).height()-180).css('margin', 0);        
        if (mapa) {
            mapa.invalidateSize();            
        }
        $tree.css('max-height', $(window).height()-345);
    }
    
    function stopPropagation(ev) {
        if (ev.stopPropagation) {
            ev.stopPropagation();
        } else {
            ev.cancelBubble = true;
        }            
    }

    function buscarCapa(text) {
        $tree.treeview('collapseAll');
        if (text!='') {
            $tree.treeview('search', [ text, {
              ignoreCase: true,     // case insensitive
              exactMatch: false,    // like or equals
              revealResults: true,  // reveal matching nodes
            }]);
        } else {
            $tree.treeview('clearSearch');
        }
    }

    function loadLayer(layerId, layerName) {
        mapLayers[layerId] = L.tileLayer(c.layerUrlTemplate.replace('$layer', layerId), {
            tms: true,
            continuousWorld: true,
            zIndex: 1
        }); // .addTo(mapa);
        overlays.addLayer(mapLayers[layerId]);
        mapLayers[layerId].layerId = layerId;
        mapLayers[layerId].sldId = 0;
        mapLayers[layerId].tooltip = true;
        mapLayers[layerId].nombre = layerName;
        layersConfig.addLayer(layerId, layerName, 0);
    }

    function unloadLayer(layerId) {
        overlays.removeLayer(mapLayers[layerId]);
        delete mapLayers[layerId];
        updateLayersConfig();        
    }

    function updateLayersConfig() {
        var conf = {
            baseLayer: $('select[name="baselayer"]').val(),
            extent: mapa.getBounds().toBBoxString(),
            layers: []
        };
        $.each($('.layersconfig-list .layersconfig-item'), function(k, v) {
            var l = mapLayers[$(v).attr('data-id')];
            if (l) {
                conf.layers.push({ layerId: l.layerId, sldId: l.sldId, tooltip: l.tooltip });
            }
        });
/*
        var layers = overlays.getLayers();
        $.each(layers, function(k, v) {
            conf.layers.push({ layerId: v.layerId, sldId: v.sldId, tooltip: v.tooltip });
        });
*/
        $('#form-save input[name=layers]').val(JSON.stringify(conf));
        if (conf.layers.length > 0) {
            $('button.save-map').removeClass('disabled');
        } else {
            $('button.save-map').addClass('disabled');
        }
        console.log(JSON.stringify(conf));
    }

    function updateExtent() {
        var conf = JSON.parse($('#form-save input[name=layers]').val());
        conf.extent = mapa.getBounds().toBBoxString();
        $('#form-save input[name=layers]').val(JSON.stringify(conf));        
        // console.log('updated config', JSON.stringify(conf));
    }

    function reorderLayers() {
        overlays.clearLayers();
        $.each($('.layersconfig-list .layersconfig-item'), function(k, v) {
            overlays.addLayer(mapLayers[$(v).attr('data-id')]);
        });
        updateLayersConfig();
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
            sz = mapa.getSize(),
            layersList = [];
        marker.id = '_'+(new Date().getTime());
        $.each($('.layersconfig-list .layersconfig-item').reverse(), function(k, v) {
            var l = mapLayers[$(v).attr('data-id')];
            if (l && l.tooltip) {
                layersList.push(l.layerId)
            }
            // console.log(layersList);
            $.ajax({
                url: '/maps/getlayersinfo/',
                dataType: 'json',
                data: {
                    BBOX: sw.x+','+sw.y+','+ne.x+','+ne.y,
                    I: ev.containerPoint.x,
                    J: ev.containerPoint.y,
                    WIDTH: sz.x,
                    HEIGHT: sz.y,
                    layers: layersList.join(',')
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
        });
        marker.on('popupclose', removeContextMarker, this);
        marker.on('click', removeContextMarker, this);
        contextMarker = marker;
    }

    return {
        init: function(divId, config) { 
            var mapDivId = $('.mg-map')[0].id;

            // Elimino el "Cargando..."
            $('#'+mapDivId).empty();
            $tree = $('.mg-layers').first();

            // El div del mapa tiene que ocupar toda la ventana
            redimensionarMapa();

            $(window).on('resize', function() {
                redimensionarMapa();
            });

            $(document).on('submit', 'form', function () {
                if (this.id!='form-save') {
                    return false;
                }
            });

            if (mg.visor && mg.visor.config) {
                c = mg.visor.config;
                // try {
                    var ext = c.extent.split(',').map(parseFloat);
                    mapa = L.map(mapDivId, {
                        continuousWorld: true,
                        worldCopyJump: false,
                        attributionControl: false,
                        minZoom: 2
                    });
                    try {
                        mapa.fitBounds(
                            L.latLngBounds(
                                L.latLng(ext[1], ext[0]),
                                L.latLng(ext[3], ext[2])
                            )
                        );
                    } catch(e) {
                        mapa.setView([0,0], 2); 
                    }
                    var attribution = L.control.attribution({
                        prefix: ''
                    }).addTo(mapa);

                    L.control.scale({imperial: false}).addTo(mapa);
                    
                    $.each(c.baseLayers, function(k, v) {
                        baseLayers[k] = L.tileLayer(v.url, {
                            tms: v.tms,
                            continuousWorld: true,
                            zIndex: 0
                        });
                    });

                    var baseLayer = baseLayers[c.baseLayer];
                    baseLayer.addTo(mapa);

                    // baseLayers[c.baseLayers[c.baseLayer].nombre].addTo(mapa);
                    overlays = L.layerGroup({ zIndex: 1 }).addTo(mapa);

                    // L.control.layers(baseLayers, {}, { 'position': 'bottomleft' }).addTo(mapa);

                    var ref_layer = L.tileLayer(c.baseLayers[c.baseLayer].url, {
                        tms: c.baseLayers[c.baseLayer].tms,
                        continuousWorld: true
                    });

                    var miniMap = new L.Control.MiniMap(ref_layer, { toggleDisplay: true, minimized: true }).addTo(mapa);

                    layersConfig = L.control.layersConfig({
                        position: 'topright',
                        title: 'Capas',
                        onRemoveLayer: function(layerId) {
                            // unloadLayer(layerId);
                            var checkedNodes = $tree.treeview('getChecked');
                            $.each(checkedNodes, function(k, v) {
                                if (v.layerId==layerId) {
                                    $tree.treeview('uncheckNode', v.nodeId);
                                    return false;
                                }
                            });
                            updateLayersConfig();
                        },
                        onReorderLayers: reorderLayers,
                        onLayerInfoChange: function(layerId, status) {
                            try {
                                mapLayers[layerId].tooltip = status;
                            } catch(e) {
                                console.log(e);
                            }
                            updateLayersConfig();
                        },
                        onStyleChange: function(layerId, sldId) {
                            try {
                                mapLayers[layerId].setUrl(c.layerUrlTemplate.replace('$layer', layerId+'$'+sldId));
                                mapLayers[layerId].sldId = sldId;
                            } catch(e) {
                                console.log(e);
                            }
                            updateLayersConfig();
                        }
                    }).addTo(mapa);

                    // Esto es para evitar que los clicks sobre los elementos flotantes sobre el
                    // mapa sean capturados por el mapa y generen movimientos no previstos        
                    $('.leaflet-control')
                        .on('mousedown', stopPropagation)
                        .on('dblclick', stopPropagation);

                    mapa.on('click', onContextMenu, this);
                    mapa.on('moveend', updateExtent, this);
                    mapa.on('zoomend', updateExtent, this);

                
                // } catch(e) {
                //     console.log('Se produjo un error al inicializar el mapa. Revise la configuración.');
                // }
                
                
                mapLayers = {};

                // Cargamos las capas iniciales
                if (c.initialLayers && c.initialLayers.length > 0) {
                    for (var i=0,l=c.initialLayers.length;i<l;i++) {
                        loadLayer(c.initialLayers[i].layerId);
                        mapLayers[c.initialLayers[i].layerId].tooltip = c.initialLayers[i].tooltip;
                        if (c.initialLayers[i].sldId!=0) {
                            try {
                                mapLayers[c.initialLayers[i].layerId].setUrl(c.layerUrlTemplate.replace('$layer', c.initialLayers[i].layerId+'$'+c.initialLayers[i].sldId));
                                mapLayers[c.initialLayers[i].layerId].sldId = c.initialLayers[i].sldId;
                            } catch(e) {
                                console.log(e);
                            }
                        }
                    }
                    updateLayersConfig();
                    // Agregamos checkbox a las capas iniciales
                    for (var i=0,l=c.layers.length;i<l;i++) {
                        $.each(c.layers[i].nodes, function(k, v) {
                            if (mapLayers[v.layerId]) {
                               v.state = { checked: true };
                               mapLayers[v.layerId].nombre = v.text;
                            }
                        });
                    }
                    var layers = overlays.getLayers();
                    $.each(layers, function(k, v) {
                        layersConfig.addLayer(v.layerId, v.nombre, v.sldId, v.tooltip);
                    });                    
                } else {
                    $('button.save-map').addClass('disabled');
                }


                // Inicializamos el tree view
                $tree.treeview({
                    data: c.layers, 
                    showCheckbox: true, 
                    showBorder: false, 
                    multiSelect: false, 
                    highlightSelected: false, 
                    levels: 0,
                    searchResultBackColor: '#fcf8e3',
                    searchResultColor: '#4a2d1b'
                });
                $('input[name="buscar"]').on('keyup', function(event) {
                    clearTimeout(searchTimeout);
                    var text = $(this).val();
                    if (text!='') {
                        searchTimeout=buscarCapa.defer(600, this, [$(this).val()]);
                    } else {
                        $tree.treeview('collapseAll');
                        $tree.treeview('clearSearch');                        
                    }
                });
                $tree.on('nodeChecked', function(event, data) {
                    loadLayer(data.layerId, data.text);
                    updateLayersConfig();
                });
                /*
                $tree.on('nodeSelected', function(event, node) {
                    $tree.treeview('toggleNodeChecked', node);
                });
                */
                $tree.on('nodeUnchecked', function(event, data) {
                    // mapa.removeLayer(mapLayers[data.layerId]);
                    unloadLayer(data.layerId);
                    layersConfig.removeLayer(data.layerId);
                });
                $.each(c.baseLayers, function(k, v) {
                    $('select[name="baselayer"]').append('<option value="'+k+'" '+(c.baseLayer==k?'selected':'')+'>'+v.nombre+'</option>');
                });
                $('select[name="baselayer"]').on('change', function(ev) {
                    mapa.removeLayer(baseLayer);
                    baseLayer = baseLayers[$(this).val()]; 
                    baseLayer.addTo(mapa);
                    updateLayersConfig();
                });

                $("button.save-map.create").click(function(e) {
                    e.preventDefault();
                    $('#modal-save').modal('show');
                });

                $('#modal-save button[type="submit"]').click(function(e) {
                    if ($('#modal-save input[name="title"]').val()=='') {
                        $('#modal-save .form-group').addClass('has-error');
                        $('#modal-save .help-block').removeClass('hidden');
                        return false;
                    } else {
                        $('#modal-save .form-group').removeClass('has-error').addClass('has-success');
                        $('#modal-save .help-block').addClass('hidden');
                        return true;
                    }
                });

            } else {
                console.log('Missing configuration mg.visor.config');
            }
        }
    };
})();