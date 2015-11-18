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

import commands, glob, os, subprocess, sys, tempfile
from debian.changelog import Changelog
from debian.deb822 import Changes, Dsc

from autobuild.config import Config

def check_label(config, label):

    if not config.check_label(label):
    
        sys.stderr.write("The label '%s' is not recognised.\n" % label)
        sys.exit(1)


if __name__ == "__main__":

    if len(sys.argv) >= 2:
    
        command = sys.argv[1]
        config = Config()
        
        if command == "add" and 6 <= len(sys.argv) <= 7:
        
            label, path, method, debian_dir = sys.argv[2:6]
            path = os.path.abspath(path)
            
            # Check to see if the label or path is already known.
            if config.check(label, [path]):
            
                sys.stderr.write("The label or path is already recognised.\n")
                sys.exit(1)
            
            # Reopen the configuration file. Really, we should lock the
            # configuration file to prevent others from modifying the file
            # after we have read it.
            config = Config()
            
            # Add the path to a list in the configuration file.
            if len(sys.argv) == 7:
                published_name = sys.argv[6]
                config.add(label, [path, method, debian_dir, published_name])
            else:
                config.add(label, [path, method, debian_dir])
            config.save()
            
            sys.exit()
    
        elif command == "remove" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the label already exists.
            check_label(config, label)
            
            # Remove the path from a list in the configuration file.
            config.remove(label)
            config.save()
            
            sys.exit()
        
        elif command == "update" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the label already exists.
            check_label(config, label)
            
            path, method = config.lines[label][:2]
            
            # Update the repository in the path by running the appropriate
            # version control command.
            os.chdir(path)
            if os.path.exists(os.path.join(path, ".git")):
                if method == "rebase":
                    result = os.system("git fetch")
                    if result == 0:
                        result = os.system("git rebase")
                else:
                    result = os.system("git pull")
            
            elif os.path.exists(os.path.join(path, ".svn")):
                result = os.system("svn up")
            
            elif os.path.exists(os.path.join(path, ".hg")):
                result = os.system("hg pull")
            else:
                result = -1
            
            if result == 0:
                print "Repository '%s' updated successfully." % label
            else:
                sys.stderr.write("Failed to update repository '%s'.\n" % label)
                sys.exit(1)
            
            sys.exit()
    
        elif command == "revision" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the label already exists.
            check_label(config, label)
            
            path = config.lines[label][0]
            
            # Find the latest revision in the repository by running the appropriate
            # version control command.
            os.chdir(path)
            if os.path.exists(os.path.join(path, ".git")):
                s = subprocess.Popen(["git", "log", "-1"], stdout=subprocess.PIPE)
                result = s.wait()
            elif os.path.exists(os.path.join(path, ".svn")):
                s = subprocess.Popen(["svn", "log", "-l", "1"], stdout=subprocess.PIPE)
                result = s.wait()
            else:
                result = -1
            
            if result == 0:
                print s.stdout.read()
            else:
                sys.stderr.write("Failed to find revision for repository '%s'.\n" % label)
                sys.exit(1)
            
            sys.exit()
    
        elif command == "snapshot" and 3 <= len(sys.argv) <= 4:
        
            label = sys.argv[2]
            
            # Check to see if the label already exists.
            check_label(config, label)
            
            entry = config.lines[label]
            path, method, debian_dir = entry[:3]
            
            # Read the changelog for the project in the repository.
            changelog_path = os.path.join(path, debian_dir, "changelog")
            
            if not os.path.exists(changelog_path):
                sys.stderr.write("No changelog found: %s/changelog.\n" % debian_dir)
                sys.exit(1)
            
            ch = Changelog(open(changelog_path))
            snapshot_name = ch.package + "-" + ch.upstream_version
            snapshot_archive_name = ch.package + "_" + ch.upstream_version
            
            if len(sys.argv) == 4:
                snapshot_dir = sys.argv[3]
            else:
                snapshot_parent_dir = tempfile.mkdtemp()
                snapshot_dir = os.path.join(snapshot_parent_dir, snapshot_name)
            
            # Unpack the current sources from the repository in the path specified
            # to the snapshot directory by running the appropriate version control
            # command.
            os.chdir(path)
            if os.path.exists(os.path.join(path, ".git")):
                # Export the latest revision to an archive into the parent
                # directory of the snapshot directory.
                snapshot_parent_dir, snapshot_name = os.path.split(snapshot_dir)
                archive_path = os.path.join(snapshot_parent_dir, snapshot_name + ".zip")
                
                submodules = [(snapshot_name, path)]

                try:
                    for line in open(".gitmodules").readlines():
                        pieces = line.split("=")
                        if len(pieces) == 2:
                            key = pieces[0].strip()
                            if key == "path":
                                subpath = pieces[1].strip()
                                submodules.append((os.path.join(snapshot_name, subpath),
                                                   os.path.join(path, subpath)))
                
                except IOError:
                    pass

                for prefix, subpath in submodules:
                
                    if not os.path.exists(subpath) or not os.listdir(subpath):
                        continue
                    
                    os.chdir(subpath)
                    result = os.system("git archive --prefix=" + prefix + "/ " + \
                                       "-o " + commands.mkarg(archive_path) + " HEAD")
                    
                    # Unpack the archive into the snapshot directory.
                    os.chdir(snapshot_parent_dir)
                    result = os.system("unzip " + commands.mkarg(archive_path) + \
                                       " 1> /dev/null 2> /dev/null")
                    # Remove the archive.
                    os.remove(archive_path)

                    # Add information about the current git commit.
                    os.chdir(subpath)
                    os.system("git show --format=format:'%H %ci' > " + \
                        os.path.join(snapshot_parent_dir, prefix, ".git_archival.txt"))

            elif os.path.exists(os.path.join(path, ".svn")):
                # Export the latest revision into the snapshot directory,
                # which will be created by svn.
                result = os.system("svn export . " + commands.mkarg(snapshot_dir))

            elif os.path.exists(os.path.join(path, ".hg")):
                # Export the latest revision into the snapshot directory.
                result = os.system("hg archive " + commands.mkarg(snapshot_dir))

            else:
                result = -1
            
            if result == 0:
                print "Repository '%s' updated successfully in %s." % (label, snapshot_dir)
            else:
                sys.stderr.write("Failed to update repository '%s'.\n" % label)
                sys.exit(1)
            
            # Create an archive of the snapshot.
            os.chdir(snapshot_dir)
            os.chdir(os.pardir)
            snapshot_archive = snapshot_archive_name + ".orig.tar.gz"
            result = os.system("tar zcf " + snapshot_archive + " " + snapshot_name)
            if result != 0:
                sys.stderr.write("Failed to create a snapshot archive for %s in %s.\n" % (label, snapshot_dir))
                sys.exit(1)

            sys.exit()

        elif command == "list" and len(sys.argv) == 2:
        
            labels = config.lines.keys()
            labels.sort()
            
            print "\n".join(labels)
            sys.exit()
        
        elif command == "info" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the label already exists.
            check_label(config, label)
            
            entry = config.lines[label]
            path, method, debian_dir = entry[:3]
            
            print label
            print "Location:           ", path
            print "Update method:      ", method
            print "Changelog directory:", debian_dir
            if len(entry) > 3:
                print "Published name:     ", entry[3]
            sys.exit()
    
    sys.stderr.write("Usage: %s add <label> <path> <update method> <packaging directory name>\n" % sys.argv[0])
    sys.stderr.write("       %s remove <label>\n" % sys.argv[0])
    sys.stderr.write("       %s update <label>\n" % sys.argv[0])
    sys.stderr.write("       %s revision <label>\n" % sys.argv[0])
    sys.stderr.write("       %s snapshot <label> <path>\n" % sys.argv[0])
    sys.stderr.write("       %s list\n" % sys.argv[0])
    sys.stderr.write("       %s info <label>\n\n" % sys.argv[0])
    sys.stderr.write("    <packaging directory name> is the name of the directory within the repository\n"
                     "    that contains the distribution packaging files. For example: debian\n\n")
    sys.exit(1)
