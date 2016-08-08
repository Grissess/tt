# TT translator for rulesets in the simple syntax

from rws import *

# Rule.action = lambda self, rule, match, bind, res: print('Fired', rule, 'matching', match, 'bindings', bind, 'resulting in', res)

ELEMS = {'Atom': 1, 'MatchPoint': 1, 'Negator': 1, 'Disjunctor': 1, 'Conjunctor': 1, 'Group': 2, 'Sequence': 2, 'Set': 2}
CHILD_RULES = []
for et, eaffin in ELEMS.items():
    egrp = Group(et, *map(MatchPoint, map(str, range(eaffin))))
    # Child initiators
    CHILD_RULES.append(Rule(Sequence('s1', Group('oper', Atom('[')), egrp), Sequence('s1', Group('Child', egrp))))
    for caffin in (1, 2):
        cgrp = Group('Child', *[MatchPoint('c%d'%(i,)) for i in range(caffin)])
        # Child continuation
        CHILD_RULES.append(Rule(Sequence('s1', cgrp, Group('oper', Atom(',')), egrp), Sequence('s1', Group('Child', cgrp, egrp))))
for caffin in (1, 2):
    cgrp = Group('Child', *[MatchPoint('c%d'%(i,)) for i in range(caffin)])
    # Child terminators
    CHILD_RULES.append(Rule(Sequence('s1', cgrp, Group('oper', Atom(']'))), Sequence('s1', Group('Children', cgrp))))

