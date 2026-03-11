# Rational Tree Existential Constraint Solver

A decision procedure for the satisfiability of existential formulae in the theory of rational trees, based on the theory developed in:

> Ghilardi, S. & Poidomani, L.M. — *Model Completeness for Rational Trees*, IJCAR 2024.
> Available at: [http://users.mat.unimi.it/users/ghilardi/allegati/GP_IJCAR24.pdf]

Developed as part of a Bachelor's thesis in Artificial Intelligence at Università degli Studi di Pavia, in collaboration with Università degli Studi di Milano and Università degli Studi di Milano-Bicocca.

## Overview

The program takes as input a file describing an existential formula in the theory of rational trees, already reduced to a disjunction of primitive formulae in flat, prenex form. For each disjunct it applies a series of rewrite rules to reduce the constraint to solved form, then runs a Pseudo Congruence Closure (PCC) procedure via the Z3 SMT solver to determine satisfiability. The formula is satisfiable if and only if at least one disjunct is satisfiable.

## Requirements

- Python 3.10+
- Z3 Python API

Install Z3 with:

```Bash
pip install z3-solver
```

## Installation

Clone the repository and install dependencies:
```bash
git clone https://github.com/ludosanse/satisfiability_existential_formula_rational_trees
cd satisfiability_existential_formula_rational_trees
pip install -r requirements.txt
```
## Usage
```Bash
python3 ERTFsolver.py <input_file> [--debug]
```
The `--debug` flag prints intermediate steps including processed disjuncts, and congruence closure literals.

## Assumptions

The program operates on the theory of rational trees with:
- Finitely many constructors
- Infinitely many constants
- An atomicity predicate `At`

The program assumes the input formula has been pre-processed:

- All terms are flat (no nested constructor applications).
- Negative atomicity literals have been eliminated.
- DNF conversion has been applied.
- Each disjunct is in prenex normal form.

## Input Format

The input is a plain text file. Declarations come first, then disjuncts.

**Declarations (optional)**

```constants a b c```

```free x y```

- `constants` lists all constant symbols used across all disjuncts
- `free` lists all free variables; any other variable is treated as existentially quantified
- Declarations are order-independent relative to each other, but must appear before the first disjunct
- Commas are optional in declarations

**Disjuncts**

Each disjunct is introduced by:

```
--- DISJUNCT
```

Followed by one literal per line. Supported literal forms:

| Form | Meaning |
|---|---|
| `x = h(y, z)` | equality with constructor term |
| `x = y` | equality between variables |
| `x = a` | equality with constant |
| `x != y` | disequality between variables |
| `x != a` | disequality with constant |
| `At(x)` | atomicity predicate |
| `Rooted(x,h)` | "x is rooted in h" |
| `x != h(y, z)` | disequality with constructor term |
| `x = h(a, b) with a, b constants` | constants as arguments of constructors |

the last three are internally converted to look like the other forms.

Comments begin with `%` and blank lines are ignored.

**Variable and constant names** must be made up of digits, letters and underscores. Variable names starting with `$` are reserved for internal use.

**Example input:**

```
constants a,b
free x,y,z
constructors h2/2

% Example from Ghilardi & Poidomani paper
--- DISJUNCT
x = h2(z, y)
y = h1(y)
z = h2(x, y)
x != y
x != z

--- DISJUNCT
x != a
Rooted(z,h2)
y = h(b)
y != h(x)
```

A few example files are included in the repository

## Project Structure

| File | Description |
|---|---|
| `main.py` | Entry point, argument parsing |
| `models.py` | Data classes for all formula components |
| `file_reader.py` | Input file parser |
| `rewrite_rules.py` | Rewrite rules 0–6 and main reduction loop |
| `PCC.py` | Pseudo Congruence Closure via Z3 |

## Future work

- Allow for negative atomicity literals by creating new disjunctions:
    ```
    (!At(x) AND φ) => (R_h1(x) AND φ) V (R_h2(x) AND φ) V ...
    ``` 
    with `φ` a constraint in solved form, for each constructor `hi` that appears in the disjunction.
- More verification of illogical or disallowed inputs
- Add a rule to remove equalities where multiple bound variables are equal to the same constant, and use a single representative for those in the disjunct, substituting the rest out.
- Major refactoring can be done to the classes defined in models.py, which would simplify file_reader.py and rewrite_rules.py significantly. Things such as a literal super class, dedicated methods for creating class instances, stuff like __eq__(), etc.
- Create a way to extract the satisfying model once SAT has been decided.
