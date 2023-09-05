#!/usr/bin/env python3

import os
import sys
import re
import time
import shutil
import platform
import argparse
import tempfile
from datetime import datetime

# ---------- Determine if Linux or Windows -----------
ForwardSlash = '/'      # Linux eg. /path/file..
BackSlash = (chr(92))   # Windows eg. \path\file..
SlashList = [ForwardSlash, BackSlash]
Sys = platform.system()
if Sys == 'Linux':       # Currently "/" is set for both systems
    Slash = ForwardSlash
if Sys == 'Windows':
    Slash = ForwardSlash

# ---------- Terminal Coloring -----------
TRED = '\033[31m'
TWHITE = '\033[37m'
TGREEN = '\033[32m'
TORANGE = '\033[33m'

# ---------- User Input -----------
def user_input():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-s", "--search", dest='str_search', help="Enter string to search")
    argParser.add_argument("-i", "--input", dest='input_deck', help="Enter input deck to scan")
    argParser.add_argument("-c", "--compare", dest='compare_deck', help="Enter input deck to compare")
    args = argParser.parse_args()
    if args:
        inp = args.input_deck
        inp1 = args.input_deck
        inp2 = args.compare_deck
        input_raw = args.input_deck

    else:
        print("")
        print("Enter an input deck to scan")
        sys.exit()
        
    if args.str_search:
        print('Searching for the term '+'\033[1m'+args.str_search+'\033[0m'+' in '+args.input_deck)
    elif args.compare_deck:
        inp2tuple = inp2, inp2
        inp2tuple_list = [inp2tuple]
        inp2short = shortname(inp2tuple_list)
#        print(inp2short)
        print('Comparing Includes in '+'\033[1m'+inp+'\033[0m and '+'\033[1m'+inp2short[0][0]+'\033[0m')
    elif args.input_deck:
        print('Scanning Includes in '+'\033[1m'+inp+'\033[0m')
    inp1tuple = inp1, inp1
    inp1tuple_list = [inp1tuple]
    inp1short = shortname(inp1tuple_list)
    inp1s = inp1short[0][0]
    father_file = os.path.abspath(inp)
    father_file_path = os.path.dirname(os.path.abspath(inp))
    inp_and_father = inp1s, father_file                               # inp and inp itself with full path as his own father in order for the search function to work
    return inp_and_father, args

# ---------- Define include search function -----------
def scan_for_includes(inp_and_father, Includes_not_exist, Includes_cannot_read):   # inp_and_father is a tuple of file and its father file
    BadChars = ['$']
    PlusEnd = ' +\n'
    SpacePlus = ' +'
    InpNoDollar = []
    include_list = []
    ForwardSlash = '/'      # Linux eg. /path/file..
    BackSlash = (chr(92))   # Windows eg. \path\file..
    SlashList = [ForwardSlash, BackSlash]
    Slash = ForwardSlash

    inp = inp_and_father[0]
    father_file = inp_and_father[1]
    father_file_path = os.path.dirname(inp_and_father[1])

    if not any(char in inp for char in SlashList):
        inp = father_file_path+Slash+inp

    inp_path = os.path.dirname(inp)

    try:
        with open(inp, 'r', encoding='utf-8', errors='ignore') as InpFile:   # Search for files that LS-Dyna will read
            for i, line in enumerate(InpFile):
                include_as_list = []
                clean_include_as_list = []
                if line.startswith('*INCLUDE'):
                    NextLine = next(InpFile)
                    NextLine = NextLine.strip()
                    NextLine = NextLine+'\n'
#                    [x.strip() for x in row]
                    include_as_list.append(NextLine)
                    while NextLine.endswith(PlusEnd) or NextLine.startswith('$'):
                        NextLine = next(InpFile)
                        NextLine = NextLine.strip()
                        NextLine = NextLine+'\n'
                        include_as_list.append(NextLine)

                    for item in include_as_list:
                        if not item.startswith('$'):
                            if item.endswith(PlusEnd):
                                item = re.sub(' \+\n', '', item)
                            else:
                                item = re.sub('\n', '', item)
                            clean_include_as_list.append(item)
                    clean_include = ''.join(clean_include_as_list)

                    if not any(char in clean_include for char in SlashList):
                        clean_include = inp_path + Slash + clean_include
                    include_and_father_file = clean_include, inp
                    include_list.append(include_and_father_file)                    

    except OSError as x:
        if x.errno == 2:
            Includes_not_exist.append(tuple((inp, father_file)))
            print(inp, TRED +'does not exist'+ TWHITE +' referenced in: '+father_file)
        elif x.errno == 13:
            Includes_cannot_read.append(tuple((inp, father_file)))
            print(inp, TORANGE +'cannot be read'+ TWHITE +' referenced in: '+father_file)
        else:
            print(inp, '- some other error')

    return include_list, Includes_not_exist, Includes_cannot_read

