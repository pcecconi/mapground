# encoding: utf-8
from fabric.api import lcd, local, sudo, prompt, prefix, env, run, cd
import random; import string;
import logging, os
logging.basicConfig()

def _get_secret_key():
	return "".join([random.SystemRandom().choice(string.digits + string.letters) for i in range(100)])

def _install_local_base_packages():
	try:
		local("sudo apt-get install uwsgi apache2 postgresql-9.3-postgis-2.1 python-psycopg2 python-gdal nginx python-virtualenv fabric uwsgi uwsgi-plugin-python python-mapscript cgi-mapserver mapserver-bin mapcache-cgi mapcache-tools imagemagick python-lxml")
		local("sudo a2enmod cgid")
		local("sudo pip install simpleflock")
	except:
		pass

def _setup_local_db(dbname, dbuser, dbpass):
	try:
		local("sudo -u postgres bash -c 'dropdb %s; dropuser %s'"%(dbname, dbuser))
	except:
		pass
	try:
		local("sudo -u postgres bash -c 'createuser -s %s'" % (dbuser))
	except:
		pass
	local('sudo locale-gen es_AR.utf8')
	local('sudo service postgresql restart')
	local("sudo -u postgres bash -c 'createdb -l es_AR.utf8 -O %s -T template0 %s'" % (dbuser, dbname))
	local("sudo -u postgres psql -d %s < setup.sql" % dbname)
	sql = '"alter user %s with password \'%s\'; create schema data; alter schema data owner to %s; alter schema utils OWNER TO %s;ALTER FUNCTION utils.campos_de_tabla(character varying, character varying) OWNER TO %s;"' % (dbuser, dbpass, dbuser, dbuser, dbuser)
	local('sudo -u postgres psql -d %s -c %s' % (dbname, sql))

def init_dev():
	_install_local_base_packages()
	dbname = 'mapground_dev'
	dbpass = prompt('Ingrese el password para asignar al usuario de la base de datos:')
	_setup_local_db(dbname, dbname, dbpass)
	secret_key = _get_secret_key()
	local("sed -e 's/mapground-db/%s/g' MapGround/settings_local.py.template | sed -e 's/mapground-user/%s/g' - | sed -e 's/mapground-password/%s/g' - | sed -e 's/secret-key/%s/g' > MapGround/settings_local.py" % (dbname, dbname, dbpass, secret_key))
	local('mkdir MapGround/media; mkdir mapcache/cache; touch mapfiles/map-error.log; sudo chmod 666 mapfiles/map-error.log')
	local('cp mapcache/mapcache.xml.template mapcache/mapcache.xml')
	local('cp mapcache/settings.py.template mapcache/settings.py')
	local('sudo chown -R www-data:www-data mapcache/cache')
 	local("deactivate; virtualenv --system-site-packages venv; source venv/bin/activate; pip install -r requirements.txt", shell='/bin/bash')
 	# local("cp venv_path_extensions.pth venv/lib/python2.7/site-packages/")
	local("source venv/bin/activate; python manage.py syncdb", shell='/bin/bash')
	local("source venv/bin/activate; python manage.py loaddata layers/fixtures/initial_data.json", shell='/bin/bash')
	local("source venv/bin/activate; python manage.py loaddata MapGround/fixtures/user.json", shell='/bin/bash')
	local('source venv/bin/activate; mapcache/manage.py add world_borders', shell='/bin/bash')
	# local('sudo -u postgres psql -c "alter role %s createdb; alter role %s superuser;"' % (dbname, dbname))
	# local("source venv/bin/activate; python manage.py test", shell='/bin/bash')

def setup():
	_install_local_base_packages()
	dbpass = prompt('Ingrese el password para asignar al usuario de la base de datos:')
	dbname = 'mapground'
	_setup_local_db(dbname, dbname, dbpass)
	dir = os.getcwd()
	with lcd(dir):
		secret_key = _get_secret_key()
		local("sed -e 's/mapground-db/%s/g' MapGround/settings_local.py.template | sed -e 's/mapground-user/%s/g' - | sed -e 's/mapground-password/%s/g' - | sed -e 's/secret-key/%s/g' > MapGround/settings_local.py" % (dbname, dbname, dbpass, secret_key))
		local("sed -e 's/\/path\/to\/your\/mapground/%s/g' mapground_uwsgi.ini.template > mapground_uwsgi.ini" % dir.replace('/', '\/'))
		local('mkdir MapGround/media; mkdir mapcache/cache; touch mapfiles/map-error.log; sudo chmod 666 mapfiles/map-error.log')
		local('cp mapcache/mapcache.xml.template mapcache/mapcache.xml')
		local('cp mapcache/settings.py.template mapcache/settings.py')
		# local('sudo chmod o+w mapfiles')
		local('sudo cp mapground_uwsgi.ini /etc/uwsgi/apps-available/mapground.ini')
		try:
			local('sudo rm /etc/uwsgi/apps-enabled/mapground.ini')
		except:
			pass
		local("sudo ln -s /etc/uwsgi/apps-available/mapground.ini /etc/uwsgi/apps-enabled/mapground.ini")
	 	local("sed -e 's/\/path\/to\/your\/mapground/%s/g' mapground_nginx+apache.conf.template > mapground_nginx.conf" % dir.replace('/', '\/'))
		local('sudo cp mapground_nginx.conf /etc/nginx/sites-available/mapground')
		try:
			local('sudo rm /etc/nginx/sites-enabled/mapground')
		except:
			pass
		local("sudo ln -s /etc/nginx/sites-available/mapground /etc/nginx/sites-enabled/mapground")
	 	local("sed -e 's/\/path\/to\/your\/mapground/%s/g' mapground_apache.conf.template > mapground_apache.conf" % dir.replace('/', '\/'))
		local('sudo cp mapground_apache.conf /etc/apache2/sites-available/mapground.conf')
		try:
			local('sudo rm /etc/apache2/sites-enabled/mapground.conf')
		except:
			pass
		local("sudo ln -s /etc/apache2/sites-available/mapground.conf /etc/apache2/sites-enabled/mapground.conf")
	 	local("deactivate; virtualenv --system-site-packages venv; source venv/bin/activate; pip install -r requirements.txt", shell='/bin/bash')
		local('source venv/bin/activate; sudo mapcache/manage.py add world_borders')
		local("source venv/bin/activate; python manage.py syncdb; python manage.py collectstatic", shell='/bin/bash')
		local("source venv/bin/activate; python manage.py loaddata MapGround/fixtures/user.json", shell='/bin/bash')
		local("source venv/bin/activate; python manage.py loaddata layers/fixtures/initial_data.json", shell='/bin/bash')
		local('sudo chown -R www-data:www-data MapGround/media mapcache/cache mapfiles mapcache/mapcache.xml')
		local('sudo service uwsgi restart; sudo service nginx restart')

def update(dir=''):
	local('git pull')
 	local("deactivate; source venv/bin/activate; pip install -r requirements.txt", shell='/bin/bash')
	local("deactivate; source venv/bin/activate; python manage.py migrate; python manage.py collectstatic", shell='/bin/bash')
	local('sudo service uwsgi restart')