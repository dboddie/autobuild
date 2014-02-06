#!/usr/bin/env python

import cgi, os

def success():

    print "Content-type: text/plain"
    print "Status-code: 200"
    print
    print "OK"

def failure(name):

    name = cgi.escape(name)
    print "Content-type: text/html"
    print "Status-code: 404"
    print
    print "<html>"
    print "<head><title>Not Found</title></head>"
    print "<body><h1>Not Found</h1>"
    print 'The requested resource "%s" was not found.' % name
    print "</body></html>"


class Handler:

    def __init__(self):
    
        pass
    
    def handle(self, query):
    
        action = query.get("action")
        method = self.actions.get(action)
        
        if method:
            method(self, query)
    
    def update(self):
    
        name = query.get("name"):
        if not name:
            failure(name)
        
        
    
    def list(self):
    
        
    
    actions = {"update": update,
               "list": list}

handler = Handler()
query = cgi.parse(os.getenv("QUERY_STRING"))
handler.handle(query)
