#!/usr/bin/env python3

import os
import sys
import re
import time
import shutil
import platform

# ---------- Determine if Linux or Windows -----------
ForwardSlash = '/'  # Linux eg. /path/file..
BackSlash = (chr(92))  # Windows eg. \path\file..
SlashList = [ForwardSlash, BackSlash]
Sys = platform.system()
if Sys == 'Linux':  # Currently "/" is set for both systems
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
        input_raw = inp
    else:
        print("")
        print("Enter an input deck to scan")
        sys.exit()

    print('Scanning Includes in ' + inp)
    father_file = os.path.abspath(inp)
    #    print('input: '+father_file)
    father_file_path = os.path.dirname(os.path.abspath(inp))
    #    print('input: '+father_file_path)
    inp_and_father = inp, father_file  # inp and inp itself with full path as his own father so the search function works
    #    print(f'input: %s' % (inp_and_father,))
    return inp_and_father


# ---------- Define search function -----------
# def scan_for_includes(inp, father_file_path, Includes_not_exist, Includes_cannot_read):
def scan_for_includes(inp_and_father, Includes_not_exist,
                      Includes_cannot_read):  # inp is a tuple of file and its father file
    BadChars = ['$']
    PlusEnd = ' +\n'
    InpNoDollar = []
    include_list = []
    ForwardSlash = '/'  # Linux eg. /path/file..
    BackSlash = (chr(92))  # Windows eg. \path\file..
    SlashList = [ForwardSlash, BackSlash]
    Slash = ForwardSlash

    inp = inp_and_father[0]
    inp_path = os.path.dirname(inp[0])
    father_file = inp_and_father[1]
    father_file_path = os.path.dirname(inp_and_father[1])

    #   print('read input: '+inp)
    #   print('read father file: '+father_file)
    #   print('read father file path: '+father_file_path)

    if not any(char in inp for char in SlashList):
        inp = father_file_path + Slash + inp
    #        print('read input after modif: '+inp)

    try:
        with open(inp, 'r', encoding='utf-8', errors='ignore') as file:  # remove LS-Dyna comments
            for line in file:
                if not any(bad_char in line for bad_char in BadChars):
                    line = line.rstrip()
                    line = line + '\n'
                    InpNoDollar.append(line)

        for i, line in enumerate(InpNoDollar):
            include_as_list = []
            clean_include_as_list = []

            if line.startswith('*INCLUDE'):  # identify LS-Dyna keyword line under which file is referenced
                j = i + 1
                include_as_list.append(InpNoDollar[j])
                while InpNoDollar[j].endswith(PlusEnd):  # concatenates lines ending with the ' +' linebreak
                    j += 1
                    include_as_list.append(InpNoDollar[j])

                for item in include_as_list:
                    if item.endswith(PlusEnd):
                        item = re.sub(' \+\n', '', item)
                    else:
                        item = re.sub('\n', '', item)
                    clean_include_as_list.append(item)
                clean_include = ''.join(clean_include_as_list)

                if not any(char in inp for char in SlashList):
                    clean_include = father_file_path + Slash + clean_include
                include_and_father_file = clean_include, inp
                include_list.append(include_and_father_file)

    except OSError as x:
        if x.errno == 2:
            Includes_not_exist.append(tuple((inp, father_file)))
            print(inp, TRED + 'does not exist' + TWHITE + ' referenced in: ' + father_file)
        elif x.errno == 13:
            Includes_cannot_read.append(tuple((inp, father_file)))
            print(inp, TORANGE + 'cannot be read' + TWHITE + ' referenced in: ' + father_file)
        else:
            print(inp, '- some other error')

    return include_list, Includes_not_exist, Includes_cannot_read


# ---------- Define recursive function -----------
def recur(include_list, Includes_not_exist, Includes_cannot_read, include_list_total):
    #    include_list_total.extend(include_list)
    subinclude_list = []
    subinclude_list_all = []
    print('Scanning ' + str(len(include_list)) + ' nested files...')
    for inp in include_list:
        subinclude_list, Includes_not_exist, Includes_cannot_read = scan_for_includes(inp, Includes_not_exist,
                                                                                      Includes_cannot_read)
        subinclude_list_all.extend(subinclude_list)
        include_list_total.extend(subinclude_list)
    #        if subinclude_list != []:
    #            print(*subinclude_list, sep='\n')
    if len(subinclude_list_all) == 0:
        print('Search finished')
        return include_list_total
    #        return include_list_total, subinclude_list_all, Includes_not_exist, Includes_cannot_read
    else:
        #        print(TRED+'we need to go deeper'+TWHITE)
        return recur(subinclude_list_all, Includes_not_exist, Includes_cannot_read, include_list_total)


