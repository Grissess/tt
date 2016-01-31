# C-like tokenizer

from rws import Atom, Group

class Tokenizer(object):
    EOF = object()
    def __init__(self, fp):
        self.fp = fp
        self.pushback = None

    def getc(self, need = False):
        if self.pushback:
            res = self.pushback
            self.pushback = None
        else:
            res = self.fp.read(1)
        if not res:
            if need:
                raise ValueError('Unexpected EOF')
            return self.EOF
        return res

    WS = ' \t\r\n\v'
    PUNCT = '`~!@#$%^&*()+-=[]\\{}|;:,./<>?'
    STR_GRP = '"' + "'"
    ESCAPE = '\\'
    ESCAPES = {'n': '\n', 't': '\t', 'v': '\v', 'r': '\r', 'a': '\a', '"': '"', "'": "'"}
    ESC_HEX = 'x'
    ESC_OCT = '0'
    OCT_DIGIT = '01234567'
    DIGIT = OCT_DIGIT + '89'
    HEX_DIGIT = DIGIT + 'abcdefABCDEF'
    IDENT_START = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
    IDENT = IDENT_START + DIGIT
    def nexttok(self):
        c = self.getc()
        if c is self.EOF:
            return self.EOF
        while c in self.WS:
            c = self.getc()
            if c is self.EOF:
                return self.EOF
        if c in self.STR_GRP:
            s = ''
            init = c
            while True:
                c = self.getc()
                if c == self.EOF:
                    raise ValueError('Unexpected EOF in string')
                if c == init:
                    return Group('string', Atom(s))
                if c == self.ESCAPE:
                    ty = self.getc(True)
                    if ty == self.ESC_HEX:
                        hval = ''
                        while True:
                            hc = self.getc(True)
                            if hc not in self.HEX_DIGIT:
                                break
                            hval += hc
                        if not hval:
                            raise ValueError('Bad hex constant: %r'%(hval,))
                        s += chr(int(hval, 16))
                        continue
                    if ty == self.ESC_OCT:
                        oval = ''
                        while True:
                            oc = self.getc(True)
                            if oc not in self.OCT_DIGIT:
                                break
                            oval += oc
                        if not oval:
                            raise ValueError('Bad oct constant: %r'%(oval,))
                        s += chr(int(oval, 8))
                        continue
                    s += self.ESCAPES.get(ty, ty)
                    continue
                s += c
        if c in self.PUNCT:
            if c == '/':
                n = self.getc()
                if n == '*':
                    while True:
                        c = self.getc()
                        if c is self.EOF:
                            return self.EOF
                        if c == '*':
                            n = self.getc()
                            if n == '/':
                                return self.nexttok()
                            elif n is self.EOF:
                                return self.EOF
                elif n is self.EOF:
                    return Group('oper', Atom(c))
            return Group('oper', Atom(c))
        if c in self.DIGIT:
            num = c
            while True:
                c = self.getc()
                if c is self.EOF:
                    return Group('num', Atom(num))
                if c not in self.DIGIT:
                    self.pushback = c
                    return Group('num', Atom(num))
                num += c
        if c in self.IDENT_START:
            ident = c
            while True:
                c = self.getc()
                if c is self.EOF:
                    return Group('ident', Atom(ident))
                if c not in self.IDENT:
                    self.pushback = c
                    return Group('ident', Atom(ident))
                ident += c
        raise NotImplementedError('Not sure what to do with %r'%(c,))

    def tokenize(self):
        doc = Group('document')
        while True:
            tok = self.nexttok()
            if tok is self.EOF:
                break
            doc.children.append(tok)
        return doc

if __name__ == '__main__':
    import sys
    print(Tokenizer(sys.stdin).tokenize())
