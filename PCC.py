import z3
from models import *
from dataclasses import is_dataclass, fields
from itertools import count # generator which increments from 0

def runPCC(disjunct,var_table,constructor_table,debug):
    """
    Use the equalities in the disjunct to construct the congruence closure literals
    based on the canonical R-assignment.

    For each inequality in the disjunct, add its negation to the congruence closure clause, and check sat.
    (so if the inequality is x!=y, add x=y)

    If all such congruence closures are UNSAT, the disjunct is SAT.
    """
    # seperate inequalities from other literals in the disjunct
    inequalities = []
    non_inequalities = []
    for lit in disjunct.literals:
        if isinstance(lit,INEQUALITY):
            inequalities.append(lit)
            continue
        non_inequalities.append(lit)

    # use equalities to build the "canonical R-assignment" congruence closure literals
    solver,var = setupCC(inequalities,non_inequalities,var_table,constructor_table,debug)

    # loop over each inequality in the disjunct
    for ineq in inequalities:
        solver.push() # save state of solver before adding temporary constraints

        # add the negated inequality
        solver.add(var[ineq.lhs.name] == var[ineq.rhs.name])
        
        result = solver.check()

        if debug: 
            print('PCC on input',ineq)
            print('Congruence closure literals:')
            print(solver)
            print('Congruence closure is',result)
        
        solver.pop() # restore solver to original state
        
        if result == z3.sat:
            # the dijsunct is satisfiable even with the inequality negated, thus the disjunct is UNSAT
            if debug: print("Disjunct is unsatisfiable")
            return "UNSAT"
        
    if debug: 
        if not inequalities: # if the for loop was skipped because there are no inequalities
            print('No inequalities in Disjunct')
        print("Disjunct is satisfiable")
    return "SAT"

def get_terms(obj) -> tuple[set[str],set[str],set[str]]: 
    """ 
    Recursive function to get all variables, constants and constructors inside of a disjunct
    """
    if isinstance(obj, VAR):
        return set([obj.name]), set(), set()
    
    elif isinstance(obj, CONSTANT):
        return set(), set([obj.name]), set()
    
    elif isinstance(obj, CONSTRUCTOR_TERM):
        v, c, cr = get_terms(obj.var_list)
        return v, c, cr | set([obj.constr])
    
    elif isinstance(obj, list):
        var_set, const_set, constr_set = set(), set(), set()
        for item in obj:
            v, c, cr = get_terms(item)
            var_set |= v
            const_set |= c
            constr_set |= cr
        return var_set, const_set, constr_set
    
    elif is_dataclass(obj): # this nicely catches EQUALITY, INEQUALITY and ATOMICITY
        return get_terms([getattr(obj, f.name) for f in fields(obj)])
    
    else:
        raise RuntimeError(f"unexpected object in get_terms: {obj}")

def make_fresh_constant(constants, P, sort, fresh_counter):
    # creates a new constant and its related predicate
    name = f"$fresh_constant_{next(fresh_counter)}"
    constants.add(name)
    P[name] = z3.Function(f"P_{name}",sort,z3.BoolSort())
    return name

def setupCC(inequalities,non_inequalities,var_table,constructor_table:dict[str,int],debug):
    # construct the signature on which we base the congruence closure
    solver = z3.Solver()
    sort = z3.DeclareSort('S') 

    # compile list of variables, constructors and constants
    v,c,cr = get_terms(inequalities)
    variables,constants,constructors = get_terms(non_inequalities)
    variables|=v
    constants|=c
    constructors|=cr

    # create signature constants, predicates and functions and mappings from names to z3 instances

    # a variable is treated as a constant inside the signature
    var = {} # variable name -> z3 constant
    for v in variables:
        var[v] = z3.Const(v,sort)
    
    P = {} # constructor or constant name -> z3 predicate
    # add a predicate for each constructor and constant in the disjunct
    # a predicate in z3 is a function that maps any constant to either true of false
    for c in constructors:
        P[c] = z3.Function(f"P_{c}",sort,z3.BoolSort()) 
    for c in constants:
        P[c] = z3.Function(f"P_{c}",sort,z3.BoolSort())

    # Functions that indicate where in the arguments another term appears: F[2](x) = y => x = h(*, *, y, ...)
    F = []
    if constructors: # verify that there are constructors in the disjunct
        biggest_arity = max([constructor_table[c] for c in constructors])
        for i in range(1,biggest_arity+1):
            F.append(z3.Function(f"F_{i}",sort,sort))


    # deal with external variables:
    # first, find non external variables
    non_external = set()
    for lit in non_inequalities: 
        if isinstance(lit,EQUALITY): 
            non_external.add(lit.lhs.name)
    # variables - non_external = external_variables (recall these are sets)
    external = variables - non_external 
    if debug: print("external variables --",list(external))
    # create fresh constants for each external variable
    counter = count()
    external_constants = [make_fresh_constant(constants,P,sort,counter) for _ in external]
    # create predicate terms for external variables
    for i,v in enumerate(external):
        constant = external_constants[i]
        for c in P:
            if c != constant:
                solver.add(z3.Not(P[c](var[v])))
            else:
                solver.add(P[constant](var[v]))

    # go through disjunct, generate congruence closure literals
    for lit in non_inequalities:
        if isinstance(lit,EQUALITY):
            head = lit.lhs.name
            if isinstance(lit.rhs,CONSTANT):
                # predicate terms
                constant = lit.rhs
                for c in P:
                    if c != constant:
                        solver.add(z3.Not(P[c](var[head])))
                    else:
                        solver.add(P[constant](var[head]))
            elif isinstance(lit.rhs,CONSTRUCTOR_TERM):
                # predicate terms
                constr = lit.rhs.constr
                for c in P:
                    if c != constr:
                        solver.add(z3.Not(P[c](var[head])))
                    else:
                        solver.add(P[constr](var[head]))
                # equality terms
                var_list = lit.rhs.var_list
                for i,v in enumerate(var_list):
                    solver.add(F[i](var[head]) == var[v.name])
    
    return solver,var
    

if __name__ == '__main__':
    pass