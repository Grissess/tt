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

class MatchPoint(RuleEx, Atom):
    def __repr__(self):
        return '<%s>'%(self.value,)

class Negator(RuleEx, Atom):
    def __repr__(self):
        return '!%r'%(self.value,)

class Disjunctor(RuleEx, Group):
    def __repr__(self):
        return '|%r'%(self.children,)

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
        if isinstance(rulenode, MatchPoint):
            if rulenode.value in bindings:
                verbose('IN MP: Verifying', exnode, 'against binding', bindings[rulenode.value])
                return self._match_inner(exnode, bindings[rulenode.value], bindings)
            verbose('IN MP: Binding', rulenode.value, 'to', exnode)
            bindings[rulenode.value] = exnode
            return True, bindings
        if isinstance(rulenode, Negator):
            res, subbind = self._match_inner(exnode, rulenode.value, bindings)
            return not res, bindings
        if isinstance(rulenode, Sequence):
            if (not isinstance(exnode, Group)) or len(rulenode.children) > len(exnode.children):
                return False, bindings
            old_bindings = bindings.copy()
            for exstart in range(len(exnode.children) - len(rulenode.children) + 1):
                bindings = old_bindings.copy()
                verbose('IN SEQ: Match', rulenode, 'against', exnode.children[exstart:exstart+len(rulenode.children)])
                for idx, child in enumerate(rulenode.children):
                    res, subbind = self._match_inner(exnode.children[exstart + idx], child, bindings)
                    if not res:
                        verbose('IN SEQ: No match')
                        break
                else:
                    bindings[rulenode.name] = (exstart, len(rulenode.children))
                    return True, bindings
            return False, bindings
        if isinstance(rulenode, Disjunctor):
            old_bindings = bindings.copy()
            for subrule in rulenode.children:
                res, subbind = self._match_inner(exnode, subrule, bindings)
                if res:
                    bindings.update(subbind)
                    return True, bindings
            return False, bindings
        if isinstance(rulenode, Group):
            if (not isinstance(exnode, Group)) or exnode.name != rulenode.name or len(exnode.children) != len(rulenode.children):
                return False, bindings
            for idx, child in enumerate(rulenode.children):
                res, subbind = self._match_inner(exnode.children[idx], child, bindings)
                if not res:
                    return False, bindings
                bindings.update(subbind)
            return True, bindings
        if isinstance(rulenode, Atom):
            if (not isinstance(exnode, Atom)) or exnode.value != rulenode.value:
                return False, bindings
            return True, bindings
        raise NotImplementedError('Cannot match %r %r on %r'%(type(rulenode), rulenode, exnode))

    def evaluate(self, tree, bindings):
        return self._eval_inner(tree, bindings, self.rhs)

    def _eval_inner(self, exnode, bindings, rulenode):
        if isinstance(rulenode, MatchPoint):
            return bindings[rulenode.value]
        if isinstance(rulenode, Sequence):
            if not isinstance(exnode, Group):
                raise TypeError("Can't extrapolate Seq %r to non-group %r"%(rulenode, exnode))
            start, length = bindings[rulenode.name]
            res = Group(exnode.name, *exnode.children)
            exchildren = exnode.children[start:start + len(rulenode.children)]
            exchildren.extend([None] * (len(rulenode.children) - len(exchildren)))
            res.children[start:start + length] = flatten([self._eval_inner(exchild, bindings, rulechild) for exchild, rulechild in zip(exchildren, rulenode.children)])
            return res
        if isinstance(rulenode, Group):
            if isinstance(exnode, Group):
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
        return '%s%r'%(type(self).__name__, self.rules)

    def pass_pre(self, tree):
        for rule in self.rules:
            result = rule.execute(tree)
            if result:
                verbose('Fired', rule, 'on', tree, 'giving', result)
                if isinstance(result, Sequence) and isinstance(tree, Group):
                    verbose('IN SEQ: Splicing', result.children, 'into', tree.children, 'at index', result.name)
                    tree.children[result.name[0]:result.name[0]+result.name[1]] = result.children
                    return tree
                return result
        if isinstance(tree, Group):
            for idx, child in enumerate(tree.children):
                result = self.pass_pre(child)
                if result:
                    tree.children[idx] = result
                    return tree
        return None

    def pass_post(self, tree):
        if isinstance(tree, Group):
            for idx, child in enumerate(tree.children):
                result = self.pass_pre(child)
                if result:
                    tree.children[idx] = result
                    return tree
        for rule in self.rules:
            result = rule.execute(tree)
            if result:
                verbose('Fired', rule, 'on', tree, 'giving', result)
                if isinstance(result, Sequence) and isinstance(tree, Group):
                    verbose('IN SEQ: Splicing', result.children, 'into', tree.children, 'at index', result.name)
                    tree.children[result.name[0]:result.name[0]+result.name[1]] = result.children
                    return tree
                return result
        return None

    def run(self, tree):
        iters = 0
        while True:
            verbose('Iter', iters, ':', tree)
            newtree = self.mode(tree)
            if not newtree:
                return tree, iters
            tree = newtree
            iters += 1

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
