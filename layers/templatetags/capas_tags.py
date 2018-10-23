from django import template
import re 

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

register.filter('quitar_char', quitar_char)


def replace_text(value, replacement):
    rep = replacement.split(',')
    try:
        return value.replace(rep[0], rep[1])
    except:
        return value

register.filter('replace_text', replace_text)


def truncar_string(value, max_length=0):
    if max_length == 0:
        return value
    return value[:max_length] + ('...' if len(value) > max_length else '')

register.filter('truncar_string', truncar_string)


def get_range(value):
    """
    Filter - returns a list containing range made from given value.

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
        return range(value)
    except:
        return None
register.filter('get_range', get_range)


@register.filter
def filtrar_mapas_por_tipo(value, valor):
    return value.filter(tipo_de_mapa=valor)

register.filter('filtrar_mapas_por_tipo', filtrar_mapas_por_tipo)

def match_format_string(format_str, s):
    """Match s against the given format string, return dict of matches.

    We assume all of the arguments in format string are named keyword arguments (i.e. no {} or
    {:0.2f}). We also assume that all chars are allowed in each keyword argument, so separators
    need to be present which aren't present in the keyword arguments (i.e. '{one}{two}' won't work
    reliably as a format string but '{one}-{two}' will if the hyphen isn't used in {one} or {two}).

    We raise if the format string does not match s.

    Example:
    fs = '{test}-{flight}-{go}'
    s = fs.format('first', 'second', 'third')
    match_format_string(fs, s) -> {'test': 'first', 'flight': 'second', 'go': 'third'}
    """

    # First split on any keyword arguments, note that the names of keyword arguments will be in the
    # 1st, 3rd, ... positions in this list
    tokens = re.split(r'\{(.*?)\}', format_str)
    keywords = tokens[1::2]

    # Now replace keyword arguments with named groups matching them. We also escape between keyword
    # arguments so we support meta-characters there. Re-join tokens to form our regexp pattern
    tokens[1::2] = map(u'(?P<{}>.*)'.format, keywords)
    tokens[0::2] = map(re.escape, tokens[0::2])
    pattern = ''.join(tokens)

    # Use our pattern to match the given string, raise if it doesn't match
    matches = re.match(pattern, s)
    if not matches:
        raise Exception("Format string did not match")

    # Return a dict with all of our keywords and their values
    return {x: matches.group(x) for x in keywords}

@register.filter
def get_id_banda(value):    
    parsed = match_format_string("('{var}', '{num}')", value.mapserverlayer_set.first().bandas)
    return parsed['var']

register.filter('get_id_banda_mapa', get_id_banda)
