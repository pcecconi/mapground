from django.conf import settings 

def front_end_settings(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'VISOR': settings.VISOR}