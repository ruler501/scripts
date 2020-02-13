#!/usr/bin/env python3

import sys
from collections import defaultdict
from prettytable import PrettyTable

def main(args=None):
    if args == None:
        args = sys.argv
    args = args[1:]
    n = len(args) 
    r = defaultdict(lambda : [""]*n)
    for i,name in enumerate(args):
        with open(name) as f:
            for line in f:
                r[line][i] = "X"
    t = PrettyTable(["Spell", *args])
    t.padding_width = 1
    t.padding_height = 0
    for k,v in sorted(r.items()):
        t.add_row([k,*v])
    print(t)

if __name__ == "__main__":
    main()
