# rws -- Simple Rewrite System

import re

def flatten(it):
    res = []
    for item in it:
        try:
            gen = iter(item)
        except TypeError:
            res.append(item)
        else:
            gen.extend(flatten(item))
    return res

DEBUG=False

def verbose(*args):
    if DEBUG:
        print(*args)

IDENT = re.compile('[a-zA-Z_][a-zA-Z0-9_]*')

class Expression(object):
    pass

class Atom(Expression):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return repr(self.value)

    def pretty(self, level = 0):
        return '  '*level + repr(self)

class Group(Expression):
    def __init__(self, name, *children):
        self.name = name
        self.children = list(children)

    def __repr__(self):
        return ('%s%r' if IDENT.match(self.name) else '%r%r')%(self.name, self.children)

    def pretty(self, level = 0):
        return '\n'.join(['  '*level + repr(self.name) + ':'] + [i.pretty(level + 1) for i in self.children])

class RuleEx(Expression):
    pass

class Sequence(RuleEx, Group):
    def __repr__(self):
        return '(%s)%r'%(self.name, self.children)

    def pretty(self, level = 0):
        return '\n'.join(['  '*level + '(%s):'%(self.name,)] + [i.pretty(level + 1) for i in self.children])

class Set(RuleEx, Group):
    def __repr__(self):
        return '{%s}%r'%(self.name, self.children)

    def pretty(self, level = 0):
        return '\n'.join(['  '*level + '{%s}:'%(self.name,)] + [i.pretty(level + 1) for i in self.children])

class MatchPoint(RuleEx, Atom):
    def __repr__(self):
        return '<%s>'%(self.value,)

class Negator(RuleEx, Atom):
    def __repr__(self):
        return '!%r'%(self.value,)

class Disjunctor(RuleEx, Group):
    def __repr__(self):
        return '|%r'%(self.children,)

class Conjunctor(RuleEx, Group):
    def __repr__(self):
        return '&%r'%(self.children,)

class Rule(object):
    action = None
    def __init__(self, lhs, rhs, action = None):
        self.lhs = lhs
        self.rhs = rhs
        if action is not None:
            self.action = action

    def __repr__(self):
        return repr(self.lhs) + ' -> ' + repr(self.rhs)

    def match(self, ex):
        return self._match_inner(ex, self.lhs, {})

    def _match_inner(self, exnode, rulenode, bindings):
        if rulenode.__class__ is Atom:
            if (exnode.__class__ is not Atom) or exnode.value != rulenode.value:
                return False, bindings
            return True, bindings
        if rulenode.__class__ is Group:
            if (exnode.__class__ is not Group) or exnode.name != rulenode.name or len(exnode.children) != len(rulenode.children):
                return False, bindings
            for idx, child in enumerate(rulenode.children):
                res, subbind = self._match_inner(exnode.children[idx], child, bindings)
                if not res:
                    return False, bindings
                bindings.update(subbind)
            return True, bindings
        if rulenode.__class__ is Sequence:
            if (exnode.__class__ is not Group) or len(rulenode.children) > len(exnode.children):
                return False, bindings
            old_bindings = bindings.copy()
            limit = len(exnode.children) - len(rulenode.children) + 1
            for exstart in range(limit):
                bindings = old_bindings.copy()
                for idx, child in enumerate(rulenode.children):
                    res, subbind = self._match_inner(exnode.children[exstart + idx], child, bindings)
                    if not res:
                        break
                else:
                    bindings[rulenode.name] = (exstart, len(rulenode.children))
                    return True, bindings
            return False, bindings
        if rulenode.__class__ is Set:
            if exnode.__class__ is not Group:
                return False, bindings
            old_bindings = bindings.copy()
            mpoint = []
            for child in rulenode.children:
                if child.__class__ is Negator:
                    for exchild in exnode.children:
                        res, subbind = self._match_inner(exchild, child.value, bindings)
                        if res:
                            return False, old_bindings
                        bindings = subbind
                    else:
                        mpoint.append(None)
                else:
                    for exidx, exchild in enumerate(exnode.children):
                        res, subbind = self._match_inner(exchild, child, bindings)
                        if res:
                            bindings = subbind
                            mpoint.append(exidx)
                            break
                    else:
                        return False, old_bindings
            bindings[rulenode.name] = mpoint
            return True, bindings
        if rulenode.__class__ is MatchPoint:
            if rulenode.value in bindings:
                return self._match_inner(exnode, bindings[rulenode.value], bindings)
            bindings[rulenode.value] = exnode
            return True, bindings
        if rulenode.__class__ is Negator:
            res, subbind = self._match_inner(exnode, rulenode.value, bindings)
            return not res, bindings
        if rulenode.__class__ is Disjunctor:
            old_bindings = bindings.copy()
            for subrule in rulenode.children:
                res, subbind = self._match_inner(exnode, subrule, bindings)
                if res:
                    bindings.update(subbind)
                    return True, bindings
            return False, bindings
        if rulenode.__class__ is Conjunctor:
            new_bindings = bindings.copy()
            for subrule in rulenode.children:
                res, subbind = self._match_inner(exnode, subrule, new_bindings)
                if not res:
                    return False, bindings
                new_bindings.update(subbind)
            bindings.update(new_bindings)
            return True, bindings
        raise NotImplementedError('Cannot match %r %r on %r'%(type(rulenode), rulenode, exnode))

    def evaluate(self, tree, bindings):
        return self._eval_inner(tree, bindings, self.rhs)

    def _eval_inner(self, exnode, bindings, rulenode):
        if rulenode.__class__ is MatchPoint:
            return bindings[rulenode.value]
        if rulenode.__class__ is Sequence:
            if exnode.__class__ is not Group:
                raise TypeError("Can't extrapolate Seq %r to non-group %r"%(rulenode, exnode))
            start, length = bindings[rulenode.name]
            res = Group(exnode.name, *exnode.children)
            exchildren = exnode.children[start:start + len(rulenode.children)]
            exchildren.extend([None] * (len(rulenode.children) - len(exchildren)))
            res.children[start:start + length] = flatten([self._eval_inner(exchild, bindings, rulechild) for exchild, rulechild in zip(exchildren, rulenode.children)])
            return res
        if rulenode.__class__ is Set:
            if exnode.__class__ is not Group:
                raise TypeError("Can't extrapolate Set %r to non-group %r"%(rulenode, exnode))
            mpoint = bindings[rulenode.name]
            for idx, child in enumerate(rulenode.children):
                if idx < len(mpoint) and mpoint[idx] is not None:
                    exnode.children[mpoint[idx]] = self._eval_inner(exnode.children[idx], bindings, child)
                else:
                    exnode.children.append(self._eval_inner(None, bindings, child))
            return exnode
        if rulenode.__class__ is Group:
            if exnode.__class__ is Group:
                exchildren = exnode.children[:len(rulenode.children)]
            else:
                exchildren = []
            exchildren.extend([None] * (len(rulenode.children) - len(exchildren)))
            return Group(rulenode.name, *flatten([self._eval_inner(exchild, bindings, child) for exchild, child in zip(exchildren, rulenode.children)]))
        return rulenode

    def execute(self, tree):
        success, bindings = self.match(tree)
        if not success:
            return None
        result = self.evaluate(tree, bindings)
        if self.action:
            new_result = self.action(self, tree, bindings, result)
            if new_result is not None:
                result = new_result
        return result

