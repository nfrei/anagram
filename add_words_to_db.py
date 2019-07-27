#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sqlite3
from sqlite3 import Error
import re

class MakeDB:

    config = configparser.ConfigParser()
    config.read('build_db.ini')
    db_file = config['DEFAULT']['db_file']
    wordlist = config['DEFAULT']['wordlist']

    def create_connection(self, db_file):
        """ create a database connection to a SQLite database """
        db_file = self.db_file
        try:
            connection = sqlite3.connect(db_file)
            print("Connected!", sqlite3.version)
        except Error as e:
            print(e)
        return connection

    def add_words(self):
            
        file = open(self.wordlist, 'r', encoding="iso-8859-1")
        words = file.readlines()

        pattern1 = re.compile(r'ß')
        pattern2 = re.compile(r'-')

        base = ''
        l = 0

        c = self.create_connection(self.db_file)
        print(c)

        with c:

            cursor = c.cursor()
        
            for w in words:
                w = w.rstrip().lower()
                w = re.sub(pattern1, '', w)
                w = re.sub(pattern2, '', w)
                
                l = len(w)
                base = ''.join(sorted(w))
                sql = '''
                INSERT INTO words(word, sorted, length)
                VALUES(?,?,?)
                '''
                try:
                    cursor.execute(sql, (w, base, l))
                    print("Inserted: ", w)
                except Error as e:
                    print("Error while inserting word: ", w, ". ", e)

        print(cursor.lastrowid)
        c.close()

mydb = MakeDB()
mydb.add_words()


