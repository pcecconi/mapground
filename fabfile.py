# encoding: utf-8
from fabric.api import lcd, local, sudo, prompt, prefix, env, run, cd
from fabric.context_managers import shell_env
import random 
import string
import logging, os
logging.basicConfig()

def _get_secret_key():
	return "".join([random.SystemRandom().choice(string.digits + string.letters) for i in range(100)])

def setup_dev():
	local("sudo ./setup_dev.sh")

def setup_prod():
	local("sudo ./setup.sh -h=localhost")

def update(dir=''):
	local('git pull')
 	local("deactivate; source venv/bin/activate; pip install -r requirements.txt", shell='/bin/bash')
	local("deactivate; source venv/bin/activate; python manage.py makemigrations; python manage.py migrate; python manage.py collectstatic", shell='/bin/bash')
	local('sudo service uwsgi restart')

def dev():
	local("sed -i 's/DEBUG = False$/DEBUG = True/' MapGround/settings_local.py")
	local("sed -i 's/DEBUG = False$/DEBUG = True/' mapcache/settings.py")

def prod():
	local("sed -i 's/DEBUG = True$/DEBUG = False/' MapGround/settings_local.py")
	local("sed -i 's/DEBUG = True$/DEBUG = False/' mapcache/settings.py")

def runserver():
	local("source venv/bin/activate; python manage.py runserver [::]:8000", shell='/bin/bash')
