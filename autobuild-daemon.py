#!/usr/bin/env python

# Copyright (C) 2014 met.no
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import cgi, commands, glob, os, shutil, subprocess, sys, tempfile
from debian.changelog import Changelog
import daemon
import web

from autobuild import builder, config, keyhandler, processes

urls = ("/", "Overview",
        "/info", "Info",
        "/update", "Update",
        "/revision", "Revision",
        "/repos", "Repos",
        "/chroots", "Chroots",
        "/build", "Build",
        "/log", "Log",
        "/products", "Products",
        "/product/(.*)", "Product",
        "/publish", "Publish")

class Base:

    def get_query(self):
    
        if web.ctx.query.startswith("?"):
            q = cgi.parse_qs(web.ctx.query[1:])
        else:
            q = {}

        return q

class Update(Base):

    """Handles requests to update source repositories and chroots."""

    template = ("$def with (name)\n"
                "Updated $name.")
    
    def GET(self):

        return self.POST()

    def POST(self):
    
        q = self.get_query()

        repo = q.get("repo")
        chroot = q.get("chroot")
        if not repo and not chroot:
            raise web.notfound()
        
        if repo:
            return self.update_repo(repo[0])
        else:
            return self.update_chroot(chroot[0])
    
    def update_repo(self, repo):

        s = subprocess.Popen(["autobuild-repo.py", "update", repo])
        if s.wait() == 0:
            t = web.template.Template(self.template)
            return t(repo)
        else:
            raise web.notfound()
    
    def update_chroot(self, chroot):

        result = os.system("sudo autobuild-builder.py update " + commands.mkarg(chroot))
        if result == 0:
            t = web.template.Template(self.template)
            return t(chroot)
        else:
            raise web.notfound()

class Info(Base):

    """Handles requests for information about chroots."""
    
    title = "Information"
    template = ("$def with (title, dist, suite, url, public_key, this_url, key)\n"
                "<html>\n<head><title>$title</title></head>\n"
                "<body>\n"
                "<h1>$title</h1>\n"
                '<p>Location: <a href="$url">$url</a></p>\n'
                "<h2>Usage</h2>\n"
                "<p>Download this page and install the repository key using the following commands:</p>\n"
                "<pre>\n"
                'wget "$this_url" -O ${key}.key\n'
                "sudo apt-key add ${key}.key\n"
                "</pre>\n"
                "<p>Copy the following lines into your <tt>/etc/apt/sources.list</tt> file:</p>"
                "<pre>\n"
                "deb $url $dist $suite\n"
                "deb-src $url $dist $suite\n"
                "</pre>\n"
                "<p>Update the lists of packages on your system:</p>\n"
                "<pre>\n"
                "sudo apt-get update\n"
                "</pre>\n"
                "<h2>Repository Key</h2>\n"
                "<pre>\n"
                "$public_key\n"
                "</pre>\n"
                "</body>\n</html>\n")
    
    def GET(self):
    
        return self.POST()
    
    def POST(self):
    
        q = self.get_query()
        
        chroot = q.get("chroot")
        if not chroot:
            raise web.notfound()
        
        return self.info_chroot(chroot[0])
    
    def info_chroot(self, chroot):

        c = config.Config("autobuild-apt-repo")
        try:
            path, dist, suite, url = c.lines[chroot]
        except KeyError:
            raise web.notfound()
        
        c = config.Config("autobuild-builder")
        try:
            template, chroots, dist, rc, signing_key = c.lines[chroot]
        except KeyError:
            raise web.notfound()
        
        try:
            public_key = keyhandler.get_key(signing_key)
        except KeyError:
            raise web.notfound()
        
        t = web.template.Template(self.template)
        t.content_type = "text/html"
        return t(self.title, dist, suite, url, public_key, web.ctx.realhome + web.ctx.fullpath, signing_key)

class Revision(Base):

    """Handles requests to obtain latest revisions of source repositories."""

    template = ("$def with (text)\n"
                "$text")
    
    def GET(self):

        q = self.get_query()

        repo = q.get("repo")
        if not repo:
            raise web.notfound()
        
        return self.revision(repo[0])
    
    def revision(self, repo):

        s = subprocess.Popen(["autobuild-repo.py", "revision", repo],
                             stdout=subprocess.PIPE)
        if s.wait() == 0:
            t = web.template.Template(self.template)
            return t(s.stdout.read())
        else:
            raise web.notfound()

