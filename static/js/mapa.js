// Definicion del namespace
var planif = planif || {};
planif.proj = {
	'EPSG:22172': new L.Proj.CRS.TMS('EPSG:22172',
	  '+proj=tmerc +lat_0=-90 +lon_0=-69 +k=1 +x_0=2500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
	  [-2200000, -189000, 9100000, 11111000],
	  {
		resolutions: [44140.625, 22070.3125, 11035.15625, 5517.578125, 2758.7890625, 1379.39453125, 689.697265625, 344.848632813, 172.424316406, 86.212158203, 43.106079102, 21.553039551, 10.776519775]
	  }
	),
	'EPSG:22173': new L.Proj.CRS.TMS('EPSG:22173',
	  '+proj=tmerc +lat_0=-90 +lon_0=-66 +k=1 +x_0=3500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
	  [-2200000, -189000, 9100000, 11111000],
	  {
		resolutions: [44140.625, 22070.3125, 11035.15625, 5517.578125, 2758.7890625, 1379.39453125, 689.697265625, 344.848632813, 172.424316406, 86.212158203, 43.106079102, 21.553039551, 10.776519775]
	  }
	),
	'EPSG:22176': new L.Proj.CRS.TMS('EPSG:22176',
	  '+proj=tmerc +lat_0=-90 +lon_0=-57 +k=1 +x_0=6500000 +y_0=0 +ellps=GRS80 +units=m +no_defs',
	  [-2200000, -189000, 9100000, 11111000],
	  {
		resolutions: [44140.625, 22070.3125, 11035.15625, 5517.578125, 2758.7890625, 1379.39453125, 689.697265625, 344.848632813, 172.424316406, 86.212158203, 43.106079102, 21.553039551, 10.776519775]
	  }
	)	
}

planif.Mapa = (function($) {
	var map = null, layer = null, refLayer = null;

	return {
		init: function(divId, mapConfig) {
			var wgs84 = new proj4.Proj("EPSG:4326"),
				origin = new proj4.Proj(mapConfig.srs),
				leftBottom = new proj4.Point(mapConfig.extent[0],mapConfig.extent[1]),
				rightTop = new proj4.Point(mapConfig.extent[2],mapConfig.extent[3]);
			proj4.transform(origin, wgs84, leftBottom);
			proj4.transform(origin, wgs84, rightTop);
			console.log(leftBottom, rightTop);
			console.log(L.latLngBounds(L.latLng(leftBottom.y, leftBottom.x), L.latLng(rightTop.y, rightTop.x)));
			mapa = L.map(divId, {
			  // crs: planif.proj[mapConfig.srs],
			  continuousWorld: true,
			  worldCopyJump: false
			}).fitBounds(L.latLngBounds(L.latLng(leftBottom.y, leftBottom.x), L.latLng(rightTop.y, rightTop.x))); // .setView([-46.18, -60.37], 2);
		
			var layer = L.tileLayer(mapConfig.onlineresource+'{z}/{x}/{y}.png', {
				attribution: '<b>Fuente:</b> '+mapConfig.attribution,
			    tms: true,
			    continuousWorld: true
			}).addTo(mapa);
		
			// add an OpenStreetMap tile layer to minimap

			var refLayer = L.tileLayer(mapConfig.onlineresource+'{z}/{x}/{y}.png', {
			    tms: true
			});
	/*
			var layer2 = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
				attribution: '<b>Fuente:</b> INDEC, Censo 2010</span>'

			}).addTo(map);
	*/

			/*
		    jQuery.get('http://sig.planificacion.gob.ar/cgi-bin/mapserv?callback=?', {
		      map: mapConfig.map,
		      mode: 'legend',
		      layers: 'all'
		    }, 'jsonp').done(function(data) {
				mapa.addControl(new Abstract(mapConfig, data));
		    }).fail(function(error) { console.log(error); });
			*/

			// mapa.addControl(new Abstract(mapConfig));
			// var miniMap = new L.Control.MiniMap(refLayer, { toggleDisplay: true, minimized: true }).addTo(mapa);
		}
	}
})(jQuery);
