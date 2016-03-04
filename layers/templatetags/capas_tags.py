from django import template

register = template.Library()

def mostrar_resumen_capa(context, c, order_by):
	# print context
	to_return = {
    	'capa': c,
    	'order_by': order_by,
	}
	return to_return

@register.inclusion_tag('capas/lista_capas.html')
def mostrar_capas(lista_capas, order_by):
    to_return = {
        'lista_capas': lista_capas,
        'order_by': order_by
    }
    return to_return

register.inclusion_tag('capas/capa.html', takes_context=True)(mostrar_resumen_capa)

def quitar_char(value, arg):
    return value.replace(arg, ' ')

register.filter('quitar_char',quitar_char)

def replace_text(value, replacement):
    rep = replacement.split(',')
    try:
      return value.replace(rep[0], rep[1])
    except:
      return value

register.filter('replace_text',replace_text)

def truncar_string(value, max_length=0):
	if max_length==0:
		return value
	return value[:max_length]+('...' if len(value)>max_length else '')

register.filter('truncar_string',truncar_string)


def get_range(value):
  """
    Filter - returns a list containing range made from given value
    Usage (in template):

    <ul>{% for i in 3|get_range %}
      <li>{{ i }}. Do something</li>
    {% endfor %}</ul>

    Results with the HTML:
    <ul>
      <li>0. Do something</li>
      <li>1. Do something</li>
      <li>2. Do something</li>
    </ul>

    Instead of 3 one may use the variable set in the views
  """
  try:
  	return range( value )
  except:
  	return None
register.filter('get_range',get_range)