RULES = RuleSet(*([
    # Atoms and MatchPoints
    Rule(Sequence('s1', Group('string', MatchPoint('X'))), Sequence('s1', Group('Atom', MatchPoint('X')))),
    Rule(Sequence('s1', Group('oper', Atom('<')), Group('ident', MatchPoint('X')), Group('oper', Atom('>'))), Sequence('s1', Group('MatchPoint', MatchPoint('X')))),
    Rule(Sequence('s1', Group('oper', Atom('<')), Group('oper', Atom('>'))), Sequence('s1', Group('MatchPoint', Atom('')))),
    # Groups and Sequences
    Rule(Sequence('s1', Group('Atom', MatchPoint('X')), Group('Children', MatchPoint('Y'))), Sequence('s1', Group('Group', MatchPoint('X'), Group('Children', MatchPoint('Y'))))),
    Rule(Sequence('s1', Group('ident', MatchPoint('X')), Group('Children', MatchPoint('Y'))), Sequence('s1', Group('Group', MatchPoint('X'), Group('Children', MatchPoint('Y'))))),
    Rule(Sequence('s1', Group('MatchPoint', MatchPoint('X')), Group('Children', MatchPoint('Y'))), Sequence('s1', Group('Sequence', MatchPoint('X'), Group('Children', MatchPoint('Y'))))),
    Rule(Sequence('s1', Group('oper', Atom('(')), Group('ident', MatchPoint('X')), Group('oper', Atom(')')), Group('Children', MatchPoint('Y'))), Sequence('s1', Group('Sequence', MatchPoint('X'), Group('Children', MatchPoint('Y'))))),
    Rule(Sequence('s1', Group('oper', Atom('{')), Group('ident', MatchPoint('X')), Group('oper', Atom('}')), Group('Children', MatchPoint('Y'))), Sequence('s1', Group('Set', MatchPoint('X'), Group('Children', MatchPoint('Y'))))),
    # Disjunctors and Conjunctors
    Rule(Sequence('s1', Group('oper', Atom('|')), Group('Children', MatchPoint('X'))), Sequence('s1', Group('Disjunctor', Group('Children', MatchPoint('X'))))),
    Rule(Sequence('s1', Group('oper', Atom('&')), Group('Children', MatchPoint('X'))), Sequence('s1', Group('Conjunctor', Group('Children', MatchPoint('X'))))),
    # Negations
    Rule(Sequence('s1', Group('oper', Atom('!')), Group('Atom', MatchPoint('X'))), Sequence('s1', Group('Negator', Group('Atom', MatchPoint('X'))))),
    Rule(Sequence('s1', Group('oper', Atom('!')), Group('MatchPoint', MatchPoint('X'))), Sequence('s1', Group('Negator', Group('MatchPoint', MatchPoint('X'))))),
    Rule(Sequence('s1', Group('oper', Atom('!')), Group('Group', MatchPoint('X'), MatchPoint('Y'))), Sequence('s1', Group('Negator', Group('Group', MatchPoint('X'), MatchPoint('Y'))))),
    Rule(Sequence('s1', Group('oper', Atom('!')), Group('Sequence', MatchPoint('X'), MatchPoint('Y'))), Sequence('s1', Group('Negator', Group('Sequence', MatchPoint('X'), MatchPoint('Y'))))),
    Rule(Sequence('s1', Group('oper', Atom('!')), Group('Disjunctor', MatchPoint('Y'))), Sequence('s1', Group('Negator', Group('Disjunctor', MatchPoint('Y'))))),
    Rule(Sequence('s1', Group('oper', Atom('!')), Group('Conjunctor', MatchPoint('Y'))), Sequence('s1', Group('Negator', Group('Conjunctor', MatchPoint('Y'))))),
    # Children
] + CHILD_RULES + [
    # Rules
    Rule(Sequence('s1', Group('Atom', MatchPoint('X')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Atom', MatchPoint('Y'))), Sequence('s1', Group('Rule', Group('Atom', MatchPoint('X')), Group('Atom', MatchPoint('Y'))))),
    Rule(Sequence('s1', Group('Atom', MatchPoint('X')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Group', MatchPoint('Y'), MatchPoint('Z'))), Sequence('s1', Group('Rule', Group('Atom', MatchPoint('X')), Group('Group', MatchPoint('Y'), MatchPoint('Z'))))),
    Rule(Sequence('s1', Group('Group', MatchPoint('X'), MatchPoint('Y')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Atom', MatchPoint('Z'))), Sequence('s1', Group('Rule', Group('Group', MatchPoint('X'), MatchPoint('Y')), Group('Atom', MatchPoint('Z'))))),
    Rule(Sequence('s1', Group('Group', MatchPoint('X'), MatchPoint('Y')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Group', MatchPoint('Z'), MatchPoint('W'))), Sequence('s1', Group('Rule', Group('Group', MatchPoint('X'), MatchPoint('Y')), Group('Group', MatchPoint('Z'), MatchPoint('W'))))),
    Rule(Sequence('s1', Group('Sequence', MatchPoint('X'), MatchPoint('Y')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Sequence', MatchPoint('Z'), MatchPoint('W'))), Sequence('s1', Group('Rule', Group('Sequence', MatchPoint('X'), MatchPoint('Y')), Group('Sequence', MatchPoint('Z'), MatchPoint('W'))))),
    Rule(Sequence('s1', Group('Set', MatchPoint('X'), MatchPoint('Y')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Set', MatchPoint('Z'), MatchPoint('W'))), Sequence('s1', Group('Rule', Group('Set', MatchPoint('X'), MatchPoint('Y')), Group('Set', MatchPoint('Z'), MatchPoint('W'))))),
    # Ruleset
    Rule(Sequence('s1', Group('Rule', MatchPoint('X'), MatchPoint('Y')), Group('oper', Atom(';'))), Sequence('s1', Group('RuleSet', Group('Rules', Group('Rule', MatchPoint('X'), MatchPoint('Y')))))),
    Rule(Sequence('s1', Group('RuleSet', MatchPoint('X')), Group('Rule', MatchPoint('Y'), MatchPoint('Z')), Group('oper', Atom(';'))), Sequence('s1', Group('RuleSet', Group('Rules', MatchPoint('X'), Group('Rule', MatchPoint('Y'), MatchPoint('Z')))))),
    Rule(Sequence('s1', Group('RuleSet', MatchPoint('X')), Group('RuleSet', MatchPoint('Y'))), Sequence('s1', Group('RuleSet', Group('Rules', MatchPoint('X'), MatchPoint('Y'))))),
]))

class Translator(object):
    def translate(self, obj):
        return getattr(self, 'trans_'+type(obj).__name__)(obj)

    def trans_Atom(self, obj):
        return obj.value

    def trans_Group(self, obj):
        return getattr(self, 'tg_'+obj.name)(obj)

    def tg_document(self, obj):
        return list(map(self.translate, obj.children))

    def tg_RuleSet(self, obj):
        return RuleSet(*self.translate(obj.children[0]))

    def tg_Rules(self, obj):
        res = []
        for i in map(self.translate, obj.children):
            if isinstance(i, list):
                res.extend(i)
            else:
                res.append(i)
        return res

    def tg_Rule(self, obj):
        return Rule(self.translate(obj.children[0]), self.translate(obj.children[1]))

    def tg_Children(self, obj):
        return self.translate(obj.children[0])

    def tg_Child(self, obj):
        res = []
        for i in map(self.translate, obj.children):
            if isinstance(i, list):
                res.extend(i)
            else:
                res.append(i)
        return res

    def tg_Atom(self, obj):
        return Atom(self.translate(obj.children[0]))

    def tg_MatchPoint(self, obj):
        return MatchPoint(self.translate(obj.children[0]))

    def tg_Negator(self, obj):
        return Negator(self.translate(obj.children[0]))

    def tg_Group(self, obj):
        return Group(self.translate(obj.children[0]), *self.translate(obj.children[1]))

    def tg_Sequence(self, obj):
        return Sequence(self.translate(obj.children[0]), *self.translate(obj.children[1]))

    def tg_Set(self, obj):
        return Set(self.translate(obj.children[0]), *self.translate(obj.children[1]))

    def tg_Disjunctor(self, obj):
        return Disjunctor(None, *self.translate(obj.children[0]))

    def tg_Conjunctor(self, obj):
        return Conjunctor(None, *self.translate(obj.children[0]))

if __name__ == '__main__':
    import ctok, sys, pickle
    tree = ctok.Tokenizer(sys.stdin).tokenize()
    print('Compiling...', file=sys.stderr)
    if len(sys.argv) > 1:
        print('(verbose enabled)', file=sys.stderr)
        Rule.action = lambda self, rule, match, bind, res: print('Fired:', rule, '\nMatching:', match, '\nBindings:', bind, '\nResulting in', res, '\n---\n', file=sys.stderr)
    res = RULES.run(tree)
    print('Iterations:', res[1], file=sys.stderr)
    print(res[0].pretty(), file=sys.stderr)
    tree = Translator().translate(res[0])
    print(tree, file=sys.stderr)
    sys.stdout.buffer.write(pickle.dumps(tree))
    sys.stdout.flush()
