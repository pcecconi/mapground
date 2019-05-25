/*
 * L.Control.LayersConfig 
 */

L.Control.LayersConfig = L.Control.extend({
	options: {
		position: 'topleft',
		title: 'Select layers',
		symbol: '<span class="glyphicon glyphicon-th-list"></span>',
		itemsTemplate: 'layersconfig-items',
		layers: {},
		onRemoveLayer: undefined,
		onReorderLayers: undefined
		// layers: [
		// 	{nombre: 'Provincias Argentinas del Rio de la Concha de tu Madre y si querés un título largo acá tenés', id:'admin_provincias', desc:'Sin descripción'}, 
		// 	{nombre: 'Ecoregiones', id:'admin_ecoregiones', desc:'Sin descripción'},
		// ]
	},
	self: this,
	slds: {
		/*
		'mrapis_ecoregiones': [
			{"url": "/media/sld/mrapis_ecoregiones_ecorregiones.png", "descripcion": "", "id_archivo_sld": "mrapis_ecoregiones_ecorregiones.sld", "id": 238, "default": true},
			{"url": "/media/sld/lmarcos_variacion_de_poblacion_91_01_variacion_poblacion_91_01.png", "descripcion": "", "id_archivo_sld": "mrapis_ecoregiones_ecorregiones2.sld", "id": 239, "default": false}
		]
		*/		
	},
	bands: {},

	onAdd: function (map) {
		var zoomName = 'leaflet-control-layersconfig',
		    container = L.DomUtil.create('div', zoomName + ' leaflet-bar');
		this.sidebarContainer = L.DomUtil.create('div', 'sidebar-right', container);

		this._map = map;

		this._button = this._createButton(
		        this.options.symbol, this.options.title,
		        zoomName + '-btn',  container, this._onClick,  this);

		var this_ptr = this;
        this._rightSidebar = L.control.sidebar(this.sidebarContainer, {
            position: 'right',
            closeButton: true,
            onClose: function () {
            	this_ptr._onClose()
            }
        });

        // var content = '<h1>Capas</h1><ul class="layersconfig-list">',
        // 	template = $('#'+this.options.itemsTemplate).html();
        // for (var i=0,l=this.options.layers.length;i<l;i++) {
        // 	content+=template.replace(/\$id/g, this.options.layers[i].id)
        // 		.replace(/\$nombre/g, this.options.layers[i].nombre)
        // 		.replace(/\$desc/g, '');
        // 		//.replace(/\$desc/g, this.options.layers[i].desc);
        // }
        // content+= '</ul>';
        // sidebarContainer.innerHTML = content;
        map.addControl(this._rightSidebar);
	    $(document).on('click', '.leaflet-sidebar .borrar', function(ev) {
	    	ev.preventDefault();
	    	var layerId = $(this).parent().parent().attr('data-id');
	    	this_ptr.removeLayer(layerId);
	    	if (typeof(this_ptr.options.onRemoveLayer) == "function") {
	    		this_ptr.options.onRemoveLayer(layerId);
	    	}
	    });
	    $(document).on('click', '.leaflet-sidebar .info', function(ev) {
	    	ev.preventDefault();
	        if (ev.stopPropagation) {
	            ev.stopPropagation();
	        } else {
	            ev.cancelBubble = true;
	        }            	    	
	    	var layerId = $(this).parent().parent().attr('data-id');
	    	$(this).toggleClass('on');
	    	if (typeof(this_ptr.options.onLayerInfoChange) == "function") {
	    		this_ptr.options.onLayerInfoChange(layerId, $(this).hasClass('on'));
	    	}
	    });
	    $(document).on('click', '.leaflet-sidebar .sld', function(ev) {
	    	ev.preventDefault();
	        if (ev.stopPropagation) {
	            ev.stopPropagation();
	        } else {
	            ev.cancelBubble = true;
	        }            	    	
	    	var layerId = $(this).parent().parent().attr('data-id');
	    	if (!$(this).hasClass('on')) {
	    		$('.leaflet-sidebar .layersconfig-item[data-id='+layerId+'] .sld').removeClass('on');
		    	$(this).toggleClass('on');
		    	if (typeof(this_ptr.options.onStyleChange) == "function") {
		    		this_ptr.options.onStyleChange(layerId, $(this).attr('data-id'), true);
		    	}
		    }
	    });
	    $(document).on('click', '.leaflet-sidebar .band', function(ev) {
	    	ev.preventDefault();
	        if (ev.stopPropagation) {
	            ev.stopPropagation();
	        } else {
	            ev.cancelBubble = true;
	        }            	    	
	    	var layerId = $(this).parent().parent().attr('data-id');
	    	if (!$(this).hasClass('on')) {
	    		$('.leaflet-sidebar .layersconfig-item[data-id='+layerId+'] .band').removeClass('on');
		    	$(this).toggleClass('on');
		    	if (typeof(this_ptr.options.onBandChange) == "function") {
		    		this_ptr.options.onBandChange(layerId, $(this).attr('data-id'), true);
		    	}
		    } else {
		    	$(this).removeClass('on');
		    	if (typeof(this_ptr.options.onBandChange) == "function") {
		    		this_ptr.options.onBandChange(layerId, $(this).attr('data-id'), false);
		    	}
			}
	    });
	    $(document).on('click', '.leaflet-sidebar .layersconfig-item', function(ev) {
			ev.preventDefault();
	        if (ev.stopPropagation) {
	            ev.stopPropagation();
	        } else {
	            ev.cancelBubble = true;
			}            	    	
		});
        this.update();
	
	    // $(".dropdown-toggle").dropdown();
	    // $('.layersconfig-list').sortable();

		return container;
	},

	addLayer: function(id, nombre, sldId, tooltip, layerType, bandId) {
		this.options.layers[id] = { 
			nombre: nombre,
			sldId: sldId,
			bandId: bandId,
			tooltip: tooltip,
			layerType: layerType
		};
		this.update();
		// this.loadSlds(id);
	},

	removeLayer: function(id) {
		try {
			delete this.options.layers[id];
		} catch(e) {
			console.log(e);
		}
		this.update();
	},

	loadSlds: function(layerId) {
		var self = this;
		if (layerId) {
			if (!self.slds[layerId]) {
				$.ajax({
		            url: '/layers/symbology/'+layerId+'/',
		            dataType: 'json',
		            data: {},
		            success: function(data) {
		                if (self.options.layers[layerId]) {
		                	self.slds[layerId] = data;
		                	self.updateSlds(layerId, data);
		                }
		            },
		            timeout: 10000,
		            error: function(e) { 
		            	console.log('Se produjo un error al intentar cargar los archivos sld de la capa:', layerId);
		            }
				});
			} else {
				self.updateSlds(layerId, self.slds[layerId]);
			}
		} else {
			$.each(self.options.layers, function(k, v) {
				self.loadSlds(k);
			});
		}
	},

	loadBands: function(layerId) {
		var self = this;
		if (layerId) {
			if (!self.bands[layerId] || !self.bands[layerId].loading) {
				self.bands[layerId] = { loading: true };
				$.ajax({
		            url: '/layers/bands/'+layerId+'/',
		            dataType: 'json',
		            data: {},
		            success: function(data) {
		                if (self.options.layers[layerId]) {
		                	self.bands[layerId] = data;
		                	self.updateBands(layerId, data);
		                }
		            },
		            timeout: 10000,
		            error: function(e) { 
		            	console.log('Se produjo un error al intentar cargar los archivos sld de la capa:', layerId);
		            }
				});
			} else {
				self.updateBands(layerId, self.bands[layerId]);
			}
		} else {
			$.each(self.options.layers, function(k, v) {
				if (v.layerType === 'RASTER')
					self.loadBands(k);
			});
		}
	},

	updateSlds: function(layerId, slds) {
		$('.layersconfig-item[data-id='+layerId+'] .dropdown-menu .disabled').remove();
		$('.layersconfig-item[data-id='+layerId+'] .dropdown-menu .sld').parent().remove();
		var template = '<li title="$sld_desc" data-toggle="tooltip" data-placement="top"><a tabindex="-1" href="#" class="sld" data-id="$id" style="min-height: 64px"><img src="$sld_thumb" width=60 height=60 class="pull-left"> <span class="pull-right glyphicon glyphicon-ok"></span></a></li>'
		for(var i=slds.length-1;i>=0;i--) {
			$('.layersconfig-item[data-id='+layerId+'] .dropdown-menu').prepend(
				template.replace(/\$id/g, slds[i].id).replace(/\$sld_thumb/g, slds[i].url).replace(/\$sld_desc/g, slds[i].descripcion)
			);
			if (this.options.layers[layerId].sldId==slds[i].id || (this.options.layers[layerId].sldId==0 && slds[i].default)) {
				$('.layersconfig-item[data-id='+layerId+'] .dropdown-menu .sld[data-id='+slds[i].id+']').toggleClass('on');
			}
		}
		$(function () {
		  $('[data-toggle="tooltip"]').tooltip()
		})		
	},

	updateBands: function(layerId, bands) {
		// console.log('update bands', layerId, this.options.layers[layerId], bands);
		var bandTemplate = '<li title="$band_desc" data-toggle="band"><a tabindex="-1" href="#" class="band" data-id="$id"><span class="nombre-banda">$titulo</span><span class="pull-right glyphicon glyphicon-ok"></span></a></li>';
		var bandsContent = '<li class="divider"></li><h6 class="dropdown-header">Bandas</h6>';
		for (var i=0, l=bands.length; i<l;i++) {
			if (this.options.layers[layerId].bandId == bands[i].id_mapa) {
				bandsContent += bandTemplate.replace(/\$id/g, bands[i].id_mapa).replace(/\$band_desc/g, bands[i].titulo).replace(/\$titulo/g, bands[i].titulo).replace(/class="band"/g, 'class="band on"')
			} else {
				bandsContent += bandTemplate.replace(/\$id/g, bands[i].id_mapa).replace(/\$band_desc/g, bands[i].titulo).replace(/\$titulo/g, bands[i].titulo)
			}

		}
		$('.layersconfig-item[data-id='+layerId+'] .dropdown-menu .tooltip-toggle').after(bandsContent);
	},

	update: function() {
        var content = '<h1>Capas</h1><ul class="layersconfig-list">',
        	template = $('#'+this.options.itemsTemplate).html(),
			self = this;
		// console.log(this.options.layers);
		if (Object.keys(this.options.layers).length > 0) {
	        $.each(this.options.layers, function(k, v) {        	
	        	content+=template.replace(/\$id/g, k)
	        		.replace(/\$nombre/g, v.nombre)
	        		.replace(/\$desc/g, '')
	        		.replace(/\$tooltip/g, v.tooltip?'on':'');
			});
			/*
			                  <li class="divider"></li>
                  <h6 class="dropdown-header">Bandas</h6>
                  <li><a tabindex="-1" href="#" class="info $tooltip" title="Temperatura">Temperatura <span class="glyphicon glyphicon-ok"></span></a></li>
			*/
	    } else {
	    	content+='<li><p>No hay capas agregadas.</p></li>';
	    }
        content+= '</ul>';
        /*
        for (var i=0,l=this.options.layers.length;i<l;i++) {
        	content+=template.replace(/\$id/g, self.options.layers[i].id)
        		.replace(/\$nombre/g, self.options.layers[i].nombre)
        		.replace(/\$desc/g, '');
        		//.replace(/\$desc/g, this.options.layers[i].desc);
        }
        */
        this.sidebarContainer.innerHTML = content;
	
	    $(".dropdown-toggle").dropdown();
	    var sortable = $('.layersconfig-list').sortable({
	    	onUpdate: self.options.onReorderLayers,
	    	filter: '.dropdown-toggle'
	    });
	    self.loadSlds();
	    self.loadBands();
	},

	isActive: function() {
		return L.DomUtil.hasClass(this._button, 'active');
	},

	_eliminar: function(ev) {
		console.log(ev);
	},

	_onClose: function () {
		L.DomUtil.removeClass(this._button, 'active');
	},

	_onClick: function (e) {
		if (L.DomUtil.hasClass(this._button, 'active')) {
			L.DomUtil.removeClass(this._button, 'active')
		} else {
			L.DomUtil.addClass(this._button, 'active');
		}
		this._rightSidebar.toggle();
	},

	_createButton: function (html, title, className, container, fn, context) {
		var link = L.DomUtil.create('a', className, container);
		link.innerHTML = html;
		link.href = '#';
		link.title = title;

		var stop = L.DomEvent.stopPropagation;

		L.DomEvent
		    .on(link, 'click', stop)
		    .on(link, 'mousedown', stop)
		    .on(link, 'dblclick', stop)
		    .on(link, 'click', L.DomEvent.preventDefault)
		    .on(link, 'click', fn, context)
		    .on(link, 'click', this._refocusOnMap, context);

		return link;
	}
});


L.control.layersConfig = function (options) {
	return new L.Control.LayersConfig(options);
};