from file_reader import parse_file
from rewrite_rules import apply_rewrite_rules
from PCC import runPCC
import argparse


def main(args):
    # read and parse file
    disjuncts, var_table, constructor_table = parse_file(args.input_file)
    if args.debugParser:
        print('disjuncts as they are read')
        print(repr(disjuncts))
        print('variables in disjuncts',var_table)
        print("constructors in disjuncts",constructor_table)
    # apply rewrite rules
    disjuncts,ediagrams = apply_rewrite_rules(disjuncts,var_table,args.debugRewrite)

    sat_flag = False
    if disjuncts: # if disjuncts is not empty
        # apply sat checker on each disjunct
        for disjunct in disjuncts:

            if args.debugPCC:
                print("\n---DISJUNCT")
                print(disjunct)
                print()
            
            result = runPCC(disjunct,var_table,constructor_table,args.debugPCC)

            #print(result)
            if result == "SAT":
                sat_flag = True
    else:
        if args.debugPCC:
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
    
    parser.add_argument('--debug', action='store_true', help='print all debug information')
    parser.add_argument('--debugPCC', action='store_true', help='print congruence closure literals')
    parser.add_argument('--debugParser', action='store_true', help='NOT IMPLEMENTED')
    parser.add_argument('--debugRewrite', action='store_true', help='print rule applications')
    
    args = parser.parse_args()

    args.debugPCC = args.debugPCC or args.debug
    args.debugParser = args.debugParser or args.debug
    args.debugRewrite = args.debugRewrite or args.debug

    main(args)
    
