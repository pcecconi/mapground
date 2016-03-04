# Instalación en Ubuntu 14.04
## Paquetes requeridos
Los paquetes requeridos se instalan al ejecutar los respectivos comandos init_*.

## Entorno de desarrollo
La inicialización del entorno de desarrollo solo es necesario ejecutarla 1 vez y consiste en lo siguiente:
```
#!bash

$ cd /path/to/your/mapground
$ fab init_dev
```
## Staging
El "staging" es similar a un deploy pero en un entorno local. La inicialización del entorno de staging solo debe ejecutarse la primera vez y consiste en:
```
#!bash

$ cd /path/to/your/mapground
$ fab init_stage
```
Cuando se hayan hecho cambios en el entorno de desarrollo y se quiera probarlos en un entorno de staging ya inicializado se deberán ejecutar los siguientes comandos:
```
#!bash

$ cd /path/to/your/mapground
$ fab stage
```
