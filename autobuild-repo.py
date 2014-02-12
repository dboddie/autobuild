#!/usr/bin/env python

import commands, glob, os, sys, tempfile
from debian.deb822 import Changes, Dsc

from autobuild.config import Config

if __name__ == "__main__":

    if len(sys.argv) >= 2:
    
        command = sys.argv[1]
        config = Config()
        
        if command == "add" and len(sys.argv) == 4:
        
            label, path = sys.argv[2:]
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
            config.add(label, [path])
            config.save()
            
            sys.exit()
    
        elif command == "remove" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the label already exists.
            config.check_label(label)
            
            # Remove the path from a list in the configuration file.
            config.remove(label)
            config.save()
            
            sys.exit()
        
        elif command == "update" and len(sys.argv) == 3:
        
            label = sys.argv[2]
            
            # Check to see if the label already exists.
            config.check_label(label)
            
            [path] = config.lines[label]
            
            # Update the repository in the path by running the appropriate
            # version control command.
            os.chdir(path)
            if os.path.exists(os.path.join(path, ".git")):
                result = os.system("git pull")
            elif os.path.exists(os.path.join(path, ".svn")):
                result = os.system("svn up")
            else:
                result = -1
            
            if result == 0:
                print "Repository '%s' updated successfully." % label
            else:
                sys.stderr.write("Failed to update repository '%s'.\n" % label)
                sys.exit(1)
            
            sys.exit()
    
        elif command == "snapshot" and len(sys.argv) == 4:
        
            label = sys.argv[2]
            snapshot_dir = sys.argv[3]
            
            # Check to see if the label already exists.
            config.check_label(label)
            
            [path] = config.lines[label]
            
            # Unpack the current sources from the repository in the path specified
            # to the snapshot directory by running the appropriate version control
            # command.
            os.chdir(path)
            if os.path.exists(os.path.join(path, ".git")):
                # Export the latest revision to an archive into the parent
                # directory of the snapshot directory.
                snapshot_parent_dir, snapshot_name = os.path.split(snapshot_dir)
                archive_path = os.path.join(snapshot_parent_dir, snapshot_name + ".zip")
                result = os.system("git archive --prefix=" + snapshot_name + "/ " + \
                                   "-o " + commands.mkarg(archive_path) + " HEAD")
                # Unpack the archive into the snapshot directory.
                os.chdir(snapshot_parent_dir)
                result = os.system("unzip " + commands.mkarg(archive_path))
                # Remove the archive.
                os.remove(archive_path)
            elif os.path.exists(os.path.join(path, ".svn")):
                # Export the latest revision into the snapshot directory,
                # which will be created by svn.
                result = os.system("svn export . " + commands.mkarg(snapshot_dir))
            else:
                result = -1
            
            if result == 0:
                print "Repository '%s' updated successfully." % label
            else:
                sys.stderr.write("Failed to update repository '%s'.\n" % label)
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
            config.check_label(label)
            
            [path] = config.lines[label]
            
            print label
            print "Location:", path
            sys.exit()
    
    sys.stderr.write("Usage: %s add <label> <path>\n" % sys.argv[0])
    sys.stderr.write("       %s remove <label>\n" % sys.argv[0])
    sys.stderr.write("       %s update <label>\n" % sys.argv[0])
    sys.stderr.write("       %s snapshot <label> <path>\n" % sys.argv[0])
    sys.stderr.write("       %s list\n" % sys.argv[0])
    sys.stderr.write("       %s info <label>\n" % sys.argv[0])
    sys.exit(1)
