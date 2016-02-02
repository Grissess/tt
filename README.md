# tt -- a Tree Transformer

`tt` is a loosely-coupled set of libraries to perform tree rewriting. In
particular, it implements *subtree isomoprhism* with rewrite rules (in
`rws.py`), has a very C-like tokenizer (`ctok.py`) that generates (depth-2)
*document trees*, and has a compiler for the *TTR syntax* (as defined in
`ttr.py`) implemented in itself (`ttr.tt`).

## Usage

### As a library

`tt` is fairly straightforward to use to directly; simply `import rws`, build a
tree and some rules, then run the rules on the tree. The primitives for doing
so are as follows:

* *Trees* are composed of anything inheriting `Expression`. *Ordinary trees*
  are composed solely of `Expression`s direct, concrete descendants, namely
  `Atom` and `Group`. Atoms form the leaves of the tree, while Groups form the
  non-leaves. Each node is *labelled*; Atoms receive a value as their only
  argument, while Groups receive a name as their first argument (and their
  children thereafter).
* *Rules* are composed of *pattern trees*, which may include descendants of
  `RuleEx`.  In addition to Groups and Atoms, which represent themselves,
  pattern trees may also contain `MatchPoint` and `Sequence`, which behave
  analogously to an Atom and a Group respectively. A MatchPoint *binds* any
  node (Group or Atom) that it would be compared against to match, whereas a
  Sequence binds a subsequence of a Group. The `Negator` and `Disjunctor` are
  also components of pattern trees, and behave as a logical negation or
  disjunction, respectively.
* *Rule sets* (class `RuleSet`) represent sequences of Rules. This entity is
  responible for *running* Rules on a tree--that is, matching every Rule until
  quiescence.

Some of the `RuleEx` derivatives have special ("binding") behavior when
evaluated as part of a pattern tree against some subtree of the input tree:

* When matching, a MatchPoint uniquely identified by its (Atomic) value will
  receive (*bind*) the first node it matches, and match unconditionally.
  Subsequent occurrences of the same MatchPoint (by value) will only match if
  the node it is to match is considered equivalent to its first binding. A
  Sequence is located where a Group would be in an input tree, and matches some
  consecutive subsequence of that Group, binding the location and length of the
  match. Interactions between matching Sequences of the same name is
  ill-defined at the moment.
* When rewriting, a MatchPoint will evaluate to whatever value it was bound to.
  A Sequence will *splice* its children into the match of the original
  Sequence--that is, the bound location and length of the sequence will be
  replaced with the content of the rewriting sequence, which need not be the
  same length. Sequences may be rewritten to a Group other than the one
  matched, which causes the splice to occur in the same location in that Group
  as it would in the matched Group.

The exact behavior is determined by placement in a Rule: the left-hand side
(first parameter) of a Rule is matched; its right-hand side (second parameter)
is rewritten using the bindings generated by the match. Currently, logical
operators do not have well-formed replacements when rewriting.

### TTR syntax

For complicated translations, it helps to have a domain-specific language to
describe the trees, rules, and other entities. For this reason, `ttr.py` was
written, which defines a language similar to a context-free grammar from a
tokenized input file, and returns some set of objects in `rws`. First, `ctok`
is invoked on the input file:

* C-style comments (slash-star) and whitespace are removed.
* All punctuation is converted to a Group with name 'oper' and a single Atom
  containing the punctuation.
* Strings with interpreted escape sequences (as in C), bounded with either
  double or single quotes, are converted to a Group of 'string' with a single
  Atom containing the (interpreted) string.
* C-style identifiers are converted to a Group 'ident' with an analogous single
  Atom.
* Positive decimal integers are converted to an analogous Group 'num'.

All of these Groups are placed under a single Group 'document', and returned.

The translation rules in `ttr` (both versions) implement the following CFG:

* Strings are mapped to Atoms with the given value.
* Identifiers in angle brackets (e.g., `<x>`) map to MatchPoints.
* Identifiers or Atoms (strings) followed by a comma-separated list of elements
  in brackets form Groups, named by the identifier or string.
* MatchPoints followed by a comma-separated list of elements in brackets form
  Sequences, named for the MatchPoint's identifier.
* Identifiers in parentheses `()` preceding a comma-separated list in brackets
  also form sequences, and prevent ambiguity inside such lists.
* An exclamation mark `!` preceding an element gives a Negation of that
  element.
* A vertical bar `|` preceding a comma-separated list in brackets gives a
  Disjunctor over that set of elements.
