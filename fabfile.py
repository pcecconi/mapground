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
	# _install_local_base_packages()
	dbname = 'mapground_dev'
	dbpass = prompt('Ingrese el password para asignar al usuario de la base de datos:')
	# _setup_local_db(dbname, dbname, dbpass)
	local("sudo ./setup_db.sh -d=%s -u=%s -p=%s"%(dbname,dbname,dbpass))
	secret_key = _get_secret_key()
	dir = os.getcwd()
	local("sed -e 's/mapground-db/%s/g' MapGround/settings_db.py.template | sed -e 's/mapground-user/%s/g' - | sed -e 's/mapground-password/%s/g' - | sed -e 's/secret-key/%s/g' > MapGround/settings_dev_db.py" % (dbname, dbname, dbpass, secret_key))
	local("cp MapGround/settings_local.py.template MapGround/settings_local.py")
	# local('mkdir MapGround/media; mkdir mapcache/cache; touch mapfiles/map-error.log; sudo chmod 666 mapfiles/map-error.log')
	try:
		local('sudo rm -rf /var/cache/mapground_dev')
		local('sudo rm -rf /var/local/mapground_dev')
	except:
		pass
	local('sudo mkdir /var/cache/mapground_dev; sudo mkdir /var/local/mapground_dev; sudo mkdir /var/local/mapground_dev/media')
	local('sudo cp -r mapfiles /var/local/mapground_dev; sudo cp -r data /var/local/mapground_dev; sudo chown -R ${USER:=$(/usr/bin/id -run)}:$USER /var/local/mapground_dev; touch /var/local/mapground_dev/mapfiles/map-error.log; sudo chmod 666 /var/local/mapground_dev/mapfiles/map-error.log')
	local("sed -e 's/\DEBUG = False$/DEBUG = True/' mapcache/settings.py.template > mapcache/settings.py")
	local('cp mapcache/mapcache.xml.template /var/local/mapground_dev/mapcache.xml')
	# local('cp mapcache/settings.py.template mapcache/settings.py')
	# local('sudo chown -R www-data:www-data mapcache/cache')
	local("sed -e 's/\/mapground\//\/mapground_dev\//g' mapground_apache.conf.template > mapground_dev_apache.conf")
	local("sudo sed -i 's/^<VirtualHost \*:8080>$/<VirtualHost *:7654>/' mapground_dev_apache.conf")
	try:
		local('sudo rm /etc/apache2/sites-enabled/mapground_dev.conf')
	except:
		pass
	local("sudo cp mapground_dev_apache.conf /etc/apache2/sites-available/mapground_dev.conf")
	local("sudo ln -s /etc/apache2/sites-available/mapground_dev.conf /etc/apache2/sites-enabled/mapground_dev.conf")
 	local("deactivate; virtualenv --system-site-packages venv; source venv/bin/activate; pip install -r requirements.txt", shell='/bin/bash')
 	# local("cp venv_path_extensions.pth venv/lib/python2.7/site-packages/")
	# local("source venv/bin/activate; python manage.py syncdb --noinput", shell='/bin/bash')
	local("source venv/bin/activate; python manage.py makemigrations", shell='/bin/bash')
	local("source venv/bin/activate; python manage.py migrate", shell='/bin/bash')
	local("source venv/bin/activate; python manage.py loaddata layers/fixtures/initial_data.json", shell='/bin/bash')
	local("source venv/bin/activate; python manage.py loaddata MapGround/fixtures/user.json", shell='/bin/bash')
	local('source venv/bin/activate; mapcache/manage.py add world_borders', shell='/bin/bash')
	local('sudo chown -R www-data:www-data /var/cache/mapground_dev; sudo chmod g+rwxs /var/cache/mapground_dev')
	local('sudo chmod 666 /var/local/mapground_dev/mapcache.xml;')
	local('sudo service apache2 restart')
	# local('sudo -u postgres psql -c "alter role %s createdb; alter role %s superuser;"' % (dbname, dbname))
	# local("source venv/bin/activate; python manage.py test", shell='/bin/bash')

def setup_prod():
	local("sudo ./setup.sh -h=localhost")

def update(dir=''):
	local('git pull')
 	local("deactivate; source venv/bin/activate; pip install -r requirements.txt", shell='/bin/bash')
	local("deactivate; source venv/bin/activate; python manage.py migrate; python manage.py collectstatic", shell='/bin/bash')
	local('sudo service uwsgi restart')

def dev():
	local("sed -i 's/DEBUG = False$/DEBUG = True/' MapGround/settings_local.py")
	local("sed -i 's/DEBUG = False$/DEBUG = True/' mapcache/settings.py")

def prod():
	local("sed -i 's/DEBUG = True$/DEBUG = False/' MapGround/settings_local.py")
	local("sed -i 's/DEBUG = True$/DEBUG = False/' mapcache/settings.py")

def runserver():
	local("source venv/bin/activate; python manage.py runserver [::]:8000", shell='/bin/bash')
