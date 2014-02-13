#!/usr/bin/env python

import cgi, commands, os, shutil, subprocess, sys, tempfile
from debian.changelog import Changelog
import daemon
import web

from autobuild import builder, config, processes

urls = ("/", "Overview",
        "/update", "Update",
        "/repos", "Repos",
        "/chroots", "Chroots",
        "/build", "Build",
        "/products", "Products",
        "/product", "Product")

class Base:

    def get_query(self):
    
        if web.ctx.query.startswith("?"):
            q = cgi.parse_qs(web.ctx.query[1:])
        else:
            q = {}

        return q

class Update(Base):

    template = ("$def with (repo)\n"
                     "Updated $repo.")
    
    def POST(self):
    
        q = self.get_query()

        repo = q.get("repo")
        if not repo:
            raise web.notfound()
        else:
            repo = repo[0]
        
        return self.update(repo)

    def update(self, repo):

        s = subprocess.Popen(["autobuild-repo.py", "update", repo])
        if s.wait() == 0:
            t = web.template.Template(self.template)
            return t(repo)
        else:
            raise web.notfound()

class Repos:

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

    title = "Build Environments"
    config = "autobuild-builder"

class Build(Base):

    template = ("$def with (chroot, repo)\n"
                "Started build of $repo for $chroot.")
    
    def GET(self):
    
        q = self.get_query()

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

        # Read the changelog for the project in the repository.
        changelog_path = os.path.join(repo_path, "debian", "changelog")
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
            raise web.notfound("Failed to create a snapshot")
        
        # Create an archive of the snapshot.
        os.chdir(snapshot_dir)
        snapshot_archive = snapshot_archive_name + ".orig.tar.gz"
        result = os.system("tar zcf " + snapshot_archive + " " + snapshot_name)
        if result != 0:
            # Remove the snapshot directory if a snapshot archive couldn't be created.
            shutil.rmtree(snapshot_dir)
            raise web.notfound("Failed to create a snapshot archive")

        # Enter the snapshot directory.
        os.chdir(snapshot_subdir)
        
        pid = os.fork()
        if pid == 0:

            # Child process (pid is 0)
            stdout_path, stderr_path, result_path = processes.output_paths(path)
            for p in stdout_path, stderr_path, result_path:
                if os.path.exists(p):
                    os.remove(p)
            
            result = os.system("autobuild-builder.py debuild " + commands.mkarg(chroot) + \
                               " 1> " + commands.mkarg(stdout_path) + \
                               " 2> " + commands.mkarg(stderr_path))

            open(result_path, "w").write(str(result))

            # Remove the lock file and delete the snapshot directory.
            processes.remove_lockfile(path)
            shutil.rmtree(snapshot_dir)
            sys.exit(result)
        else:
            # Parent process (pid is child pid)
            processes.update_process(path, pid)

        os.chdir(current_dir)

        t = web.template.Template(self.template)
        return t(chroot, repo)

class Products(Base):

    template = ("$def with (title, chroot, repo, products)\n"
                "<html>\n<head><title>$title</title></head>\n"
                "<body>\n"
                "<h1>$title</h1>\n"
                "<dl>\n"
                "$for (name, version), files in products:\n"
                "    <dt>$name $version</dt>\n"
                "    $for file in files:\n"
                '        <dd><a href="$("/product?chroot=%s&file=%s" % (chroot, file["name"]))">$file["name"]</a></dd>\n'
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

        c = config.Config(Chroots.config)
        b = builder.Builder(c)
        
        try:
            products = b.products(chroot)
        except KeyError:
            raise notfound("No such chroot")
        
        keys = filter(lambda key: key[0].startswith(repo), products.keys())
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
        
        t = web.template.Template(self.template)
        return t("Products", chroot, repo, p)

class Product(Base):

    def GET(self):
    
        q = self.get_query()
        
        chroot = q.get("chroot")
        file_name = q.get("file")
        if not chroot or not file_name:
            raise web.notfound()
        
        web.header("Content-Disposition", 'attachment; filename="%s"' % file_name[0])
        return self.product(chroot[0], file_name[0])

    def product(self, chroot, file_name):

        c = config.Config(Chroots.config)
        b = builder.Builder(c)
        
        try:
            info = b.info(chroot)
        except KeyError:
            raise notfound("No such chroot")
        
        file_path = os.path.join(info["products"], file_name)

        return open(file_path, "rb").read()

class Overview:

    template = ("$def with (title, chroots, repos, status)\n"
                "<html>\n<head><title>$title</title>\n"
                '<style type="text/css">\n'
                '  .success { color: green }\n'
                '  .failure { color: red }\n'
                '</style>\n'
                "</head>\n"
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
                "        <td>$status(chroot, repo)</td>\n"
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
        
        t = web.template.Template(self.template)
        t.content_type = "text/html"
        return t("Overview", chroots, repos, self.status)

    def status(self, chroot, repo):
    
        status = processes.status(chroot, repo)
        if status == "Building":
            return "Building"
        elif status == "Built":
            return ('<span class="success">Built</span> '
                    '(<a href="/products?chroot=%(chroot)s&repo=%(repo)s">products</a>, '
                    '<a href="/build?chroot=%(chroot)s&repo=%(repo)s">rebuild</a>)') % \
                    {"chroot": chroot, "repo": repo}
        elif status == "Failed":
            return ('<span class="failure">Failed</span> '
                    '(<a href="/build?chroot=%(chroot)s&repo=%(repo)s">build</a>)') % \
                    {"chroot": chroot, "repo": repo}
        else:
            return '(<a href="/build?chroot=%(chroot)s&repo=%(repo)s">build</a>)' % \
                   {"chroot": chroot, "repo": repo}


if __name__ == "__main__":

    with daemon.DaemonContext():
    
        app = web.application(urls, globals())
        app.run()