* An Element is any aforementioned Atom, Group, MatchPoint, Sequence, Negator,
  or Disjunctor.
* An arrow `->` between two (compatible) Elements creates a Rule. Compatible
  elements include:
  * An Atom or Group to an Atom or Group.
  * A Sequence to a Sequence.
* A Rule followed by a semicolon `;` creates a RuleSet with that Rule.
  Adjacent RuleSets are joined in proper sequence.

Examples of this syntax are given in the `*.tt` files in this directory, and
also some other files that are dependent on them.

These definitions are defined in a simpler syntax in ttr.tt. Bear in mind that
all Rules in a RuleSet are executed in sequence.

### Executing TTR

To execute TTR on a tree, use the `ttexec.py` helper, which:

1. Compiles the TTR syntax file given on the command line.
2. Preprocess stdin, through at least `ctok` and optionally also `ttr`.
3. Executes the syntax file's RuleSet over the stdin ordinary tree.
4. Writes the resulting tree to stdout (in TTR format).

## Theory

TT was designed to be a small language that is simultaneously:

* Capable of being Turing-complete, or, equivalently, representing the Type-0
  (recursively enumerable) languages in the Chomsky hierarchy.
* Thereby capable of simply describing itself.
* Fairly easy to understand and use for practical purposes (id est, not
  Brainfuck).

While polynomial-time algorithms trivially exist for subtree isomorphism with
ordered children exist, this currently uses a slow method that could stand to
be improved.

### Bootstrapping and Quines

The demonstration that TT is capable of compiling itself is possible to execute
directly from the current state of the repository. However, since TT's
computational model does not readily admit the convenient metaphors of IO that
most modern machines implement, some conversion steps are required.
Furthermore, due to the general inefficiency of the algorithm at present, this
process takes me a couple minutes, and presumably can take even longer on slow
hardware. Nonetheless, it is possible, and can be demonstrated as follows.

The bootstrapping grammar is written in TT, executed in Python's RWS (arguably
a virtual machine). A necessary preprocessing step to convert text to ordinary
trees is done via `ctok`. After the grammar runs, a *TT tree* is generated,
which is an *ordinary* tree that *represents* the structure of an arbitrary
(possibly pattern) tree. Translating from a TT tree to a plain tree is done by
the `ttr.Translator`, which is invoked on option from `ttexec`.

The self-encoded grammar is in `ttr.tt`. To execute it using the `ttexec`
helper, use it as such:

	$ python3 ttexec.py ttr.tt -u < ttr.tt > ttr2.tt

This will generate the Stage 2 compiler `ttr2.tt`, which can be tested for
correspondence with `ttr.tt`; however, it's easier to verify it against a Stage
3 build. First, however, because a document can consist of an arbitrary list of
RuleSets, Rules, and trees, you must remove the leading and trailing brackets
`[]` from ttr2.tt; then:

	$ python3 ttexec.py ttr2.tt -u < ttr2.tt > ttr3.tt

If all went well (and after removing the leading and trailing brackets from
`ttr3.tt`), there should be no difference between `ttr2.tt` and `ttr3.tt`:

	$ diff ttr2.tt ttr3.tt && echo success
	success

### Proof of Turing Completeness

TT is Turing Complete; in fact, it can completely emulate a Turing machine. The
program `turma.tt` is a Turing Machine executor, that expects a tree describing
a machine description consisting of:

* A group named TuringMachine, with the exact children:
  * Group State, with a single Atom child, representing the state.
  * Group Tape, bounded on the left with 'LMARK', on the right with 'RMARK',
	and with empty cells denoted 'EMPTY', along with any other ordinary
	Elements representing tape symbols, with exactly one child (not 'LMARK' or
	'RMARK') being the only child of a group Head.
  * Group Transitions, with an arbitrary number of Transition groups, each
	consisting of the ordered children:
	* The Atom in the current State.
	* The symbol in the current Head.
	* An atom 'LEFT' or 'RIGHT' representing the direction of move to take.
	* A symbol to replace the current Head's position with.
	* An Atom to make the new State.

An example of such a file is given in `streq.tm`, a Turing Machine which
determines if two bitstrings (separated by a 'SEP') are equal. In the current
implementation, it passes to the 'ACCEPT' state in 66 iterations. Executing the
machine is done as follows:

	$ python3 ttexec.py turma.tt -t < streq.tm

The additional -t option indicates that the input file is to be interpreted as
a TT file, not an arbitrary file to be tokenized. Using the above grammar for
TT files, it's possible to construct ordinary trees for such input by avoiding
use of the symbols `->` and `;`.
