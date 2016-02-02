# A TT executor

import sys
import os
import argparse
import pickle

import ttr
import ctok
import rws

parser = argparse.ArgumentParser(description='Execute TT files')
parser.add_argument('ttfile', help='File to execute')
parser.add_argument('-t', '--ttr', dest='ttr', action='store_true', help='Also process the input through TTR (must then be an ordinary tree)')
parser.add_argument('-u', '--unttr', dest='unttr', action='store_true', help='Process output through Translator (must be a TTR tree)')
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Show productions as they fire')
parser.add_argument('-c', '--compile', dest='compile', action='store_true', help='Compile the input TT unconditionally (default whenever the TT is newer)')
args = parser.parse_args()

if args.ttfile.endswith('.ttc'):
    fname_compiled = args.ttfile
    fname_source = args.ttfile[:-1]
elif args.ttfile.endswith('.tt'):
    fname_compiled = args.ttfile + 'c'
    fname_source = args.ttfile
else:
    fname_compiled = args.ttfile + '.ttc'
    fname_source = args.ttfile + '.tt'

try:
    st_compiled = os.stat(fname_compiled)
except FileNotFoundError:
    st_compiled = None
try:
    st_source = os.stat(fname_source)
except FileNotFoundError:
    st_source = None

if not (st_compiled or st_source):
    print('No files found; stop.', file=sys.stderr)
    exit(1)

if args.compile or (st_source and not st_compiled) or (st_compiled and st_source and st_source.st_mtime > st_compiled.st_mtime):
    fp = open(fname_source, 'r')
    exec_toktree = ctok.Tokenizer(fp).tokenize()

    print('Compiling executive...', file=sys.stderr)

    exec_tree, iters = ttr.RULES.run(exec_toktree);
    print('...(took', iters, 'iterations)', file=sys.stderr)

    print(exec_tree.pretty(), file=sys.stderr)
    exec_res = ttr.Translator().translate(exec_tree)
    if len(exec_res) != 1:
        print('Translation failed! Result was %r'%(exec_res,))
        exit(1)

    rules = exec_res[0]
    print('Writing compiled result...', file=sys.stderr)
    pickle.dump(rules, open(fname_compiled, 'wb'))
else:
    print('Loaded from compiled file', file=sys.stderr)
    rules = pickle.load(open(fname_compiled, 'rb'))

if not isinstance(rules, rws.RuleSet):
    print('Bad executive format (need singular RuleSet):', rules, file=sys.stderr)
    exit(1)

print('Compiling input...', file=sys.stderr)
in_toktree = ctok.Tokenizer(sys.stdin).tokenize()
if args.ttr:
    in_toktree = ttr.RULES.run(in_toktree)[0]
    in_toktree = ttr.Translator().translate(in_toktree)[0]
print(rules, file=sys.stderr)
print('Executing on input...', file=sys.stderr)
if args.verbose:
    rws.Rule.action = lambda self, rule, match, bind, res: print('Fired:', rule, '\nMatching:', match, '\nBindings:', bind, '\nResulting in', res, '\n---\n')
out, iters = rules.run(in_toktree)
if args.unttr:
    print('Translating...', file=sys.stderr)
    out = ttr.Translator().translate(out)
print('...(took', iters, 'iterations)', file=sys.stderr)
print(out)
print('Done.', file=sys.stderr)