# ---------- Define short include name funtion -----------
def shortname(include_list):  # list of tuples
    include_list_short = []
    for x in include_list:
        inc_as_list = x[0].split("/")
        father_as_list = x[1].split("/")
        inc_short = inc_as_list.pop()
        father_short = father_as_list.pop()
        include_and_father_file_short = inc_short, father_short
        include_list_short.append(include_and_father_file_short)
    return include_list_short

# ---------- List missing includes -----------
def list_missing_files(Includes_not_exist, Includes_cannot_read):
    nr_notfound = str(len(Includes_not_exist))
    nr_unreadable = str(len(Includes_cannot_read))
    nr_bad_includes = str(len(Includes_not_exist) + len(Includes_cannot_read))

    if len(Includes_not_exist) > 0:
        print(TRED + 'Warning: ' + nr_notfound + ' referenced Includes does not exist: ' + TWHITE)
        #        print(*Includes_not_exist, sep = '\n')
        [print('Include: ' + f'{x[0]:<40}' + ' referenced in: ' + x[1]) for x in Includes_not_exist]
        print("")

    if len(Includes_cannot_read) > 0:
        print(TORANGE + 'Warning: ' + nr_unreadable + ' referenced Includes have no read permission: ' + TWHITE)
        [print('Include: ' + f'{x[0]:<40}' + ' referenced in: ' + x[1]) for x in Includes_cannot_read]
        #        print(*Includes_cannot_read, sep = '\n')
        print("")

    if (len(Includes_not_exist) + len(Includes_cannot_read)) == 0:
        print(TGREEN + 'All includes accesible! ' + TWHITE)

    elif (len(Includes_not_exist) + len(Includes_cannot_read)) > 0:
        if len(Includes_not_exist) > 0:
            print(TRED + 'Warning: ' + nr_notfound + ' referenced Includes does not exist' + TWHITE)
        if len(Includes_cannot_read) > 0:
            print(TORANGE + 'Warning: ' + nr_unreadable + ' referenced Includes have no read permission' + TWHITE)


# ---------- Copy Includes to folder given by user -----------
def copy_files(include_list):
    answer = input("Copy includes to a folder? [y/n]: ")
    if answer.lower() in ["y", "yes"]:
        targetdir = input("Enter path: ")
        for include in include_list:
            shutil.copy(include[0], targetdir)
        #        shutil.copy(input_raw, targetdir)
        print("")
        #    print("Includes copied to ", targetdir)
        print(TGREEN + "Includes copied to " + targetdir + TWHITE)

        setrights = 'chmod 777 ' + targetdir + '/*'
        setrightsdir = 'chmod 777 ' + targetdir
        os.system(setrights)
        os.system(setrightsdir)
        print("")
        #    print("Rights set to 777")
        print(TGREEN + "Rights set to 777" + TWHITE)

    elif answer.lower() in ["n", "no"]:
        sys.exit()
    else:
        sys.exit()


# ---------- Run -----------
if __name__ == "__main__":
    t = time.time()
    inp = user_input()
    include_list = [inp]
    include_list_total = []
    Includes_cannot_read = []
    Includes_not_exist = []
    include_list_total = recur(include_list, Includes_not_exist, Includes_cannot_read, include_list_total)

    # ---------- Terminal output: print the found nested files -----------
    print('Final list:')
    include_list_total_short = shortname(include_list_total)
    #    print(*shortname(include_list_total), sep = '\n')
    [print('Include: ' + f'{x[0]:<60}' + ' referenced in: ' + x[1]) for x in include_list_total_short]
    elapsed = time.time() - t
    elapsed = round(elapsed, 2)
    print("\nDone. Time elapsed: " + str(elapsed) + " seconds")
    print("")

    # ---------- List missing files -----------
    list_missing_files(Includes_not_exist, Includes_cannot_read)

    # ---------- Copy the files (optional) -----------
    copy_files(include_list_total)


