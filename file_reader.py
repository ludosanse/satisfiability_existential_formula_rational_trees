"""
Parser.py

Turn custom format file into python classes representing the dijsuncts
Format file specs are detailed in FORMAT_SPECS.txt

go line by line, use regex to match the case to some pattern (atomicity statement, equality, etc.)

compile together into list of disjuncts.

ASSUMPTIONS:
- no negative atomicity literals like !At(x)
- all terms flat (NO NESTING)
- variables and constants start with either a letter or a number, no special characters.
- Equalities only have variables on the left hand side
- first line after declarations is '---DISJUNCT'

if any of these aren't true, code will raise an error (i'm decently certain).

Wish list:
- raise error if non variable is on left hand side of equality
- have error messages say on what line of the input file the error was encountered
"""
from models import *
import re # regex
from itertools import count # generator which increments from 0
    
def assert_valid_var_name(name):
    """checks that a variable name follows the specification"""
    if bool(re.match(r"^\w+$", name)):
        return True
    else:
        raise RuntimeError(f'Invalid variable name {name}')

def assert_valid_constructor_name(name):
    """checks that a constructor name follows the specification"""
    if bool(re.match(r"^[a-zA-Z]", name)):
        return True
    else:
        raise RuntimeError(f'Invalid constructor name {name}')

def get_var(name,var_table: dict[str, VAR]) -> VAR:
    """Given a variable name, returns an instance of VAR, and registers it in var_table"""
    if name in var_table:
        return var_table[name]
    else:
        assert_valid_var_name(name)
        new_var =  VAR(name)
        var_table[name] = new_var
        return new_var

def make_fresh_var(var_table: dict[str, VAR], fresh_counter) -> VAR:
    """creates a new variable with a distinct name"""
    name = f"$var_{next(fresh_counter)}"
    new_var =  VAR(name)
    var_table[name] = new_var
    return new_var

def update_var_table(var_table: dict[str, VAR], free_vars):
    """updates the var_table to correctly reflect whether a variable is free or existentially bound"""
    for v in free_vars:
        if v not in var_table:
            var_table[v] = VAR(name=v, is_free=True)
        else:
            var_table[v].is_free = True
    return var_table

def assert_constructor_arity(constructor_term,constructor_table):
    """
    input: a newly created constructor term
    output: bool

    A constructor must have consistent arity across all disjuncts.
    In this function, constructor names are registered in a dictionary 'constructor_table' before being passed on.
    Said table has constructor names (strings) as keys and arities (integers) as items.
    (this machinery could potentially be done at the class level, but its more trouble than it's worth)
    """
    assert_valid_constructor_name(constructor_term.constr)
    if constructor_term.constr in constructor_table:
        if len(constructor_term.var_list) != constructor_table[constructor_term.constr]:
            raise AssertionError(f"constructor {constructor_term} has inconsistent arity: both {len(constructor_term.var_list)} and {constructor_table[constructor_term.constr]} (at least)")
    else:
        constructor_table[constructor_term.constr] = len(constructor_term.var_list)


def parse_constructor_args(arg_names, constants, var_table, fresh_var_counter):
    """
    Extract variable and constants from a string h(x,y,z,...)

    input: a list of strings, each potentially a name of a variable or constant
    output: a list of VAR class instances, a list of equality literals of the type $x = a

    if a constant 'a' appears in the arguments of a constructor, 
    we can generate a new variable '$x', add '$x = a' to the disjunction, 
    and substitute '$x' in the arguments of the constructor when adding it to the disjunction.
    """
    args = []
    extra_literals = []
    for v in arg_names:
        v = v.strip()
        if v != '':
            if v in constants:
                fresh = make_fresh_var(var_table, fresh_var_counter)
                extra_literals.append(EQUALITY(fresh, CONSTANT(v)))
                args.append(fresh)
            else:
                args.append(get_var(v, var_table))
    return args, extra_literals

