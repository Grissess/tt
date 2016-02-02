# A TT executor

import sys

import ttr
import ctok
import rws

if len(sys.argv) < 2:
    print('Usage:', sys.argv[0], 'ttfile.tt [ttrin] [debug] < input > out.tt', file=sys.stderr)
    exit(1)

fp = open(sys.argv[1], 'r')
exec_toktree = ctok.Tokenizer(fp).tokenize()

print('Compiling executive...', file=sys.stderr)

exec_tree, iters = ttr.RULES.run(exec_toktree);
print('...(took', iters, 'iterations)', file=sys.stderr)

print(exec_tree.pretty(), file=sys.stderr)
exec_res = ttr.Translator().translate(exec_tree)
if len(exec_res) != 1 or not isinstance(exec_res[0], rws.RuleSet):
    print('Bad executive format (need singular RuleSet):', exec_res, file=sys.stderr)
    exit(1)

rules = exec_res[0]
print('Compiling input...', file=sys.stderr)

in_toktree = ctok.Tokenizer(sys.stdin).tokenize()
if len(sys.argv) > 2:
    in_toktree = ttr.RULES.run(in_toktree)[0]
    in_toktree = ttr.Translator().translate(in_toktree)[0]
print(rules, file=sys.stderr)
print('Executing on input...', file=sys.stderr)
if len(sys.argv) > 3:
    rws.Rule.action = lambda self, rule, match, bind, res: print('Fired:', rule, '\nMatching:', match, '\nBindings:', bind, '\nResulting in', res, '\n---\n')
out, iters = rules.run(in_toktree)
print('...(took', iters, 'iterations)', file=sys.stderr)
print(out)
print('Done.', file=sys.stderr)
