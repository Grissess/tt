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

Some of the `RuleEx` derivatives have special behavior when evaluated as part
of a pattern tree against some subtree of the input tree:

* MatchPoints, as identified unqiuely by their (Atomic) value, will:
	* On matching: on their first encounter, match unconditionally and *bind*
	  the value they were matched against. Subsequently, they will only match
	  if the value they are matched against is considered equivalent to their
	  initial binding.
	* On rewrite: Writes the value bound--but see AppendChildren below.
* Sequences, as identified by their (Group) name, will:
	* On matching: succeeding only against a Group, will match some consecutive
	  subsequence of that Group's children, binding the location and length of
	  the match.
	* On rewriting: *splices* its children into the Group it is rewritten
	  against, such that the matched subsequence is replaced by the Sequence's
	  children. The rewritten children need not be the same length (the
	  rewritten Group's children will lengthen or shorten accordingly), nor
	  does the rewritten Group need to be the same as the matched Group--the
	  splice occurs in the rewritten Group in the same location and with the
	  same length as it would in the matched Group.
* Sets, as identified by their name, will:
	* On matching: attempt to match each of its children with some element of
	  the Group it is matching against. The algorithm is, at worst,
	  O(permutations(n, m)), where n is the number of children of the Group and
	  m is the number of children of the Set, but the Set's children are tested
	  from left to right, so some paths may be culled early. It is recommended
	  to, if possible, move stricter criteria to the left. On its first
	  success, the Set binds a mapping (a Python dict) of children indices to
	  the corresponding indices of the matched Group where each Set child
	  matched.
	* On rewriting: The first m children (where m is the number of children of
	  the matching Set that created the binding) are rewritten against the
	  children of the rewritten Group in the same location as the corresponding
	  match. If the rewriting Set has less than m children, the remaining match
	  indices in the rewritten Group are removed. If the rewriting Set has more
	  than m children, the additional children are appended (rewritten against
	  nothing). Like Sequences, the rewritten Group need not be the matched
	  Group; the match indices are applied to the rewritten Group exactly as
	  they were recorded from the matched Group.
* Negators, allowed only in matches, invert the sense of their solitary child
  (technically an Atom value), but otherwise preserve all the side effects of
  that child's match (such as bindings).
* Conjunctors, allowed only in matches, match their children from left to
  right; as each child succeeds, its bindings are available to the next
  children. If a child fails, the match fails, and all new bindings are
  dropped, Otherwise (if all succeed), the new bindings are globally available.
* Disjunctors, allowed only in matches, match their children from left to
  right. Should a child match, the match succeeds, and the bindings from that
  match are globally available. Should no child match, the Disjunctor fails to
  match.
* NameMatch, allowed only in matches, succeeds only if it is matched against a
  Group whose name is equal to its Atomic value. Commonly conjuncted with a
  MatchPoint, a special TTR syntax exists for this purpose.
* AppendChildren, allowed only in rewrites, appends its second and subsequent
  children to its first child; if the first child is a Group, that Group's
  children are concatenated, in order, with the subsequent AppendChild's
  children. If the first child is an Atom, it is silently converted to an empty
  Group of the same name as the Atom's value. The subsequent children are
  rewritten *against nothing*, which proscribes the use of Sequences or Sets.
  As a direct subsequent child (not an ancestor nested one or more Groups
  deep), a MatchPoint is treated specially here: if it is bound against a
  Group, that Group's children are *concatenated* into the children (and the
  bound Group's name ignored). This is useful for renaming groups with
  arbitrary children--though the self-hosting TTR grammar, being older, does
  not yet take advantage of this.

The exact behavior is determined by placement in a Rule: the left-hand side
(first parameter) of a Rule is matched; its right-hand side (second parameter)
is rewritten using the bindings generated by the match. When rewriting Groups,
if rewritten against a Group, the children of the rewriting Group are rewritten
against the children of the rewritten Group in exactly the same order. If
the rewriting Group has more children than the rewritten Group, the excess
children are rewritten against nothing.

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
* An ampersand `&` preceding a comma-separated list in brackets gives a
  Conjunctor over that set of elements
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

### TT LISP

A small proof-of-concept of an evaluator is included in `ttl.py`, which reads
in TTR from stdin, and emits TTR from stdout. The incoming tree can be a
pattern tree without loss of generality, but TTL rewrites groups, which makes
usage in Rules and RuleSets dubious.

The core is the `ttl.Executor`, which rewrites a tree via its `eval` method.
When encountering a Group, its name is checked; if it begins with a prefix (as
set by the `prefix` attribute, default `_`) and the name is an attribute of the
form `eval_name` on the `Executor`, that method is called to rewrite that
Group, returning an Expression (usually either a Group or Atom).

Error checking is done within `eval`; if an error occurs, an `ERROR` group is
rewritten instead; its sole child is a Group whose name is the (non-qualified)
name of the Python Exception class, and whose children are Atoms consisting of
the string form of the Exception's arguments (`args`). Extenders of TTL may
take advantage of this to provide debugging information via these arguments. A
traceback is not yet included, in part for brevity.

This module is highly expected to mutate substantially, and so its intrinsics
aren't yet documented. Refer to `ttl.py` in the source distribution to observe
the currently-supported TTL functions. Suggestions for useful functions are
welcome via issues against this project.

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
