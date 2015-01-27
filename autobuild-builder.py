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

import sys, traceback

from autobuild.builder import Builder

def run(function, arguments):

    try:
        return function(*arguments)
    
    except:
        sys.stderr.write(traceback.format_exc() + "\n")
        sys.exit(1)

def run_result(function, arguments):

    result = run(function, arguments)
    if result != 0:
        return 1
    else:
        return 0

if __name__ == "__main__":

    if len(sys.argv) >= 2:
    
        command = sys.argv[1]
        builder = Builder()
        
        if command == "create" and len(sys.argv) == 6:
        
            sys.exit(run_result(builder.create, sys.argv[2:]))
        
        elif command == "destroy" and len(sys.argv) == 3:
        
            sys.exit(run(builder.destroy, sys.argv[2:3]))
        
        elif command == "login" and len(sys.argv) == 3:
        
            sys.exit(run(builder.login, sys.argv[2:3]))
        
        elif command == "update" and len(sys.argv) == 3:
        
            sys.exit(run(builder.update, sys.argv[2:3]))
        
        elif command == "info" and len(sys.argv) == 3:
        
            info = run(builder.info, sys.argv[2:3])

            print sys.argv[2]
            print "Template:          ", info["template"]
            print "Installation:      ", info["installation"]
            print "Distribution:      ", info["distribution"]
            print "Configuration file:", info["configuration"]
            print "Hooks directory:   ", info["hooks"]
            print "Products directory:", info["products"]
            print "Signing key:       ", info["signing key"]
            sys.exit()
        
        elif command == "hooks" and len(sys.argv) == 3:
        
            sys.exit(run(builder.hooks, sys.argv[2:3]))
        
        elif command == "products" and len(sys.argv) == 3:
        
            products = run(builder.products, sys.argv[2:3])
            keys = products.keys()
            keys.sort()

            for name, version in keys:
                print name, version

            sys.exit()
        
        elif command == "list" and len(sys.argv) == 2:
        
            labels = run(builder.list, ())
            print "\n".join(labels)
            sys.exit()
        
        elif command == "build" and len(sys.argv) == 4:
        
            sys.exit(run_result(builder.build, sys.argv[2:4]))
        
        elif command == "debuild" and 3 <= len(sys.argv) <= 4:
        
            sys.exit(run_result(builder.debuild, sys.argv[2:4]))
        
        elif command == "remove" and len(sys.argv) == 4:
        
            sys.exit(run(builder.remove, sys.argv[2:4]))
    
    sys.stderr.write("Usage: %s create <label> <template> <install dir> <distribution>\n" % sys.argv[0])
    sys.stderr.write("       %s destroy <label>\n" % sys.argv[0])
    sys.stderr.write("       %s login <label>\n" % sys.argv[0])
    sys.stderr.write("       %s update <label>\n" % sys.argv[0])
    sys.stderr.write("       %s list\n" % sys.argv[0])
    sys.stderr.write("       %s info <label>\n" % sys.argv[0])
    sys.stderr.write("       %s hooks <label>\n" % sys.argv[0])
    sys.stderr.write("       %s products <label>\n" % sys.argv[0])
    sys.stderr.write("       %s build <label> <package name or .dsc file>\n" % sys.argv[0])
    sys.stderr.write("       %s debuild <label> [source]\n" % sys.argv[0])
    sys.stderr.write("       %s remove <label> <package name>\n" % sys.argv[0])
    sys.exit(1)
