#!/usr/bin/env python

import sys, traceback

from autobuild.builder import Builder

def run(function, arguments):

    try:
        function(*arguments)
        return 0
    
    except:
        sys.stderr.write(traceback.format_exc() + "\n")
        return 1


if __name__ == "__main__":

    if len(sys.argv) >= 2:
    
        command = sys.argv[1]
        builder = Builder()
        
        if command == "create" and len(sys.argv) == 6:
        
            sys.exit(run(builder.create, sys.argv[2:]))
        
        elif command == "destroy" and len(sys.argv) == 3:
        
            sys.exit(run(builder.destroy, sys.argv[2:3]))
        
        elif command == "update" and len(sys.argv) == 3:
        
            sys.exit(run(builder.update, sys.argv[2:3]))
        
        elif command == "info" and len(sys.argv) == 3:
        
            sys.exit(run(builder.info, sys.argv[2:3]))
        
        elif command == "hooks" and len(sys.argv) == 3:
        
            sys.exit(run(builder.hooks, sys.argv[2:3]))
        
        elif command == "products" and len(sys.argv) == 3:
        
            sys.exit(run(builder.products, sys.argv[2:3]))
        
        elif command == "list" and len(sys.argv) == 2:
        
            sys.exit(run(builder.list, ()))
        
        elif command == "build" and len(sys.argv) == 4:
        
            sys.exit(run(builder.build, sys.argv[2:4]))
        
        elif command == "debuild" and len(sys.argv) == 3:
        
            sys.exit(run(builder.debuild, sys.argv[2:3]))
        
        elif command == "remove" and len(sys.argv) == 4:
        
            sys.exit(run(builder.remove, sys.argv[2:4]))
    
    sys.stderr.write("Usage: %s create <label> <template> <install dir> <distribution>\n" % sys.argv[0])
    sys.stderr.write("       %s destroy <label>\n" % sys.argv[0])
    sys.stderr.write("       %s update <label>\n" % sys.argv[0])
    sys.stderr.write("       %s list\n" % sys.argv[0])
    sys.stderr.write("       %s info <label>\n" % sys.argv[0])
    sys.stderr.write("       %s hooks <label>\n" % sys.argv[0])
    sys.stderr.write("       %s products <label>\n" % sys.argv[0])
    sys.stderr.write("       %s build <label> <package name or .dsc file>\n" % sys.argv[0])
    sys.stderr.write("       %s debuild <label>\n" % sys.argv[0])
    sys.stderr.write("       %s remove <label> <package name>\n" % sys.argv[0])
    sys.exit(1)
