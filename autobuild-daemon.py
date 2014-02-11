#!/usr/bin/env python

import cgi, commands, os, subprocess, sys
import daemon
import web

from autobuild import config, processes

urls = ("/", "Overview",
        "/update", "Update",
        "/repos", "Repos",
        "/chroots", "Chroots",
        "/build", "Build")

class Update:

    done_template = ("$def with (repo)\n"
                     "Updated $repo.")
    
    def POST(self):
    
        if web.ctx.query.startswith("?"):
            q = cgi.parse_qs(web.ctx.query[1:])
        else:
            q = {}

        repo = q.get("repo")
        if not repo:
            raise web.notfound()
        else:
            repo = repo[0]
        
        return self.update(repo)

    def update(self, repo):

        s = subprocess.Popen(["autobuild-repo.py", "update", repo])
        if s.wait() == 0:
            t = web.template.Template(self.done_template)
            return t(repo)
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
    
        global process_manager
        current_dir = os.path.abspath(os.curdir)

        try:
            repo_conf = config.Config("autobuild-repo")
            repo_path = repo_conf.lines[repo][0]
            
            build_conf = config.Config("autobuild-builder")
            if not build_conf.check_label(chroot):
                raise web.notfound()

        except KeyError:
            raise web.notfound()
        
        # Check for an existing process and reserve space for a new one.
        path = processes.claim_process(chroot, repo)
        if not path:
            raise web.notfound("Not starting build")
        
        current_dir = os.path.abspath(os.curdir)
        os.chdir(repo_path)
        
        pid = os.fork()
        if pid == 0:
            # Child process (pid is 0)
            stdout_path = path + ".stdout"
            stderr_path = path + ".stderr"
            result = os.system("sudo autobuild-builder.py debuild" + commands.mkarg(chroot) + \
                               " 1> " + commands.mkarg(stdout_path) + \
                               " 2> " + commands.mkarg(stderr_path))
            processes.remove_lockfile(path)
            sys.exit(result)
        else:
            # Parent process (pid is child pid)
            processes.update_process(path, pid)

        os.chdir(current_dir)

        t = web.template.Template(self.done_template)
        return t(chroot, repo)

class Overview:

    done_template = ("$def with (title, chroots, repos, building)\n"
                     "<html>\n<head><title>$title</title></head>\n"
                     "<body>\n"
                     "<h1>$title</h1>\n"
                     "<table>\n"
                     "    <tr>\n"
                     "    <th></th>\n"
                     "$for chroot in chroots:\n"
                     "    <th>$chroot</th>\n"
                     "    </tr>\n"
                     "$for repo in repos:\n"
                     "    <tr>\n"
                     "    <th>$repo</th>\n"
                     "    $for chroot in chroots:\n"
                     "        <td>$building(chroot, repo)</td>\n"
                     "    </tr>\n"
                     "</table>\n"
                     "</body>\n</html>\n")
    
    def GET(self):

        c = config.Config(Chroots.config)
        chroots = c.lines.keys()
        chroots.sort()
        c = config.Config(Repos.config)
        repos = c.lines.keys()
        repos.sort()
        
        t = web.template.Template(self.done_template)
        t.content_type = "text/html"
        return t(self.title, labels, chroots, processes.is_building)


if __name__ == "__main__":

    if True: # with daemon.DaemonContext():
    
        app = web.application(urls, globals())
        app.run()
