+function ($) {
  'use strict';

	$('#todas').on('click', function(ev) {
		ev.preventDefault();
		$('#id_categorias input').prop('checked', true);	
	});
	
	$('#ninguna').on('click', function(ev) {
		ev.preventDefault();
		$('#id_categorias input').prop('checked', false);	
	});

}(jQuery);