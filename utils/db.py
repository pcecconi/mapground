# -*- coding: utf-8 -*-
from django.db import connection

def drop_table(schema, table, cascade=False):
    query = ('SELECT DropGeometryColumn(\'%s\',\'%s\',\'geom\'); '
                'DROP TABLE "%s"."%s"') % (schema, table, schema, table)
    if cascade:
        query += ' CASCADE'
    cur = connection.cursor()
    cur.execute(query)

def setup_inheritance(schema, parent_table, child_table):
    query = ('ALTER TABLE "%s"."%s" INHERIT "%s"."%s"') % (schema, child_table, 
        schema, parent_table)
    cur = connection.cursor()
    cur.execute(query)

def add_column(schema, table, col_name, col_type, default_val=None):
    query = ('ALTER TABLE "%s"."%s" ADD COLUMN "%s" %s') % (schema, table, 
        col_name, col_type)
    if default_val != None:
        query+=" DEFAULT '%s'"%(default_val)
    cur = connection.cursor()
    cur.execute(query)