# ---------- Define recursive function -----------
def recur(include_list, Includes_not_exist, Includes_cannot_read, include_list_total):
    subinclude_list = []
    subinclude_list_all = []
    print('Scanning '+str(len(include_list))+' nested files...')
    for inp in include_list: 
        subinclude_list, Includes_not_exist, Includes_cannot_read = scan_for_includes(inp, Includes_not_exist, Includes_cannot_read)
        subinclude_list_all.extend(subinclude_list)
        include_list_total.extend(subinclude_list)
    if len(subinclude_list_all) == 0:
        print('Scanning complete')
        include_list_total.sort(key=lambda x: x[0])
        return Includes_not_exist, Includes_cannot_read, include_list_total
    else:
        return recur(subinclude_list_all, Includes_not_exist, Includes_cannot_read, include_list_total)

# ---------- Define short include name function -----------
def shortname(include_list):                                 # list of tuples
    include_list_short= []
    for x in include_list:
        inc_as_list = x[0].split("/")
        inc_short = inc_as_list.pop()
        father_as_list = x[1].split("/")
        father_short = father_as_list.pop()
        include_and_father_file_short = inc_short, father_short
        include_list_short.append(include_and_father_file_short)
    return include_list_short

# ---------- Get file timestamp -----------
def get_timestamp(inc):
    try:
        IncTimeStamp = os.path.getmtime(inc) + 3600
        IncDate = datetime.utcfromtimestamp(IncTimeStamp).strftime('%Y-%m-%d %H:%M')
        return IncDate
    except OSError as e:
        if e.errno == 2:
            IncDate = 'file does not exist'
        elif e.errno == 13:
            IncDate = 'file cannot be read'
        else:
            IncDate = 'file error'
        return IncDate
        
# ---------- List missing includes -----------
def list_missing_files(Includes_not_exist, Includes_cannot_read):
    nr_notfound = str(len(Includes_not_exist))
    nr_unreadable = str(len(Includes_cannot_read))
    nr_bad_includes = str(len(Includes_not_exist) + len(Includes_cannot_read))

    if len(Includes_not_exist) > 0:
        print(TRED +'Warning: '+nr_notfound+' referenced Includes does not exist: '+TWHITE)
#        print(*Includes_not_exist, sep = '\n')
        [print('Include: '+f'{x[0]:<40}'+' referenced in: '+x[1]) for x in Includes_not_exist]
        print("")

    if len(Includes_cannot_read) > 0:
        print(TORANGE +'Warning: '+ nr_unreadable+' referenced Includes have no read permission: '+TWHITE)
        [print('Include: '+f'{x[0]:<40}'+' referenced in: '+x[1]) for x in Includes_cannot_read]
#        print(*Includes_cannot_read, sep = '\n')
        print("")

    if (len(Includes_not_exist) + len(Includes_cannot_read)) == 0:
        print(TGREEN +'All includes accesible! '+TWHITE)
        print('')

    elif (len(Includes_not_exist) + len(Includes_cannot_read)) > 0:
        if len(Includes_not_exist) > 0:
            print(TRED +'Warning: '+nr_notfound+' referenced Includes does not exist'+TWHITE)
        if len(Includes_cannot_read) > 0:
            print(TORANGE +'Warning: '+ nr_unreadable+' referenced Includes have no read permission'+TWHITE)

# ---------- Copy Includes to folder given by user -----------
def copy_files(include_list):
    answer = input("Copy includes to a folder? [y/n]: ")
    if answer.lower() in ["y","yes"]:
        targetdir = input("Enter path: ")
        for include in include_list:
            shutil.copy(include[0], targetdir)
