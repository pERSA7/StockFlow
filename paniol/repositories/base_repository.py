# clase base con el metodo _get_cursor() y manejo comun de errores
import os 
import sys
import pymysql
import traceback


class BaseRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def _get_cursor(self):
        return self.db_manager._get_cursor()

    @property
    def conn(self):
        return self.db_manager.conn
        