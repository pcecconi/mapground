# encoding: utf-8
from fabric.api import lcd, local, sudo, prompt, prefix, env, run, cd
from fabric.context_managers import shell_env
import random; import string;
import logging, os
logging.basicConfig()

def _get_secret_key():
	return "".join([random.SystemRandom().choice(string.digits + string.letters) for i in range(100)])

def _install_local_base_packages():
	try:
		local("sudo apt-get update; sudo apt-get install uwsgi apache2 postgresql-9.3-postgis-2.1 python-psycopg2 python-gdal nginx python-virtualenv fabric uwsgi uwsgi-plugin-python python-mapscript cgi-mapserver mapserver-bin mapcache-cgi mapcache-tools imagemagick python-lxml")
		local("sudo a2enmod cgid")
		local("sudo pip install simpleflock")
	except:
		pass

def _setup_local_db(dbname, dbuser, dbpass):
	with shell_env(LC_ALL='es_AR.UTF-8', LANGUAGE='es_AR.UTF-8', LANG='es_AR.UTF-8'):
		try:
			local("sudo -u postgres bash -c 'dropdb %s; dropuser %s'"%(dbname, dbuser))
		except:
			pass
		try:
			local("sudo -u postgres bash -c 'createuser -s %s'" % (dbuser))
		except:
			pass
		# local('sudo /usr/sbin/locale-gen es_AR.utf8')
		local('sudo service postgresql restart')
		local("sudo -u postgres bash -c 'createdb -l es_AR.utf8 -O %s -T template0 %s'" % (dbuser, dbname))
		local("sudo -u postgres psql -d %s < setup.sql" % dbname)
		sql = '"alter user %s with password \'%s\'; create schema data; alter schema data owner to %s; alter schema utils OWNER TO %s;ALTER FUNCTION utils.campos_de_tabla(character varying, character varying) OWNER TO %s;"' % (dbuser, dbpass, dbuser, dbuser, dbuser)
		local('sudo -u postgres psql -d %s -c %s' % (dbname, sql))

def setup_dev():
	# _install_local_base_packages()
	dbname = 'mapground_dev'
	dbpass = prompt('Ingrese el password para asignar al usuario de la base de datos:')
	_setup_local_db(dbname, dbname, dbpass)
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
	# _install_local_base_packages()
	dbpass = prompt('Ingrese el password para asignar al usuario de la base de datos:')
	dbname = 'mapground'
	_setup_local_db(dbname, dbname, dbpass)
	dir = os.getcwd()
	with lcd(dir):
		secret_key = _get_secret_key()
		local("sed -e 's/mapground-db/%s/g' MapGround/settings_db.py.template | sed -e 's/mapground-user/%s/g' - | sed -e 's/mapground-password/%s/g' - | sed -e 's/secret-key/%s/g' > MapGround/settings_local_db.py" % (dbname, dbname, dbpass, secret_key))
		local("sed -e 's/\DEBUG = True$/DEBUG = False/' MapGround/settings_local.py.template > MapGround/settings_local.py")
		try:
			local('sudo rm -rf /var/cache/mapground')
			local('sudo rm -rf /var/local/mapground')
		except:
			pass
		local("sed -e 's/\/path\/to\/your\/mapground/%s/g' mapground_uwsgi.ini.template > mapground_uwsgi.ini" % dir.replace('/', '\/'))
		local('sudo mkdir /var/cache/mapground; sudo mkdir /var/local/mapground; sudo mkdir /var/local/mapground/media; touch mapfiles/map-error.log; sudo chmod 666 mapfiles/map-error.log')
		local('sudo cp -r mapfiles /var/local/mapground; sudo cp -r data /var/local/mapground; sudo chown -R ${USER:=$(/usr/bin/id -run)}:$USER /var/local/mapground')
		local('cp mapcache/mapcache.xml.template /var/local/mapground/mapcache.xml')
		local("sed -e 's/\DEBUG = True$/DEBUG = False/' mapcache/settings.py.template > mapcache/settings.py")
		# local('cp mapcache/settings.py.template mapcache/settings.py')
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
	 	# local("sed -e 's/\/path\/to\/your\/mapground/%s/g' mapground_apache.conf.template > mapground_apache.conf" % dir.replace('/', '\/'))
		local('sudo cp mapground_apache.conf.template /etc/apache2/sites-available/mapground.conf')
		try:
			local('sudo rm /etc/apache2/sites-enabled/mapground.conf')
		except:
			pass
		local("sudo ln -s /etc/apache2/sites-available/mapground.conf /etc/apache2/sites-enabled/mapground.conf")
	 	local("deactivate; virtualenv --system-site-packages venv; source venv/bin/activate; pip install -r requirements.txt", shell='/bin/bash')
		local('source venv/bin/activate; sudo mapcache/manage.py add world_borders')
		# local("source venv/bin/activate; python manage.py syncdb --noinput; python manage.py collectstatic", shell='/bin/bash')
		local("source venv/bin/activate; python manage.py makemigrations; python manage.py migrate", shell='/bin/bash')
		local("source venv/bin/activate; python manage.py loaddata MapGround/fixtures/user.json", shell='/bin/bash')
		local("source venv/bin/activate; python manage.py loaddata layers/fixtures/initial_data.json", shell='/bin/bash')
		local('sudo chown -R www-data:www-data /var/local/mapground /var/cache/mapground;')
		local('sudo service uwsgi restart; sudo service apache2 restart; sudo service nginx restart')

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