#        shutil.copy(input_raw, targetdir)
        print("")
    #    print("Includes copied to ", targetdir)
        print(TGREEN + "Includes copied to "+targetdir + TWHITE)

        setrights = 'chmod 777 '+targetdir+'/*'
        setrightsdir = 'chmod 777 '+targetdir
        os.system(setrights)
        os.system(setrightsdir)
        print("")
    #    print("Rights set to 777")
        print(TGREEN + "Rights set to 777" + TWHITE)

    elif answer.lower() in ["n","no"]:
         sys.exit()
    else:
         sys.exit()

# ---------- Create Include Dictionary -----------    
def get_dict_parent_children(ListOfTuples):
    IncDict = {}
    Parents = list(set([x[1] for x in ListOfTuples]))
    for p in Parents:
        ChildList = []
        for y in ListOfTuples:
            if p == y[1]:
                ChildList.append(y[0])
        IncDict[p] = ChildList
    return IncDict
  
# ---------- Print tree structure ----------- 
def print_tree(root, IncDict, tree_list, level=0):
    rootDate = get_timestamp(root)
    SpaceLength = 150 - 3*level - len(root)
    print("   "*level, root, " "*SpaceLength, rootDate)
    subs = IncDict[root]
    subs.sort(key=lambda x: x[0])
    trunk = '   ' * level
    trunk = trunk+root
    tree_list.append(trunk)
    for s in subs:
        if s in IncDict:
            print_tree(s, IncDict, tree_list, level + 1)
        else:
            sDate = get_timestamp(s)
            lvl = level + 1
            SpaceLength = 150 - 3*lvl - len(s)
            branch = '   ' * lvl
            branch = branch+s
            tree_list.append(branch)
            print("   "*lvl, s, " "*SpaceLength, sDate)
    return tree_list

# ---------- Print tree structure into list----------- 
def print_tree_to_list(root, IncDict, tree_list, level=0):
    rootDate = get_timestamp(root)
    SpaceLength = 150 - 3*level - len(root)
#    print(IncDict)
    subs = IncDict[root]
    subs.sort(key=lambda x: x[0])
    if level > 0:
        trunk1 = ' +- '
    else:
        trunk1 = ''
    trunk2 = ' |  ' * (level-1)
    trunk = trunk2+trunk1+root
    tree_list.append(trunk)
    for s in subs:
        if s in IncDict:
            print_tree_to_list(s, IncDict, tree_list, level + 1)
        else:
            sDate = get_timestamp(s)
            lvl = level + 1
            SpaceLength = 150 - 3*lvl - len(s)
            branch1 = ' +- '
            branch2 = ' |  ' * (lvl - 1)
            branch = branch2+branch1+s
            tree_list.append(branch)
#            print("   "*lvl, s, " "*SpaceLength, sDate)
    return tree_list
 
# ---------- User input how to visualize the tree structure with loop-----------        
def user_choose_long_or_short_tree_loop(inp, include_list_total, include_list_total_short):
    if len(include_list_total) < 1:
        print('\nNo nested files found')
        quit()
        
    print('')
    ans = input("Display tree structure long or short? [l/s]: ")
    print('')
    tree_list = []
    if ans == 'l':
        IncDict = get_dict_parent_children(include_list_total)
        root = inp[1]
#        print('\n')
        print_tree(root, IncDict, tree_list, level=0)
        user_choose_long_or_short_tree_loop(inp, include_list_total, include_list_total_short)
    elif ans == 's':
        IncDict = get_dict_parent_children(include_list_total_short)
        inpl = [inp]
        inpls = shortname(inpl)
        root = inpls[0][0]
#        print('\n')
        print_tree(root, IncDict, tree_list, level=0)
        user_choose_long_or_short_tree_loop(inp, include_list_total, include_list_total_short)
    else:
        pass
    return tree_list
# ---------- User input how to visualize the tree structure -----------
def user_choose_long_or_short_tree(inp, include_list_total, include_list_total_short, ans):
    if len(include_list_total) < 1:
        print('\nNo nested files found')
        quit()
    tree_list = []
    if ans == 'l':
        IncDict = get_dict_parent_children(include_list_total)
        root = inp[1]
        tree_list = print_tree_to_list(root, IncDict, tree_list, level=0)
    elif ans == 's':
        IncDict = get_dict_parent_children(include_list_total_short)
        inpl = [inp]
        inpls = shortname(inpl)
        root = inpls[0][0]
        tree_list = print_tree_to_list(root, IncDict, tree_list, level=0) 
    else:
        print('specify [l/s] for long or shor tree structure')
    return tree_list