def parse_literal(line,constants,var_table: dict[str, VAR],fresh_var_counter,constructor_table):
    """
    Use regex to match the literal to it's type, instantiate and return the relevant class(es)
    """
    # Negated Atomicity literal (Error)
    m = re.match(r"[~¬]At\((\w+)\)", line)
    if m:
        raise ValueError(f"negated atomicity literal found: {line}. these should be dealt with before DNF conversion")

    # Atomicity literals
    m = re.match(r"At\((\w+)\)",line)
    if m:
        return ATOMICITY(get_var(m.group(1),var_table))
    
    # Rooted literal: "Rooted(<var>,<constructor>)"
    # logically speaking: R_h(x) => ∃y_1,...,∃y_{ar_h}( x = h(y_1,...,y_{ar_h}) )
    m = re.match(r"Rooted\((\w+),(\w+)\)",line)
    if m:
        constr_name = m.group(2)
        if constr_name in constructor_table:
            fresh_vars = [make_fresh_var(var_table,fresh_var_counter) for i in range(constructor_table[constr_name])]
            cons_term = CONSTRUCTOR_TERM(constr_name,fresh_vars)
            assert_constructor_arity(cons_term,constructor_table) # not actually necessary but eh
            var = get_var(m.group(1),var_table)
            return EQUALITY(var,cons_term)
        else:
            raise RuntimeError(f"cannot call 'Rooted' on constructor term that has not appeared before in the input. Use constructor declaration if necessary")
        
    # deal with var != constructor case
    m = re.match(r"(\w+)\s*!=\s*(\w+)\((.+)\)", line)
    if m:
        # logically speaking: x!= h(args) => exists fresh_var( x != fresh_var and fresh_var = h(args))
        literals = [] # literals to output
        
        # get arguments for constructor, accounting for possible constants in the arguments
        arg_names = m.group(3).replace(' ',',').split(',')
        args, extra_literals = parse_constructor_args(arg_names,constants,var_table,fresh_var_counter)

        # create $fresh = h(args), x != $fresh literals
        fresh_var = make_fresh_var(var_table,fresh_var_counter) # create fresh variable
        constructor_term = CONSTRUCTOR_TERM(m.group(2), args)
        assert_constructor_arity(constructor_term,constructor_table)
        
        constructor_literal = EQUALITY(
            lhs=fresh_var,
            rhs= constructor_term
        )

        inequality_literal = INEQUALITY(
            lhs=get_var(m.group(1), var_table),
            rhs=fresh_var
        )
        literals.extend(extra_literals)
        literals.extend([constructor_literal,inequality_literal])
        return tuple(literals)
    
    # Inequaility literals
    m = re.match(r"(\w+)\s*!=\s*(\w+)",line)
    if m:
        lhs = get_var(m.group(1),var_table)
        rhs = m.group(2)
        if rhs in constants:
            term = CONSTANT(name = rhs)
            fresh_var = make_fresh_var(var_table,fresh_var_counter)

            xNeqFresh_literal = INEQUALITY(
                lhs = lhs,
                rhs = fresh_var
                )
            FreshEqA_literal = EQUALITY(
                lhs= fresh_var,
                rhs = term,
            )
            return xNeqFresh_literal, FreshEqA_literal
        return INEQUALITY(lhs = lhs, rhs = get_var(rhs,var_table))

    # Equality literals
    m = re.match(r"(\w+)\s*=\s*(.+)",line)
    if m:
        rhs = m.group(2)
        literals = [] # literals to output

        # check if rhs is constuctor term
        m2 = re.match(r"(\w+)\s*\((.+)\)",rhs)
        if m2:
            # get arguments for constructor, accounting for possible constants in the arguments
            arg_names = m2.group(2).replace(' ',',').split(',')
            args,extra_literals = parse_constructor_args(arg_names,constants,var_table,fresh_var_counter)
            term = CONSTRUCTOR_TERM(
                constr = m2.group(1),
                var_list=args
            )
            assert_constructor_arity(term,constructor_table)
            literals.extend(extra_literals)
        # check if rhs a constant
        elif rhs in constants:
            term = CONSTANT(name = rhs)
        # otherwise rhs a variable
        else:
            term = get_var(rhs,var_table)

        literals.append(EQUALITY(
            lhs = get_var(m.group(1),var_table),
            rhs = term
        ))
        return tuple(literals)
    
    # no literals matched, confused, raise error
    raise RuntimeError(f"literal {line} doesn't match any literal type")
    

def parse_file(inputFile_name):
    """
    loop through each newline in the file, forming literals which are added to DISJUNCT

    input: file name in the form of a string
    output: a list of DISJUNCT instances
    """
    current_disjunct = None
    all_disjuncts = []
    free_vars = set()
    var_table: dict[str, VAR] = {}
    constructor_table = {}
    fresh_var_counter = count() # generator which increments from 0
    constants = set()
    with open(inputFile_name) as f:
        while True:
            
            line = f.readline()

            if line == "": # end of file
                if current_disjunct: # if the current disjunct isn't empty
                    all_disjuncts.append(current_disjunct)
                break

            line = line.strip() # removes leading/trailing whitespace and newline tokens '\n'

            if line == "" or line.startswith('%'): # blank line or comment
                continue
            
            if line.startswith('free'): # declaration of free variables
                vars = line.replace(',',' ').split(' ')
                for i in range(len(vars)):
                    if vars[i] in ['\n','free','']:
                        continue
                    if assert_valid_var_name(vars[i]):
                        free_vars.add(vars[i])
                continue

            if line.startswith('constants'): # declaration of constants
                cons = line.replace(',',' ').split(' ')
                for i in range(len(cons)):
                    if cons[i] in ['\n','constants','']:
                        continue
                    if assert_valid_var_name(cons[i]):
                        constants.add(cons[i])
                continue

            if line.startswith('constructors'): # declaration of constructors
                constrs = line.replace(',',' ').split(' ')
                for i in range(len(constrs)):
                    if constrs[i] in ['\n','constructors','']:
                        continue
                    constr_name,arity = constrs[i].split('/')
                    # register constructor to constructor table (this very much a bodge)
                    assert_constructor_arity(CONSTRUCTOR_TERM(constr_name,list(range(int(arity)))),constructor_table) 
                continue
                    
            if line == "--- DISJUNCT": # declaring new disjunct
                if current_disjunct: # if the current disjunct isn't empty
                    all_disjuncts.append(current_disjunct)
                current_disjunct = DISJUNCT()
                continue
            
            if current_disjunct is None:
                raise RuntimeError('no disjunct declared')
            
            # it is none of the above, so it must be some kind of literal
            result = parse_literal(line,constants,var_table,fresh_var_counter,constructor_table)

            # there are cases in which we add more than one literal per line, which come in the form of a tuple
            if type(result) == tuple:
                for r in result:
                    current_disjunct.literals.append(r)
            else:
                current_disjunct.literals.append(result)

    var_table = update_var_table(var_table,free_vars)

    return all_disjuncts, var_table, constructor_table


if __name__ == '__main__':
    disjuncts, var_table, constructor_table = parse_file("test_rooted.txt")
    for dis in disjuncts:
        print("\n--DISJUNCT")
        print(dis)
    print(var_table)