+function ($) {
  'use strict';

  $("[name=list-style]").change(function(e) {
  	var s = $(this).parent().siblings(),
  		lc = $(this).parents(".list-container").first();
  	s.each(function(k, v) {
  		lc.removeClass(v.getElementsByTagName("input")[0].id);
  	});
  	lc.addClass($(this).attr("id"));
  });

  $(".btn.eliminar").click(function(e) {
  	e.preventDefault();
  	var next = $(e.target).attr('href'),
        msg = "¿Está seguro que desea <b>"+$(e.target).attr('title')+"</b>? Esta acción no podrá deshacerse.";
  	$('#modal-eliminar [data-action]').click(function(ev) {
  		ev.preventDefault();
  		if ($(ev.target).attr('data-action') == 'eliminar') {
  			document.location=next;
  		}
  	});
  	$('#modal-eliminar .modal-body').html(msg);
  	$('#modal-eliminar').modal('show');
  });

  $('.list-container>.thumbnail').hover(function() {
    $(this).addClass('active hovered');
  }, function() {
    $(this).removeClass('active hovered');
  });

  $('.list-container>.thumbnail').click(function() {
    if (!$(this).hasClass('hovered')) {
      $(this).toggleClass('active');
    }
  });

  $('.band-selector').change(function() {
    $('.map-frame').attr("src",  $(this).val())
    $('.full-screen-map-link').attr("href", $(this).val()+"?abstract=0&title=1")
  })

 }(jQuery);