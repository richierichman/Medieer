#!/usr/bin/env python
import json
import sys
import re

from urllib2 import urlopen, HTTPError
from urllib import quote_plus
from datetime import datetime

import data
from sqlobject import SQLObjectNotFound

class APIMedia():
    title = ''
    genres = []
    actors = []
    description = ''
    year = ''
    runtime = ''
    director = ''
    ids = []
    rating = ''
    poster_url = ''
    
class APIGenre():
    name = ''
    ids = []

class APIPerson():
    name = ''
    ids = []
    job = ''

class APIBase():
    lang = 'en'
    
    def __init__(self):
        pass
    
    def _hasLeadingSlash(self, term):
        if len(term) > 0:
            try:
                term.index('/')
            except ValueError:
                return False
            else:
                return True
        else:
            return True
        
    def makeURL(self, path, term=''):
        if not self._hasLeadingSlash(term):
            term = '/%s' % term
        
        self.url = "%(proto)s://%(host)s%(path)s%(term)s" % \
                    {'proto': self.protocol,
                     'host': self.host,
                     'path': path,
                     'term': term}
            
    def getResponse(self):
        if not self.url:
            raise APIError('No defined URL to access')
        
        try:
            self.server_response = urlopen(self.url)
        except HTTPError:
            raise APIError("Couldn't open %s for reading" % self.url)

        self._server_msg = self._server_response.msg
        
        if "OK" not in self._server_msg:
            raise APIError("Server responded with something I can't handle.")
        else:
            self._response_data = self._server_response.read()

class TMDB(APIBase):
    self.output = output
    self.path_format = '/%(version)s/%(api)s/%(lang)s/%(output)s/%(apikey)s'
    self.apikey = '32143db63692aa6a5cb01336cc06211b'
    self.protocol = 'http'
    self.host = 'api.themoviedb.org'
    self.version = '2.1'
    self.output = 'json'
    self.api = 'tmdb'
    
    def getAPIMethod(self, domain, method):
        calledAPI = "%s.%s" % (domain.capitalize(), method)
        return calledAPI
    
    def pathParams(self):
        return {'version': self.version, 
                'api': self.api_method,
                'lang': self.lang,
                'output': self.output,
                'apikey': self.apikey,}

    def lookup(self, search_term, domain = 'movie'):
        self.domain = domain        
        self.search_term = search_term
        if isinstance(self.search_term , str):
            if re.search(self.imdb_id_pattern, self.search_term):
                self.method = 'imdbLookup'
            else:
                self.method = 'search'
        else:
            self.method = 'getInfo'
            
        self.api_method = self.getAPIMethod(self.domain, self.method)
        path = self.path_format % self.pathParams()
        self.makeURL(path, self.search_term)
        self.getResponse()
        
        movies = self.parseResponse(method)

        if method == 'search' and domain == 'movie':
            for movie in movies:
                self.lookup(movie.tmdb_id)
        
        return movies
        
    def parseResponse(self, method):
        json_data = json.loads(self._response_data)
        if "Nothing found" in json_data:
            raise APIError("No information found for ")
        api_data = eval('self.%sParser' % method)(json_data)
        return api_data
    
    def getInfoParser(self, api_data):
        d = api_data[0]
        movie = APIMovie()
        movie.title = d.get('name', '')
        movie.description = d.get('overview', '')
        movie.year = d.get('released', '')
        movie.runtime = d.get('runtime', '')
        movie.rating = d.get('certification', 'NR')
        movie.genres = self.getGenres(d.get('genres',[]))
        movie.actors = self.getPerson(d.get('cast', []), 'actor')
        movie.director = self.getPerson(d.get('cast', []), 'director')
        movie.ids = [['tmdb', d.get('id', 0)], ['imdb', d.get('imdb_id', 'tt0000000')]]
        movie.poster_url = self.getPoster(d.get('posters'), [])
        
        return movie
        
    def searchParser(self):
        pass
    
    def getListParser(self):
        pass
        
    def getGenres(self, genre_list):
        genres = []
        for genre in genre_list:
            g = APIGenre()
            g.name = genre.get('name', '')
            g.ids = [['tmdb', genre.get('id', 0)]]
            genres.append(g)
            
        return genres
        
    def getPerson(self, cast_list, search_job):
        people = []
        for cast in cast_list:
            job = cast.get('job', '')
            if job.lower() == search_job:
                person = APIPerson()
                person.name = cast.get('name', '')
                person.role = job
                person.id = [['tmdb', cast.get('id', 0)],]
                people.append(person)
            
        return people
        
    def getPoster(self, poster_list):
        poster_url = ''
        for image in poster_list:
            poster = image.get('image', {})
            if poster.get('size', '') == 'cover' and poster.get('url', False):
                poster_url = poster.get('url')
            
            if not poster_url and poster.get('size', None) == 'mid' and poster.get('url', False):
                poster_url = poster.get('url')
        
        return poster_url

class APIError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)    

        
if __name__ == '__main__':
    connect()
    t = TMDB()
    this_id = t.getMovieIDByName('Aliens')
    print "ID: ", this_id
    this_movie = t.getMovieInfoByTMDB_ID(this_id)
    print this_movie.toxml()
    
    