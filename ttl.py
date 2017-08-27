import functools, operator

from rws import *

def flatten_children(obj):
    if obj.__class__ is Group:
        ret = []
        for child in obj.children:
            new_child = flatten_children(child)
            if isinstance(new_child, list):
                ret.extend(new_child)
            else:
                ret.append(new_child)
        return ret
    return obj

def _eval_agg_gen(agg, numtype):
    def _inner(self, obj, agg=agg, numtype=numtype):
        val = agg(numtype(i.value) for i in self.children_eval(obj))
        return Atom(str(val))
    return _inner

def _product_gen(init):
    def product(seq, init=init):
        return functools.reduce(operator.__mul__, seq, init)
    return product

def _eval_bin_gen(op, numtype):
    def _inner(self, obj, op=op, numtype=numtype):
        left, right = self.children_eval(obj)
        return Atom(str(op(numtype(left.value), numtype(right.value))))
    return _inner

class Executor(object):
    prefix = '_'
    def eval(self, obj):
        if obj.__class__ is Group:
            if obj.name.startswith(self.prefix):
                try:
                    return getattr(self, 'eval_' + obj.name[len(self.prefix):], self.unknown_eval)(obj)
                except Exception as e:
                    return self.convert_exc(e)
            return Group(obj.name, *self.children_eval(obj))
        return obj

    def unknown_eval(self, obj):
        return obj

    def children_eval(self, obj):
        return map(self.eval, obj.children)

    def convert_exc(self, e):
        return Group('ERROR', Group(type(e).__name__, *(Atom(str(i)) for i in e.args)))

    def eval_concat(self, obj):
        return Atom(''.join(map(i.value for i in self.children_eval(obj))))

    def eval_join(self, obj):
        children = list(self.children_eval(obj))
        new_children = []
        for child in children[1:]:
            new_children.extend(child.children)
        return Group(children[0].value, *new_children)

    def eval_map(self, obj):
        children = list(self.children_eval(obj))
        new_children = []
        gname, func = children[:2]
        for child in children[2:]:
            new_children.append(self.eval(Group(func.name, *(func.children + [child]))))
        return Group(gname.value, *new_children)

    def eval_rep(self, obj):
        children = list(self.children_eval(obj))
        new_children = []
        gname, rname, rcnt = children[:3]
        for child in children[3:]:
            new_children.append(Group(rname.value, *([child] * int(rcnt.value))))
        return Group(gname.value, *new_children)

    def eval_first(self, obj):
        return self.eval(obj.children[0])

    def eval_butfirst(self, obj):
        gname, grp = self.children_eval(obj)
        return Group(gname.value, *grp.children[1:])

    def eval_last(self, obj):
        return self.eval(obj.children[-1])

    def eval_butlast(self, obj):
        gname, grp = self.children_eval(obj)
        return Group(gname.value, *grp.children[:-1])

    def eval_pop(self, obj):
        return self.eval(obj.children[0]).children[0]

    def eval_flatten(self, obj):
        children = list(self.children_eval(obj))
        new_children = []
        for child in children[1:]:
            new_child = flatten_children(child)
            if isinstance(new_child, list):
                new_children.extend(new_child)
            else:
                new_children.append(new_child)
        return Group(children[0].value, *new_children)

    # Arithmetic

    eval_sum = _eval_agg_gen(sum, int)
    eval_sumf = _eval_agg_gen(sum, float)
    eval_prod = _eval_agg_gen(_product_gen(1), int)
    eval_prodf = _eval_agg_gen(_product_gen(1.0), float)
    eval_diff = _eval_bin_gen(operator.__sub__, int)
    eval_difff = _eval_bin_gen(operator.__sub__, float)
    eval_quot = _eval_bin_gen(operator.__floordiv__, int)
    eval_quotf = _eval_bin_gen(operator.__truediv__, float)
    eval_mod = _eval_bin_gen(operator.__mod__, int)
    eval_modf = _eval_bin_gen(operator.__mod__, float)

    # For the LISP folk:

    eval_car = eval_first
    eval_caar = eval_pop
    eval_cdr = eval_butfirst

if __name__ == '__main__':
    import ctok, ttr, sys
    print('Compiling input...', file=sys.stderr)
    inp = ctok.Tokenizer(sys.stdin).tokenize()
    inp = ttr.RULES.run(inp)[0]
    print(inp)
    inp = ttr.Translator().translate(inp)[0]
    print('Executing on input...', file=sys.stderr)
    outp = Executor().eval(inp)
    print(outp)
    print('Done.', file=sys.stderr)
