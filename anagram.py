
from flask import Flask, render_template, request
from flask import current_app, g
from flask.cli import with_appcontext
import click
from wtforms import Form, StringField, TextAreaField, validators
from collections import Counter
import configparser
import re
import sqlite3
import numpy as np

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('anagram_conf.ini')
DATABASE = config['DEFAULT']['db']

print("DATABASE: ", DATABASE)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def check_anagram(form, field):
    """ Checks wether a and b are anagrams. """
    # Convert input to lowercase
    a = field.data.lower()
    b = form.string_1.data.lower()
    # strip non-word characters
    pattern = re.compile('[\W]+')
    a = pattern.sub('', a)
    b = pattern.sub('', b)
    res = (Counter(a) == Counter (b))
    
    form.is_anagram.data = res
    app.logger.info("is anagram: ", res)
    return res


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_words(sorted_word):
    if sorted_word:
        res = query_db('SELECT word FROM words WHERE sorted = ?', [sorted_word])
        return res    
    return ["No matches"]

def get_composed_anagrams(search):
    comp_ana = {}
    print("Composed Anagrams: ", search)
    l = int((len(search) / 2) + 1) # more then half the length of the search input
    res = query_db('SELECT word FROM words WHERE length = ?', [l])

    for r in res:
        a = np.array(sorted(r['word']))
        b = np.array(sorted(search))
        insect = np.intersect1d(a,b)
        if Counter(insect) == Counter(r['word']):
            print("Matches: ", r['word'])
            diff = list((Counter(search) - Counter(insect)).elements())
            if diff and len(diff) == (len(search)-len(insect)): # Appenzeller - Panzer
                next = ''.join(sorted(diff))
                print("Next: ", next)
                res2 = get_words(next)
                for r2 in res2:
                    print("Ahoi:", r2['word'])
                    if r['word'] in comp_ana and r2['word'] is not None:
                        print("Adding ", r2['word'], " to ", comp_ana[r['word']])
                        comp_ana[r['word']].append(str(r2['word']))
                        print("OK? ", comp_ana[r['word']])
                    elif r2['word'] is not None:
                        comp_ana[r['word']] = [r2['word']]
                        print("Created: ", r['word'], comp_ana[r['word']])
                    else:
                        pass
                    
                    print("comp_ana: ", comp_ana)
    return comp_ana

def get_anagrams(form, field):
    # Find and show anagrams
    search = ''.join(sorted(form.anaget.data))
    print("Search: ", search)
    res = query_db('select * from words where sorted = ?', [search])
    print("Res: ", res)
    text = []
    for r in res:
        text.append(r['word'])
    form.anagrams = text
    comps = get_composed_anagrams(search)
    form.comp_anagrams = comps
    return


class AnagramForm(Form):
    string_1 = StringField("String 1")
    string_2 = StringField("String 2", validators=[check_anagram])
    is_anagram = StringField("Result")
    anaget = StringField("Input", validators=[get_anagrams])
    anagrams = TextAreaField("Anagrams")
    comp_anagrams = TextAreaField("Composed Anagrams")


@app.route('/', methods=['GET','POST'])
def start():
    form = AnagramForm(request.form)
    form.validate()
    return render_template('start.html', form=form)

        
# https://wtforms.readthedocs.io/en/stable/
# https://flask.palletsprojects.com/en/1.1.x/patterns/wtforms/