class Repos:

    """Handles requests to list the available source repositories."""

    title = "Repositories"
    config = "autobuild-repo"
    template = ("$def with (title, repos)\n"
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

        t = web.template.Template(self.template)
        t.content_type = "text/html"
        return t(self.title, labels)

class Chroots(Repos):

    """Handles requests to list the available chroots."""

    title = "Build Environments"
    config = "autobuild-builder"

class Build(Base):

    """Handles requests to build the contents of a source repository in a chroot."""

    template = ("$def with (chroot, repo)\n"
                "<html>\n<head><title>Building $repo in $chroot</title></head>\n"
                "<body>\n"
                "<p>Started build of $repo for $chroot.</p>"
                '<ul><li><a href="/log?chroot=$(chroot)&repo=$(repo)&log=stdout">stdout</a></li>\n'
                '    <li><a href="/log?chroot=$(chroot)&repo=$(repo)&log=stderr">stderr</a></li></ul>\n'
                "</body>\n</html>\n")
    
    def GET(self):
    
        q = self.get_query()

        chroot = q.get("chroot")
        repo = q.get("repo")
        build_type = q.get("build_type")
        if not chroot or not repo:
            raise web.notfound()
        
        if build_type:
            build_type = build_type[0]
            if build_type not in ("source", "source-changes", "default"):
                raise web.notfound("Invalid build type specified.")
        else:
            build_type = "default"

        return self.build(chroot[0], repo[0], build_type)

    def build(self, chroot, repo, build_type):
    
        global process_manager
        current_dir = os.path.abspath(os.curdir)

        try:
            repo_conf = config.Config("autobuild-repo")
            repo_path = repo_conf.lines[repo][0]
            debian_dir = repo_conf.lines[repo][2]
            
            build_conf = config.Config("autobuild-builder")
            if not build_conf.check_label(chroot):
                raise web.notfound()

            fixes_dir = config.Config("autobuild-fixes", load = False)

        except KeyError:
            raise web.notfound()
        
        # Check for an existing process and reserve space for a new one.
        path = processes.manager.claim_process(chroot, repo)
        if not path:
            raise web.notfound("Not starting build")
        
        current_dir = os.path.abspath(os.curdir)

        # Read the changelog for the project in the repository.
        changelog_path = os.path.join(repo_path, debian_dir, "changelog")
        
        if not os.path.exists(changelog_path):
            processes.manager.remove_lockfile(path)
            raise web.notfound("No changelog found: %s/changelog" % debian_dir)
        
        ch = Changelog(open(changelog_path))
        snapshot_name = ch.package + "-" + ch.upstream_version
        snapshot_archive_name = ch.package + "_" + ch.upstream_version

        # Create a snapshot of the latest revision of the repository.
        snapshot_dir = tempfile.mkdtemp()
        snapshot_subdir = os.path.join(snapshot_dir, snapshot_name)
        result = os.system("autobuild-repo.py snapshot " + commands.mkarg(repo) + " " + \
                           commands.mkarg(snapshot_subdir))

        if result != 0:
            # Remove the snapshot directory if a snapshot couldn't be created.
            shutil.rmtree(snapshot_dir)
            processes.manager.remove_lockfile(path)
            raise web.notfound("Failed to create a snapshot")
        
        # Remove existing output/status log files.
        stdout_path, stderr_path, result_path = processes.manager.output_paths(path)
        for p in stdout_path, stderr_path, result_path:
            if os.path.exists(p):
                os.remove(p)
            
        # Enter the snapshot directory.
        os.chdir(snapshot_subdir)
        
        # Apply any fixes that may be required.
        fixes_path = os.path.join(fixes_dir.path, repo)
        if os.path.exists(fixes_path):
            try:
                result = os.system(fixes_path + " " + commands.mkarg(chroot) + \
                                   " 1>> " + commands.mkarg(stdout_path) + \
                                   " 2>> " + commands.mkarg(stderr_path))
                if result != 0:
                    processes.manager.remove_lockfile(path)
                    open(result_path, "w").write(str(result))
                    raise web.notfound("Failed to fix snapshot before building")

            except IOError:
                pass
        
        pid = os.fork()
        if pid == 0:

            # Child process (pid is 0)
            result = os.system("autobuild-builder.py debuild " + \
                               commands.mkarg(chroot) + " " + \
                               commands.mkarg(build_type) + \
                               " 1>> " + commands.mkarg(stdout_path) + \
                               " 2>> " + commands.mkarg(stderr_path))

            open(result_path, "w").write(str(result))

            # Remove the lock file and delete the snapshot directory.
            processes.manager.remove_lockfile(path)
            shutil.rmtree(snapshot_dir)
            sys.exit(result)
        else:
            # Parent process (pid is child pid)
            processes.manager.update_process(path, pid)

        os.chdir(current_dir)

        t = web.template.Template(self.template)
        return t(chroot, repo)

class Products(Base):

    """Handles requests to list the products made using a chroot."""

    template = ("$def with (title, chroot, repo, products)\n"
                "<html>\n<head><title>$title</title></head>\n"
                "<body>\n"
                "<h1>$title</h1>\n"
                "<dl>\n"
                "$for (name, version), files in products:\n"
                "    <dt>$name $version</dt>\n"
                "    $for file in files:\n"
                '        <dd><a href="$("/product/%s/%s" % (chroot, file["name"]))">$file["name"]</a></dd>\n'
                "</dl>\n"
                "</body>\n</html>\n")
    
    def GET(self):
    
        q = self.get_query()
        
        chroot = q.get("chroot")
        repo = q.get("repo")
        if not chroot or not repo:
            raise web.notfound()
        
        return self.products(chroot[0], repo[0])

    def products(self, chroot, repo):

        p = self.get_product_files(chroot, repo)
        t = web.template.Template(self.template)
        return t("Products", chroot, repo, p)
    
    def get_product_files(self, chroot, repo):

        c = config.Config(Chroots.config)
        b = builder.Builder(c)
        
        c = config.Config(Repos.config)
        info = c.lines[repo]
        if len(info) == 4:
            published_name = info[3]
        else:
            published_name = repo
        
        try:
            products = b.products(chroot)
        except KeyError:
            raise notfound("No such chroot")
        
        keys = filter(lambda key: key[0].startswith(published_name), products.keys())
        keys.sort()
        
        p = []
        for key in keys:
            files = {}
            for product in products[key]:
                for file in product["Files"]:
                    files[file["name"]] = file
            files = files.values()
            files.sort()
            p.append((key, files))

        return p

class Product(Base):

    """Handles requests for specific build products."""

    def GET(self, path):
    
        pieces = path.split("/")
        if len(pieces) != 2:
            raise web.notfound()
        
        chroot, file_name = pieces
        
        if not chroot or not file_name:
            raise web.notfound()
        
        web.header("Content-Disposition", 'attachment; filename="%s"' % file_name)
        return self.product(chroot, file_name)

    def product(self, chroot, file_name):

        c = config.Config(Chroots.config)
        b = builder.Builder(c)
        
        try:
            info = b.info(chroot)
        except KeyError:
            raise notfound("No such chroot")
        
        file_path = os.path.join(info["products"], file_name)

        return open(file_path, "rb").read()

class Log(Base):

    """Handles requests for log files."""

    template = ("$def with (title, text)\n"
                "<html>\n<head><title>$title</title></head>\n"
                "<body>\n"
                "<h1>$title</h1>\n"
                "<pre>\n"
                "$text\n"
                "</pre>\n"
                '<a name="end"></a>\n'
                "</body>\n</html>\n")

    def GET(self):
    
        q = self.get_query()
        
        chroot = q.get("chroot")
        repo = q.get("repo")
        log = q.get("log")
        if not chroot or not repo or not log:
            raise web.notfound()
        
        return self.log(chroot[0], repo[0], log[0])

    def log(self, chroot, repo, log):
    
        label = processes.manager.process_path(chroot, repo)
        file_name = label + "." + log
        
        if file_name not in processes.manager.output_paths(label):
            raise web.notfound("Failed to find log file")
        
        file_path = os.path.join(processes.manager.temp_dir, file_name)

        t = web.template.Template(self.template)
        title = "Log for " + repo + " in " + chroot
        text = open(file_path, "rb").read()
        return t(title, text)

class Publish(Base):

    """Handles requests for publication of build products in apt repositories."""
    
    config = "autobuild-apt-repo"

    def GET(self):

        q = self.get_query()
        
        chroot = q.get("chroot")
        repo = q.get("repo")
        if not chroot or not repo:
            raise web.notfound()
        
        return self.publish(chroot[0], repo[0])
    
    def publish(self, chroot, repo):
    
        c = config.Config(Publish.config)
        
        published = []

        for label in chroot + " " + repo, chroot:
        
            if c.check_label(label):
                published.append(self._publish(c, label, chroot, repo))
            else:
                continue
        
        if not published:
            raise web.notfound("No apt repository defined for %s" % chroot)

        return "\n".join(published)
    
    def _publish(self, c, label, chroot, repo):
    
        repo_path, suite, component, repo_url = c.lines[label]
        repo_component_path = os.path.join(repo_path, "dists", suite, component)
        
        p = Products()
        products = p.get_product_files(chroot, repo)

        c = config.Config(Chroots.config)
        b = builder.Builder(c)
        
        try:
            info = b.info(chroot)
        except KeyError:
            raise notfound("No such chroot: " + chroot)
        
        all_file_names = []

        for (name, version), files in products:

            file_names = map(lambda f: os.path.join(info["products"], f["name"]), files)
            result = os.system("python-apt-repo-setup.py add " + \
                               commands.mkarg(repo_component_path) + \
                               " " + " ".join(map(commands.mkarg, file_names)))
            if result != 0:
                raise web.notfound("Failed to add %s files to the apt repository" % name)

            all_file_names += file_names
        
        result = os.system("python-apt-repo-setup.py update " + commands.mkarg(repo_path))
        if result != 0:
            raise web.notfound("Failed to update the apt repository")
        
        result = os.system("python-apt-repo-setup.py sign " + commands.mkarg(repo_path) + " " + commands.mkarg(suite))
        if result != 0:
            raise web.notfound("Failed to sign the apt repository")
        
        return "Files added to %s (%s):\n%s\n" % (repo_url, repo_component_path, "\n".join(all_file_names))

class Overview:

    """Handles requests for an overview of the available chroots, source repositories
    and the status of any builds."""

    template = ("$def with (title, chroots, repos, apt_repos, status)\n"
                "<html>\n<head><title>$title</title>\n"
                '<style type="text/css">\n'
                '  .success { background-color: #c0f0c0; color: black }\n'
                '  .started { background-color: #f0c080; color: black }\n'
                '  .failure { background-color: #f0c0c0; color: black }\n'
                '  .commands { font-size: smaller }\n'
                '  table { border: 1px solid #808080 }\n'
                '  .left-heading { text-align: left }\n'
                '</style>\n'
                "</head>\n"
                "<body>\n"
                "<h1>$title</h1>\n"
                '<table cellspacing="4" cellpadding="2">\n'
                "    <tr>\n"
                "    <th></th>\n"
                "$for chroot in chroots:\n"
                '    <th>$chroot <span="commands">(<a href="/info?chroot=$chroot">info</a>, '
                '                                  <a href="/update?chroot=$chroot">update</a>)</span></th>\n'
                "</tr>\n"
                "$for repo in repos:\n"
                "    <tr>\n"
                '    <th class="left-heading">$repo<br />\n'
                '      <span class="commands">(<a href="/revision?repo=$repo">revision</a>,\n'
                '                              <a href="/update?repo=$repo">update</a>)</span></th>\n'
                "    $for chroot in chroots:\n"
                "        $status(chroot, repo, apt_repos)\n"
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
        c = config.Config(Publish.config)
        apt_repos = c.lines.keys()
        
        t = web.template.Template(self.template)
        t.content_type = "text/html"
        return t("Overview", chroots, repos, apt_repos, self.status)

    def status(self, chroot, repo, apt_repos):
    
        status, time_str = processes.manager.status(chroot, repo)
        if status == "Building":
            return ('<td class="started">Started (%(time)s)<br />\n'
                    '<span class="commands">(<a href="/log?chroot=%(chroot)s&repo=%(repo)s&log=stdout">stdout</a>, '
                    '<a href="/log?chroot=%(chroot)s&repo=%(repo)s&log=stderr">stderr</a>)</span></td>') % \
                    {"chroot": chroot, "repo": repo, "time": time_str}
        
        elif status == "Built":
            t = ('<td class="success">Built (%(time)s)<br />\n'
                 '<span class="commands">(<a href="/products?chroot=%(chroot)s&repo=%(repo)s">products</a>, '
                 '<a href="/build?chroot=%(chroot)s&repo=%(repo)s">rebuild</a>, '
                 '<a href="/build?chroot=%(chroot)s&repo=%(repo)s&build_type=source">full source</a>, '
                 '<a href="/build?chroot=%(chroot)s&repo=%(repo)s&build_type=source-changes">source changes</a>')
            if chroot in apt_repos:
                 t += ', <a href="/publish?chroot=%(chroot)s&repo=%(repo)s">publish</a>'
            
            t += ')</span></td>'
            return t % {"chroot": chroot, "repo": repo, "time": time_str}
        
        elif status == "Failed":
            return ('<td class="failure">Failed (%(time)s)<br />\n'
                    '<span class="commands">(<a href="/build?chroot=%(chroot)s&repo=%(repo)s">build</a>, '
                    '<a href="/build?chroot=%(chroot)s&repo=%(repo)s&build_type=source">full source</a>, '
                    '<a href="/build?chroot=%(chroot)s&repo=%(repo)s&build_type=source-changes">source changes</a>, '
                    '<a href="/log?chroot=%(chroot)s&repo=%(repo)s&log=stdout">stdout</a>, '
                    '<a href="/log?chroot=%(chroot)s&repo=%(repo)s&log=stderr">stderr</a>)</span></td>') % \
                    {"chroot": chroot, "repo": repo, "time": time_str}
        else:
            return ('<td>\n'
                    '<span class="commands">(<a href="/build?chroot=%(chroot)s&repo=%(repo)s">build</a>, '
                    '<a href="/build?chroot=%(chroot)s&repo=%(repo)s&build_type=source">full source</a>, '
                    '<a href="/build?chroot=%(chroot)s&repo=%(repo)s&build_type=source-changes">source changes</a>)'
                    '</span></td>') % \
                    {"chroot": chroot, "repo": repo}


if __name__ == "__main__":

    with daemon.DaemonContext():
    
        app = web.application(urls, globals())
        app.run()
