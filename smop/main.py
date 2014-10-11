# SMOP compiler -- Simple Matlab/Octave to Python compiler
# Copyright 2011-2013 Victor Leikehman

import version
import sys,cPickle,glob,os
import getopt,re
import lexer,parse,resolve,backend,options,node,graphviz
import networkx as nx
import readline

#from version import __version__
__version__ = version.__version__

def usage():
    print "SMOP compiler version " + __version__
    print """Usage: smop [options] file-list
    Options:
    -V --version
    -X --exclude=FILES      Ignore files listed in comma-separated list FILES
    -d --dot=REGEX          For functions whose names match REGEX, save debugging
                            information in "dot" format (see www.graphviz.org).
                            You need an installation of graphviz to use --dot
                            option.  Use "dot" utility to create a pdf file.
                            For example: 
                                $ python main.py fastsolver.m -d "solver|cbest"
                                $ dot -Tpdf -o resolve_solver.pdf resolve_solver.dot
    -h --help
    -o --output=FILENAME    By default create file named a.py
    -o- --output=-          Use standard output
    -s --strict             Stop on the first error
    -v --verbose
"""

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],
                                       "d:ho:vVsX:", 
                                       [
                                        "dot=",
                                        "exclude",
                                        "help",
                                        "output=",
                                        "strict",
                                        "verbose",
                                        "version",
                                       ])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    exclude_list = []
    output = None
    verbose = 0
    strict = 0
    dot = None

    for o, a in opts:
        if o in ("-s", "--strict"):
            strict = 1
        elif o in ("-d", "--dot"):
            dot = re.compile(a)
        elif o in ("-X", "--exclude"):
            exclude_list += a.split(",")
        elif o in ("-v", "--verbose"):
            verbose += 1
        elif o in ("-V", "--version"):
            print "SMOP compiler version " + __version__
            sys.exit()
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
        else:
            assert False, "unhandled option"

    """
    if not args:
        usage()
        sys.exit()
    """
    if not args:
        symtab = {}
        print "? for help"
        while 1:
            try:
                buf = raw_input("=>> ")
                if not buf:
                    continue
                while buf[-1] == "\\":
                    buf = buf[:-1] + "\n" + raw_input("... ")
                #print buf
                if buf[0] == '?':
                    print '!a="def f(): \\n\\treturn 123"'
                    print "!exec a"
                    print "!print f"
                    print "!print f()"
                    print "!reload(backend)"
                    print "=>> function t=foo(a) \\"
                    print "... t=123"
                    print "!exec foo(3)"

                    continue
                if buf[0] == '!':
                    try:
                        exec buf[1:]
                    except:
                        print "eh?"
                    continue
                t = parse.parse(buf if buf[-1]=='\n' else buf+'\n')
                if not t:
                    continue
            except EOFError:
                return
            resolve.resolve(t,symtab)
            _ = backend.backend(t)
            print _

    if not output:
        output = "a.py"
    fp = open(output,"w") if output != "-" else sys.stdout
    print >> fp, "# Autogenerated with SMOP version " + __version__
    print >> fp, "# " + " ".join(sys.argv)
    print >> fp, """
from __future__ import division
try:
    from runtime import *
except ImportError:
    from smop.runtime import *
"""

    for pattern in args:
        for filename in glob.glob(os.path.expanduser(pattern)):
            if not filename.endswith(".m"):
                print "\tIngored file: '%s'" % filename
                continue
            if os.path.basename(filename) in exclude_list:
                print "\tExcluded file: '%s'" % filename
                continue
            if verbose:
                print filename
            buf = open(filename).read().replace("\r\n","\n")
            func_list = parse.parse(buf if buf[-1]=='\n' else buf+'\n',filename)
            if not func_list and strict:
                sys.exit(-1)

            for func_obj in func_list: 
                try:
                    func_name = func_obj.head.ident.name
                    if verbose:
                        print "\t",func_name
                except AttributeError:
                    if verbose:
                        print "\tJunk ignored"
                    if strict:
                        sys.exit(-1)
                    continue
                fp0 = open("parse_"+func_name+".dot","w") if dot and dot.match(func_name) else None
                if fp0:
                    graphviz.graphviz(func_obj,fp0)
                if options.do_resolve:
                    G = resolve.resolve(func_obj)

            for func_obj in func_list:
                s = backend.backend(func_obj)
                print >> fp, s

if __name__ == "__main__":
    main()
