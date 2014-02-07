#!/usr/bin/env python

import cgi, commands, os, subprocess

def success(value = "OK"):

    print "Content-type: text/plain"
    print "Status-code: 200"
    print
    print cgi.escape(value)

def failure(message = ""):

    print "Content-type: text/html"
    print "Status-code: 404"
    print
    print "<html>"
    print "<head><title>Not Found</title></head>"
    print "<body><h1>Not Found</h1>"
    print cgi.escape(message)
    print "</body></html>"


class Handler:

    def __init__(self):
    
        pass
    
    def handle(self, query):
    
        # Get the action parameter - this will be a list of string containing
        # ideally only one item.
        action = query.get("action")
        if not action:
            failure()
        
        method = self.actions.get(action[0])
        
        if method:
            method(self, query)
        else:
            failure()
    
    def update_repo(self, query):
    
        name = query.get("name")
        if not name:
            failure("update-repo")
            return
        
        name = name[0]
        
        s = subprocess.Popen(["autobuild-repo.py", "update", commands.mkarg(name)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if s.wait() == 0:
            success(s.stdout.read())
        else:
            failure(s.stderr.read())
    
    def list_repo(self, query):
    
        s = subprocess.Popen(["autobuild-repo.py", "list"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if s.wait() == 0:
            success(s.stdout.read())
        else:
            failure(s.stderr.read())
    
    def list_distros(self, query):
    
        s = subprocess.Popen(["autobuild-builder.py", "list"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if s.wait() == 0:
            success(s.stdout.read())
        else:
            failure(s.stderr.read())
    
    # update-repo <repo>
    # list-repo
    # list-packages <distribution>
    actions = {"update-repo": update_repo,
               "list-repo": list_repo,
               "list-distros": list_distros}

handler = Handler()
query = cgi.parse(os.getenv("QUERY_STRING"))
handler.handle(query)
