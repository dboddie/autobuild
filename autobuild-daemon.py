#!/usr/bin/env python

import cgi, commands, os, subprocess, sys
import daemon
import web

from autobuild import builder, config

urls = ("/update", "Update",
        "/repos", "Repos",
        "/chroots", "Chroots",
        "/build", "Build")

class Update:

    done_template = ("$def with (name)\n"
                     "Updated $name.")
    
    def GET(self):
    
        if web.ctx.query.startswith("?"):
            q = cgi.parse_qs(web.ctx.query[1:])
        else:
            q = {}

        name = q.get("name")
        if not name:
            raise web.notfound()
        else:
            name = name[0]
        
        return self.update(name)

    def update(self, name):

        s = subprocess.Popen(["autobuild-repo.py", "update", name])
        if s.wait() == 0:
            t = web.template.Template(self.done_template)
            return t(name)
        else:
            raise web.notfound()

class Repos:

    title = "Repositories"
    config = "autobuild-repo"
    done_template = ("$def with (title, repos)\n"
                     "<html>\n<head><title>$title</title></head>\n"
                     "<body>\n"
                     "<h1>$title</h1>\n"
                     "<ul>\n"
                     "$for name in repos:\n"
                     "    <li>$name</li>\n"
                     "</ul>\n"
                     "</body>\n</html>\n")
    
    def GET(self):

        return self.list()

    def list(self):
    
        c = config.Config(self.config)
        labels = c.lines.keys()
        labels.sort()

        t = web.template.Template(self.done_template)
        t.content_type = "text/html"
        return t(self.title, labels)

class Chroots(Repos):

    title = "Build Environments"
    config = "autobuild-builder"

class Build:

    done_template = ("$def with (chroot, repo)\n"
                     "Started build of $repo for $chroot.")
    
    def GET(self):
    
        if web.ctx.query.startswith("?"):
            q = cgi.parse_qs(web.ctx.query[1:])
        else:
            q = {}

        chroot = q.get("chroot")
        repo = q.get("repo")
        if not chroot or not repo:
            raise web.notfound()
        
        return self.build(chroot[0], repo[0])

    def build(self, chroot, repo):
    
        current_dir = os.path.abspath(os.curdir)

        try:
            repo_conf = config.Config("autobuild-repo")
            repo_path = repo_conf.lines[repo][0]
            
            build_conf = config.Config("autobuild-builder")
            b = builder.Builder(build_conf)
            
            os.chdir(repo_path)
            b.debuild(chroot)
            os.chdir(current_dir)

        except (KeyError, builder.AutobuildError):
            os.chdir(current_dir)
            raise web.notfound()
        
        current_dir = os.path.abspath(os.curdir)
        os.chdir(repo_path)

        os.system("sudo autobuild-builder.py debuild " + commands.mkarg(chroot) + " &")
        os.chdir(current_dir)

        t = web.template.Template(self.done_template)
        return t(chroot, repo)


if __name__ == "__main__":

    if True: # with daemon.DaemonContext():
    
        app = web.application(urls, globals())
        app.run()
