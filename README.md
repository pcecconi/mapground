# Instalación en Ubuntu 18.04
## Paquetes requeridos
Los paquetes requeridos se instalan al ejecutar el script provision.sh (automáticamente si se usa Vagrant, al ejecutar el primer vagrant up)

## Entorno de desarrollo
La inicialización del entorno de desarrollo solo es necesario ejecutarla 1 vez y consiste en lo siguiente:
```
#!bash

$ cd /path/to/your/mapground
$ fab setup_dev
$ fab runserver
```
## Deploy
El deploy en producción, una vez corrido el provision.sh, consiste en lo siguiente:
```
#!bash

$ cd /path/to/your/mapground
$ fab setup_prod
```
Para alternar entre ambos entornos se usan los comandos:
```
#!bash

$ cd /path/to/your/mapground
$ fab dev # para pasar a dev
$ fab prod # para pasar a prod
```