class RuleSet(object):
    def __init__(self, *rules):
        self.rules = rules
        self.mode = self.pass_pre

    def __repr__(self):
        if not self.rules:
            return '<empty RuleSet>'
        return '; '.join(map(repr, self.rules)) + ';'

    def pass_one(self, tree):
        for rule in self.rules:
            result = rule.execute(tree)
            if result:
                if result.__class__ is Sequence and tree.__class__ is Group:
                    tree.children[result.name[0]:result.name[0]+result.name[1]] = result.children
                    return tree, 0
                return result, 0
        return None

    def pass_pre(self, tree, level=0):
        for rule in self.rules:
            result = rule.execute(tree)
            if result:
                if result.__class__ is Sequence and tree.__class__ is Group:
                    tree.children[result.name[0]:result.name[0]+result.name[1]] = result.children
                    return tree, level
                return result, level
        if tree.__class__ is Group:
            for idx, child in enumerate(tree.children):
                result = self.pass_pre(child, level+1)
                if result:
                    tree.children[idx] = result[0]
                    return result
        return None

    def pass_post(self, tree, level=0):
        if tree.__class__ is Group:
            for idx, child in enumerate(tree.children):
                result = self.pass_pre(child, level)
                if result:
                    tree.children[idx] = result[0]
                    return result
        for rule in self.rules:
            result = rule.execute(tree)
            if result:
                if result.__class__ is Sequence and tree.__class__ is Group:
                    tree.children[result.name[0]:result.name[0]+result.name[1]] = result.children
                    return tree, level
                return result, level
        return None

    def run(self, tree):
        iters = {}
        while True:
            try:
                newtree = self.mode(tree)
            except Exception:
                import traceback, sys
                print('Error occured during processing tree:', file=sys.stderr)
                traceback.print_exc()
                print('Current input state:', tree, file=sys.stderr)
                return tree, iters
            if not newtree:
                return tree, iters
            tree = newtree[0]
            iters[newtree[1]] = iters.get(newtree[1], 0) + 1

if __name__ == '__main__':
    rules = RuleSet(
        Rule(Atom('a'), Group('g', Atom('b'), Atom('c'))),
        Rule(Group('g', MatchPoint('x'), Atom('c')), Group('g', Group('h', MatchPoint('x')), Atom('d'))),
    )
    tree = Group('q', Atom('a'), Atom('f'), Atom('a'))
    print(tree.pretty())
    print(rules.run(tree)[0].pretty())
    rules = RuleSet(
        Rule(Sequence('s1', Atom('a'), MatchPoint('x')), Sequence('s1', MatchPoint('x'), Atom('a')))
    )
    tree = Group('q', Atom('a'), Atom('b'), Atom('c'), Group('g', Atom('b'), Atom('a'), Atom('b')))
    print(tree.pretty())
    print(rules.run(tree)[0].pretty())
    rules = RuleSet(
        Rule(Sequence('s1', MatchPoint('x'), MatchPoint('x')), Sequence('s1', Atom('x'), Atom('y')))
    )
    tree = Group('q', Atom('a'), Atom('b'), Atom('c'), Atom('c'), Group('g', Atom('b'), Atom('b'), Atom('a'), Atom('b')), Group('g', Atom('b'), Atom('b'), Atom('a'), Atom('b')))
    print(tree.pretty())
    print(rules.run(tree)[0].pretty())
