from file_reader import parse_file
from rewrite_rules import apply_rewrite_rules
from PCC import runPCC
import argparse


def main(args):
    # read and parse file
    disjuncts, var_table, constructor_table = parse_file(args.input_file)
    # apply rewrite rules
    disjuncts,ediagrams = apply_rewrite_rules(disjuncts,var_table,args.debug)

    sat_flag = False
    if disjuncts: # if disjuncts is not empty
        # apply sat checker on each disjunct
        for disjunct in disjuncts:

            if args.debug:
                print("\n---DISJUNCT")
                print(disjunct)
                print()
            
            result = runPCC(disjunct,var_table,constructor_table,args.debug)

            #print(result)
            if result == "SAT":
                sat_flag = True
    else:
        if args.debug:
            print('all disjuncts were found to be unsat before PCC was run')

    if sat_flag:
        print('SAT')
    else:
        print('UNSAT')

if __name__ == '__main__':
    # command line machinery
    parser = argparse.ArgumentParser(
        description='Decision procedure for rational tree constraints'
    )
    parser.add_argument('input_file', nargs='?', default='test_rooted.txt', 
                        help='path to the input file')
    
    parser.add_argument('--debug', action='store_true', help='print debug information')

    args = parser.parse_args()

    main(args)
    
