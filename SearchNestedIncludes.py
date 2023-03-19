#!/usr/bin/env python3

import os
import sys
import re
import time
import shutil
import platform

# ---------- Determine Linux or Windows -----------
ForwardSlash = '/'      # Linux eg. /path/file..
BackSlash = (chr(92))   # Windows eg. \path\file..
SlashList = [ForwardSlash, BackSlash]
Sys = platform.system()
if Sys == 'Linux': # Sets the Slash variable according to OS
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
    if sys.argv[1:]:
        inp = sys.argv[1]
        input_itself = inp
    else:
        print("")
        print("Enter an input deck to scan")
        sys.exit()

    print('Scanning Includes in '+inp)
    father_file_path = os.path.dirname(os.path.abspath(inp))
    print(father_file_path)
    return inp, father_file_path, input_itself

# ---------- Define search function -----------
def scan_for_includes(inp, father_file_path):
    BadChars = ['$']
    InpNoDollar = []
    Includes = []
    PlusOrInclude = ['+', 'INCLUDE']
    PlusEnd = ' +\n'
    IncWithPlus = []
    list_of_lists = []
    include_as_list = []
    clean_include_as_list = []
    include_list = []
#    father_file_path = os.getcwd()

    pwd = os.getcwd()
    if not any(char in inp for char in SlashList):
        inp = father_file_path+Slash+inp

    inp_path = os.path.dirname(inp)
    father_file_path = inp_path

    with open(inp, 'r', encoding='utf-8', errors='ignore') as file:   # remove LS-Dyna comments
        for line in file:
            if not any(bad_char in line for bad_char in BadChars):
                InpNoDollar.append(line)

    for i, line in enumerate(InpNoDollar):
        include_as_list = []
        clean_include_as_list = []

        if line.startswith('*INCLUDE'):
            j = i+1
            include_as_list.append(InpNoDollar[j])
            while InpNoDollar[j].endswith(PlusEnd):
                j += 1
                include_as_list.append(InpNoDollar[j])

            for item in include_as_list:
                if item.endswith(PlusEnd):
                    item = re.sub(' \+\n', '', item)
                else:
                    item = re.sub('\n', '', item)
                clean_include_as_list.append(item)
            clean_include = ''.join(clean_include_as_list)

#            if Slash not in clean_include:
#                clean_include = father_file_path+Slash+clean_include
            if not any(char in inp for char in SlashList):
                clean_include = father_file_path + Slash + clean_include

            include_list.append(clean_include)

    return include_list, father_file_path

# ---------- Copy Includes to folder given by user -----------
def copy_files(include_list):
    answer = input("Copy includes to a folder? [y/n]: ")
    if answer.lower() in ["y","yes"]:
        targetdir = input("Enter path: ")
        for include in include_list:
            shutil.copy(include, targetdir)
        shutil.copy(input_itself, targetdir)
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

# ---------- Run the search -----------
if __name__ == "__main__":
    t = time.time()
#    inp, father_file_path, input_itself = user_input()
    inp = r'E:\Jan\Software\Scripts\fea\Test_Folder\Run001\input.inp.txt'
    input_itself = inp
    #print(inp)
    father_file_path = os.path.dirname(os.path.abspath(inp))
    print(father_file_path)

    #inp, father_file_path, input_itself = user_input()
    include_list, father_file_path = scan_for_includes(inp, father_file_path)
    include_list.sort()
    #for item in include_list:
    #    item = os.path.abspath(item)
    #    print(item)

    #print(*include_list, sep = '\n')

    [x.encode('utf-8') for x in include_list]
    [os.path.abspath(x) for x in include_list]
#    print(*include_list, sep='\n')
#    print(father_file_path)

    subincludes = []
    i = 1

    SearchToDo = True
    while SearchToDo:
        list_length_start = len(include_list)
    #    print(list_length_start)
        for item in include_list:
            subincludes, father_file_path = scan_for_includes(item, father_file_path)
            include_list.extend(subincludes)
            include_list = list(filter(None, include_list))
    #        print(include_list)
            list_length_end = len(include_list)

        include_list = list(set(include_list))
        list_length_end = len(include_list)
        length_diff = list_length_end - list_length_start
        diff = str(length_diff)
        ii = str(i)
    #    print(list_length_end)
        i = i+1
        print(diff+' more includes found in sublevel '+ii)
        if length_diff == 0:
            SearchToDo = False
            break

    #lprint('----------------------------')

    include_list = list(set(include_list))
    include_list.sort()

    print(*include_list, sep = '\n')

    elapsed = time.time() - t
    elapsed = round(elapsed, 2)
    print("\nDone. Time elapsed: " + str(elapsed) + " seconds")
    print("")

    copy_files(include_list)


