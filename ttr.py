# TT translator for rulesets in the simple syntax

from rws import *

# Rule.action = lambda self, rule, match, bind, res: print('Fired', rule, 'matching', match, 'bindings', bind, 'resulting in', res)

ELEMS = {'Atom': 1, 'MatchPoint': 1, 'Group': 2, 'Sequence': 2}
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
    # Children
] + CHILD_RULES + [
    # Rules
    Rule(Sequence('s1', Group('Atom', MatchPoint('X')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Atom', MatchPoint('Y'))), Sequence('s1', Group('Rule', Group('Atom', MatchPoint('X')), Group('Atom', MatchPoint('Y'))))),
    Rule(Sequence('s1', Group('Atom', MatchPoint('X')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Group', MatchPoint('Y'), MatchPoint('Z'))), Sequence('s1', Group('Rule', Group('Atom', MatchPoint('X')), Group('Group', MatchPoint('Y'), MatchPoint('Z'))))),
    Rule(Sequence('s1', Group('Group', MatchPoint('X'), MatchPoint('Y')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Atom', MatchPoint('Z'))), Sequence('s1', Group('Rule', Group('Group', MatchPoint('X'), MatchPoint('Y')), Group('Atom', MatchPoint('Z'))))),
    Rule(Sequence('s1', Group('Group', MatchPoint('X'), MatchPoint('Y')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Group', MatchPoint('Z'), MatchPoint('W'))), Sequence('s1', Group('Rule', Group('Group', MatchPoint('X'), MatchPoint('Y')), Group('Group', MatchPoint('Z'), MatchPoint('W'))))),
    Rule(Sequence('s1', Group('Sequence', MatchPoint('X'), MatchPoint('Y')), Group('oper', Atom('-')), Group('oper', Atom('>')), Group('Sequence', MatchPoint('Z'), MatchPoint('W'))), Sequence('s1', Group('Rule', Group('Sequence', MatchPoint('X'), MatchPoint('Y')), Group('Sequence', MatchPoint('Z'), MatchPoint('W'))))),
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

    def tg_Group(self, obj):
        return Group(self.translate(obj.children[0]), *self.translate(obj.children[1]))

    def tg_Sequence(self, obj):
        return Sequence(self.translate(obj.children[0]), *self.translate(obj.children[1]))

if __name__ == '__main__':
    import ctok, sys
    tree = ctok.Tokenizer(sys.stdin).tokenize()
    print(tree.pretty())
    res = RULES.run(tree)
    print('Iterations:', res[1])
    print(res[0].pretty())
    print(Translator().translate(res[0]))