# ---------- Search for a string in Includes -----------
def string_search(args, include_list_total):
    if args.str_search:
        str2search = args.str_search
        simple_include_list_raw = []
        for item in include_list_total:
            simple_include_list_raw.append(item[0])
            simple_include_list_raw.append(item[1])
        simple_include_list = list(set(simple_include_list_raw))
        for item in simple_include_list:
            command = 'grep --color --with-filename '+str2search+' '+item
            os.system(command)
        return simple_include_list
    else:
        pass
# ---------- End script function under certain conditions -----------
def end_script(args):
    if args.str_search:
        sys.exit()

# ---------- Main single file -----------
def main_single(inp, args, ans):
#    inp, args = user_input()
    t = time.time()
    include_list = [inp]
    Includes_not_exist, Includes_cannot_read, include_list_total = recur(include_list, Includes_not_exist = [], Includes_cannot_read = [], include_list_total = [])  
    include_list_total.sort(key=lambda x: x[0])
#    simple_include_list = string_search(args, include_list_total)
#    end_script(args)
#    print('Final list:')
    include_list_total_short = shortname(include_list_total)
#    [print('Include: '+f'{x[0]:<60}'+' referenced in: '+x[1]) for x in include_list_total]
    elapsed = time.time() - t
    elapsed = round(elapsed, 2)
    print("\nDone. Time elapsed: " + str(elapsed) + " seconds")
    print("")

    list_missing_files(Includes_not_exist, Includes_cannot_read)
    tree_list = user_choose_long_or_short_tree(inp, include_list_total, include_list_total_short, ans)
    if not args.compare_deck:
        print(*tree_list, sep = '\n')
    '''
    if not args.compare_deck:
        copy_files(include_list_total)
    '''
    return tree_list
    
# ---------- Main compare 2 files-----------
def main_compare(inp, args):
    print('')
    ans = input("Display tree structure long or short? [l/s]: ")
    print('')
    td = tempfile.TemporaryDirectory()
    td_path = td.name
    inp_1_and_father = inp
    inp_2 = args.compare_deck
    inp2tuple = inp_2, inp_2
    inp2tuple_list = [inp2tuple]
    inp2short = shortname(inp2tuple_list)
    inp_2s = inp2short[0][0]
    inp_2_father_file = os.path.abspath(inp_2)
    inp_2_and_father = inp_2s, inp_2_father_file
    list_1 = [inp_1_and_father]
    list_2 = [inp_2_and_father]
    title_1 = shortname(list_1)
    title_2 = shortname(list_2)
    t_1 = title_1[0][0]
    t_2 = title_2[0][0]
#    print(inp_1_and_father)
#    print(inp_2_and_father)
    tree_list_1 = main_single(inp_1_and_father, args, ans)
    tree_list_2 = main_single(inp_2_and_father, args, ans)

    with open(os.path.join(td_path, t_1), "w") as file1:
        for item in tree_list_1:
            file1.write(f"{item}\n")
    with open(os.path.join(td_path, t_2), "w") as file2:
        for item in tree_list_2:
            file2.write(f"{item}\n")
    command = 'xxdiff '+td_path+'/'+t_1+' '+td_path+'/'+t_2
    print(command)
    os.system(command) 
    
# ---------- Main search for a string -----------
def main_search(inp, args):
    t = time.time()
    include_list = [inp]
    Includes_not_exist, Includes_cannot_read, include_list_total = recur(include_list, Includes_not_exist = [], Includes_cannot_read = [], include_list_total = [])  
    include_list_total.sort(key=lambda x: x[0])
    simple_include_list = string_search(args, include_list_total)
    elapsed = time.time() - t
    elapsed = round(elapsed, 2)
    print("\nDone. Time elapsed: " + str(elapsed) + " seconds")
    print("")

# ---------- Main -----------
def main():
    inp, args = user_input()
    if args.str_search:
        main_search(inp, args)
    elif args.compare_deck:
        main_compare(inp, args)
    elif args.input_deck:
        print('')
        ans = input("Display tree structure long or short? [l/s]: ")
        print('')
        main_single(inp, args, ans)
    else:
        print("enter arguments (-i, -s, -c)")

# ---------- Run -----------
if __name__ == "__main__":
    main()
