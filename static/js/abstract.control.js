var mg = mg || {};

mg.Abstract = L.Control.extend({
    initialize: function (mapConfig, legend, options) {
        this.config = mapConfig;
        this.legend = legend;
        L.Util.setOptions(this, options);
    },

    options: {
        position: 'topright',
        abstract: true,
        title: true,
        minimized: false
    },

	hideText: 'Ocultar referencias',
	
	showText: 'Mostrar referencias',

    onAdd: function (map) {
    	this._container = L.DomUtil.create('div', 'leaflet-control-abstract legend');
    	var divAbstract = L.DomUtil.create('div', 'abstract', this._container)
    	if (this.options.title) {
        	divAbstract.innerHTML = '<p class="title">'+this.config.title+'</p>';
        }
        if (this.options.abstract) {
        	divAbstract.innerHTML = divAbstract.innerHTML + this.config.abstract;
        }
       	divAbstract.innerHTML = divAbstract.innerHTML + this.legend;

		this._addToggleButton();

		if (this.options.minimized) {
			this._minimize();
		}

	    return this._container;
    },

	_addToggleButton: function () {
		this._toggleDisplayButton = this._createButton(
				'', this.hideText, 'leaflet-control-abstract-toggle-display', this._container, this._toggleDisplayButtonClicked, this);
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
			.on(link, 'click', fn, context);

		return link;
	},

	_toggleDisplayButtonClicked: function () {
		this._userToggledDisplay = true;
		if (!this._minimized) {
			this._minimize();
			this._toggleDisplayButton.title = this.showText;
		}
		else {
			this._restore();
			this._toggleDisplayButton.title = this.hideText;
		}
	},

	_setDisplay: function (minimize) {
		if (minimize != this._minimized) {
			if (!this._minimized) {
				this._minimize();
			}
			else {
				this._restore();
			}
		}
	},

	_minimize: function () {
		// hide the control
		this._container.prevWidth = L.DomUtil.getStyle(this._container, 'width');
		this._container.prevHeight = L.DomUtil.getStyle(this._container, 'height');
		this._container.style.width = '19px';
		this._container.style.height = '19px';
		this._container.className += ' minimized';
		this._toggleDisplayButton.className += ' minimized';
		this._minimized = true;
	},

	_restore: function () {
		$(this._container).css('width', '');
		$(this._container).css('height', '');
		this._toggleDisplayButton.className = this._toggleDisplayButton.className
				.replace(/(?:^|\s)minimized(?!\S)/g, '');
		this._container.className = this._container.className
				.replace(/(?:^|\s)minimized(?!\S)/g, '');
		this._minimized = false;
	},    
});