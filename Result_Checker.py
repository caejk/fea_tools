#!/usr/bin/env python3

import subprocess
import sys
import os
import re
import glob
from datetime import datetime
from pwd import getpwuid
from os import stat
import time
import tempfile
import zipfile

TBLUE = '\033[94m'
TRED = '\033[31m'
TWHITE = '\033[37m'
TGREEN = '\033[32m'  # Green Text
TORANGE = '\033[33m'  # orange text

Help = """Dispose Check Help:

Parameters:

-u,     only runs by the user logged into the shell
-u=username,    only runs by specified user(s)
-ignore=string,     ignores runs containing "string"
-a4,    opens selected runs in Animator

Multiple search patterns can be specified using AND, OR logic:
Space = OR, / = AND

Example:

dispose_check.py -u -u=user1 -u=user2 v001/fh v002/fd -ignore=test -a4

Selects runs that:
 - have "v001" and "fh" or "v002" and "fd" in their name
 - are owned by users: "user1", "user2" or the user themselves
 - do not have the word "test" in the name
 - runs will be opened in animator"""

def GetCogX(run):
    command = 'grep -s -A3 "t o t a l" ' + run + '/d3hsp' + ' | grep -s "x-coordinate of mass center" | cut -d "=" -f 2'
    CogX = subprocess.check_output(command, shell=True, universal_newlines=True).strip()
    try:
        CogX = float(CogX)
        CogX = format(CogX, '.0f')
        CogX = str(CogX) + " mm"
    except:
        #        print("no COG")
        CogX = "       "
    return CogX


def GetTermStatus(run):
    command_term = 'tail ' + run + '/d3hsp 2>/dev/null | grep -s "t e r m i n a t i o n"'
    command_time = 'tail ' + run + '/d3hsp 2>/dev/null | grep -s dt | cut -d "t" -f 2 | cut -d " " -f 2'
    EndTime = ''
    try:
        Taild3hsp = subprocess.check_output(command_term, shell=True, universal_newlines=True).strip()
        if 'E r r o r' in Taild3hsp:
            TermStatus = TRED + 'Error ' + TWHITE
            try:
                EndTime = subprocess.check_output(command_time, shell=True, universal_newlines=True).strip()
                EndTime = float(EndTime)
                EndTime = format(EndTime, '.0f')
                EndTime = TRED + EndTime + " ms" + TWHITE
            except:
                EndTime = ''
        elif 'N o r m a l' in Taild3hsp:
            TermStatus = TGREEN + 'Normal' + TWHITE
            try:
                EndTime = subprocess.check_output(command_time, shell=True, universal_newlines=True).strip()
                EndTime = float(EndTime)
                EndTime = format(EndTime, '.0f')
                EndTime = TGREEN + EndTime + " ms" + TWHITE
            except:
                EndTime = ''
        else:
            TermStatus = TORANGE + 'Unknown' + TWHITE
    except:
        TermStatus = TORANGE + 'Unknown' + TWHITE

    return TermStatus, EndTime


def GetMass(run):
    command_mass_phys = 'grep -s -m 1 "physical mass" ' + run + '/all_mes | cut -d "=" -f 2'
    command_mass_lf = 'grep -s -m 1 "added lf mass" ' + run + '/all_mes | cut -d "=" -f 2'
    command_mass_add = 'grep -s -B2 -m 1 "physical mass" ' + run + '/all_mes | grep -s "added mass" | cut -d "=" -f 2'

    try:
        MassPhys = subprocess.check_output(command_mass_phys, shell=True, universal_newlines=True).strip()
        MassPhys = float(MassPhys)
    except:
        MassPhys = '   '
    try:
        MassLF = subprocess.check_output(command_mass_lf, shell=True, universal_newlines=True).strip()
        MassLF = float(MassLF)
    except:
        MassLF = '   '
        try:
            MassLF = subprocess.check_output(command_mass_add, shell=True, universal_newlines=True).strip()
            MassLF = float(MassLF)
        except:
            MassLF = '   '
    try:
        TotalMass = MassPhys + MassLF
        #        TotalMass = float(TotalMass)
        TotalMass = format(TotalMass, '.1f')
        TotalMass = str(TotalMass)
    #        print(TotalMass)
    except:
        MassPhys = ''
        MassLF = ''
        TotalMass = '      '
    return TotalMass


def GetOLC(run):
    CommandGetResultPath = ''                    # Project specific Path
    ResultPath = subprocess.check_output(CommandGetResultPath, shell=True, universal_newlines=True).strip()
    Brokerzip = ResultPath + '/broker.zip'
    with zipfile.ZipFile(Brokerzip, mode="r") as zf:
        with zf.open("custom.xml") as OlcFile:    # Project specific Path
            content = OlcFile.readlines()
            for i in range(len(content)):
                #                print(content[i])
                row = (content[i])
                row = row.decode('utf-8')
                match = re.search('id digits', row)
                if match:
                    OlcRaw = re.search('<id digits="1" format="f" type="char_value">(.+?)</id>', row)
                    OLC_str = OlcRaw.group(1)
                    OLC_value = round(float(OLC_str), 1)
                    break

    return OLC_value


def RunFilter(DirPattern, IgnorePattern):
    t1 = time.time()
    DirList = next(os.walk('.'))[1]
    #    print(str(len(DirList)), ' runs found')
    if any('/' in x for x in DirPattern):  # Create list of lists of patterns if "/" wildcard is invoked
        AndPatterns = [p.split('/') for p in DirPattern]
        #        print(AndOrPatterns)
        ListOfRunsReduced_ = []
        for AndPattern in AndPatterns:
            ListOfRunsOfCurrentAndPattern = [x for x in DirList if all(p in x for p in AndPattern)]
            ListOfRunsReduced_.extend(ListOfRunsOfCurrentAndPattern)
    else:
        ListOfRunsReduced_ = [x for x in DirList if any(p in x for p in DirPattern)]

    ListOfRunsReduced = [x for x in ListOfRunsReduced_ if not any(i in x for i in IgnorePattern)]  # 1st round of filtering according to ignore pattern
    ListOfRunsReduced.sort(key=os.path.getctime)
    print('{:3s}'.format(str(len(ListOfRunsReduced))), 'folders match pattern')
    ListOfRunsReducedByPattern = []  # In this list the subfolder containing the d3hsp will be saved
    elapsed1 = time.time() - t1
    elapsed1 = round(elapsed1, 2)
    #    print(str(elapsed1))
    for Run in ListOfRunsReduced:
        t = time.time()
        command_d3hsp_1_level = 'ls -l ' + Run + '/d3hsp 2>/dev/null | rev | cut -d " " -f 1 | rev'
        command_d3hsp_2_level = 'ls -l ' + Run + '/*/d3hsp 2>/dev/null | rev | cut -d " " -f 1 | rev'
        command_d3hsp_3_level = 'ls -l ' + Run + '/*/*/d3hsp 2>/dev/null | rev | cut -d " " -f 1 | rev'
        command_d3hsp_4_level = 'ls -l ' + Run + '/*/*/*/d3hsp 2>/dev/null | rev | cut -d " " -f 1 | rev'
        try_d3hsp_1 = subprocess.check_output(command_d3hsp_1_level, shell=True, universal_newlines=True).strip()
        match1 = try_d3hsp_1
        #        print('1: ', match1)
        if 'd3hsp' in match1:
            match = match1
        else:
            try_d3hsp_4 = subprocess.check_output(command_d3hsp_4_level, shell=True, universal_newlines=True).strip()
            match4 = try_d3hsp_4
            #            print('4: ', match4)
            if 'd3hsp' in match4:
                match = match4
            else:
                try_d3hsp_3 = subprocess.check_output(command_d3hsp_3_level, shell=True,
                                                      universal_newlines=True).strip()
                match3 = try_d3hsp_3
                #                print('3: ', match3)
                if 'd3hsp' in try_d3hsp_3:
                    match = match3
                else:
                    try_d3hsp_2 = subprocess.check_output(command_d3hsp_2_level, shell=True,
                                                          universal_newlines=True).strip()
                    match2 = try_d3hsp_2
                    #                    print('2: ', match2)
                    if 'd3hsp' in try_d3hsp_2:
                        match = match2
                    else:     # Fallback: search with glob if file lies deeper than 4 subfolders
                        filename = 'd3hsp'
                        match = glob.glob(f"{Run}/**/{filename}", recursive=True)
                        print('glob used', match)
                        print('')

        if 'd3hsp' in match:
            abs_dir = os.path.dirname(match)
            rel_dir = os.path.relpath(abs_dir, os.getcwd())
            ListOfRunsReducedByPattern.append(rel_dir)
        elapsed = time.time() - t
        elapsed = round(elapsed, 4)

    ListOfRunsReducedByPattern = list(set(ListOfRunsReducedByPattern))
    ListOfRunsReducedByPattern.sort(key=os.path.getctime)
    if len(ListOfRunsReducedByPattern) == 0:
        print('0   folders contain d3hsp')
        quit()
    else:
        print('{:3s}'.format(str(len(ListOfRunsReducedByPattern))), 'folders contain d3hsp file')
        ListOfRunsReducedByPatternAndIgnore = [x for x in ListOfRunsReducedByPattern if not any(i in x for i in IgnorePattern)] # 2nd round of filtering according to ignore pattern, this time considering subfolders
        ListOfRunsReducedByPatternAndIgnore.sort(key=os.path.getctime)
        LenBeforeIgnore = len(ListOfRunsReducedByPattern)
        LenAfterIgnore = len(ListOfRunsReducedByPatternAndIgnore)
        NrOfIgnored = LenBeforeIgnore - LenAfterIgnore
        if NrOfIgnored > 0:
            print('{:3s}'.format(str(NrOfIgnored)),
                  'folders with a subfolder containing the ignore pattern have been ignored')
        else:
            if len(ListOfRunsReducedByPatternAndIgnore) == 0:
                quit()
            else:
                pass
        return ListOfRunsReducedByPatternAndIgnore


def FilterByOwner(filter_by_owner, OwnersToConsider, ListOfRunsReducedByPattern):
    if filter_by_owner:
        ListOfRunsReducedByOwner = [r for r in ListOfRunsReducedByPattern if
                                    any(getpwuid(stat(r).st_uid).pw_name in u for u in OwnersToConsider)]
        print('{:3s}'.format(str(len(ListOfRunsReducedByOwner))), 'folders match owner')
    else:
        ListOfRunsReducedByOwner = ListOfRunsReducedByPattern
    if len(ListOfRunsReducedByOwner) == 0:
        #        print('No runs matching the owner found')
        quit()
    return ListOfRunsReducedByOwner


def analyse_user_input():
    KeyWords = ['-u', '-a4', '-u=', '-ignore=', '-h']
    filter_by_owner = False
    OwnersToConsider = []
    user_args = sys.argv
    user_args_noPyFile = user_args[1:]
    user_args_noPyFile_noKeyWords = [i for i in user_args_noPyFile if not any(k in i for k in KeyWords)]

    if any('-h' == arg for arg in user_args):
        print(Help)
        quit()
    if len(user_args_noPyFile_noKeyWords) == 0:
        DirPattern=['']
    else:
        DirPattern = user_args_noPyFile_noKeyWords
    if any('-ignore=' in arg for arg in user_args):
        IgnorePattern = [i.replace('-ignore=', '') for i in user_args if '-ignore=' in i]
    else:
        IgnorePattern = []

    if any('-a4' == arg for arg in user_args):
        open_animator = True
    else:
        open_animator = False

    if any('-u' == arg for arg in user_args):
        OwnersToConsider.append(os.getlogin())
        filter_by_owner = True

    if any('-u=' in arg for arg in user_args):
        owners = [u.replace('-u=', '') for u in user_args if '-u=' in u]
        OwnersToConsider.extend(owners)
        OwnersToConsider = list(set(OwnersToConsider))
        filter_by_owner = True
#        print('sort by another owner(s):' )
#        print(owners)
    if OwnersToConsider != []:
#        print(str(len(OwnersToConsider)), ' owner(s) will be considered:', *OwnersToConsider, sep=' ')
        print('{:3s}'.format(str(len(OwnersToConsider))), 'owner(s) will be considered:', *OwnersToConsider, sep=' ')
#    print(OwnersToConsider)
    return DirPattern, OwnersToConsider, filter_by_owner, open_animator, IgnorePattern

def MainOutput():
    t = time.time()
    MaxLenOfRunName = len((max(ListOfRunsReduced, key=len)))
    HeaderSpacer1 = ' ' * 27
    # LenOfSpacer2 = MaxLenOfRunName - 8 - len(DispDir)
    LenOfSpacer2 = MaxLenOfRunName
    HeaderSpacer2 = ' ' * LenOfSpacer2

    elapsed = time.time() - t
    elapsed = round(elapsed, 2)

    times_cog = []
    times_term = []
    times_mass = []

    print('{:8s} {:17s} {:100} {:8} {:10} {:10} {:8} {:8}'.format("Owner", "Date", "Run Name", "Mass", "COG(x)", "Termin.",
                                                              "Time", "OLC"))

    PlotList = []

    for r in ListOfRunsReduced:
        #    ListedRun = subprocess.check_output("ls -lahd "+r, shell=True)
        RunTimeStamp = os.stat(r).st_mtime + 3600
        RunDate = datetime.utcfromtimestamp(RunTimeStamp).strftime('%Y-%m-%d %H:%M')
        RunOwnerId = os.stat(r).st_uid
        RunOwner = getpwuid(os.stat(r).st_uid).pw_name[:7]

        t = time.time()
        RunCogX = None
        RunCogX = GetCogX(r)
        elapsed = time.time() - t
        elapsed = round(elapsed, 2)
        times_cog.append(elapsed)
        #    print("\n Done. Time to get COG(x): " + str(elapsed) + " seconds", end='')

        t = time.time()
        RunTermStatus = None
        EndTime = None
        RunTermStatus, EndTime = GetTermStatus(r)
        elapsed = time.time() - t
        elapsed = round(elapsed, 2)
        times_term.append(elapsed)
        #    print("\n Done. Time to get Termin.: " + str(elapsed) + " seconds", end='')

        t = time.time()
        RunMass = None
        RunMass = GetMass(r)
        elapsed = time.time() - t
        elapsed = round(elapsed, 2)
        times_mass.append(elapsed)
        #    print("\n Done. Time to get Mass: " + str(elapsed) + " seconds")

        RunName = r
        if DispDir in r:
            RunName = r.replace(DispDir, '')
            RunName = RunName.replace('/', '')
        if DispDir == r:
            RunName = r

        NameOffset = MaxLenOfRunName - len(r)
        RunName += ' ' * NameOffset

        #    try:
        EndTimeList = EndTime.split(' ')
        #    print(EndTimeList[0])
        EndTimeValueString = EndTimeList[0]
        EndTimeValueString = EndTimeValueString.strip(' ')


        if '1' in EndTimeValueString:
            try:
                OLC_value = GetOLC(r)
            except:
                OLC_value = '   '
        else:
            OLC_value = '   '

        if '/' in RunName:
            NameAsList = RunName.split("/")
            RunShortName = NameAsList[0]
        else:
            RunShortName = RunName

        print('{:8s} {:17s} {:110} {:8} {:20} {:20} {:8} {:6}'.format(RunOwner, RunDate, TBLUE + RunShortName + TWHITE,
                                                                      RunMass, TRED + RunCogX + TWHITE, RunTermStatus,
                                                                      EndTime, OLC_value))

        d3plot_path = os.path.abspath(r + '/d3plot')
        PlotList.append(d3plot_path)

# -------------------
# Script Statistics
# -------------------
    print('')
    AvgSearchTimeCog = sum(times_cog) / len(times_cog)
    AvgSearchTimeTerm = sum(times_term) / len(times_term)
    AvgSearchTimeMass = sum(times_mass) / len(times_mass)

    AvgCog = round(AvgSearchTimeCog, 2)
    AvgTerm = round(AvgSearchTimeTerm, 2)
    AvgMass = round(AvgSearchTimeMass, 2)

    total_elapsed = time.time() - tot_t
    total_elapsed = round(total_elapsed, 2)
    NoOfRuns = len(ListOfRunsReduced)
    CheckSpeed = NoOfRuns / total_elapsed
    CheckSpeed = round(CheckSpeed, 2)
    print("Total of " + str(NoOfRuns) + " runs found in: " + str(total_elapsed) + " seconds, that is: " + str(
        CheckSpeed) + " runs per second")

    if open_animator:
        td = tempfile.TemporaryDirectory()
        home_dir = os.path.expanduser('~')
        with open(os.path.join(home_dir, 'open_d3plots.ses'), "w") as file1:
            for item in PlotList:
                file1.write(
                    's[new]:rea fil "Dyna3d" ' + f"{item}" + ' GEO=0:pid:all DIS=0:all FUN=0:all:"pl. strain (Shell/Solid)" ADD=no' + '\n')

        a4_command = '/usr/local/bin/animator_a4_2.5.3 -s ' + home_dir + '/open_d3plots.ses'
        print(a4_command)
        os.system(a4_command)

# ----------------------
# Run Script
# ----------------------
if __name__ == "__main__":
    t = time.time()
    tot_t = time.time()
    DispDir = os.getcwd()
    ListOfRuns = []
    ListOfAllRuns = []
    print('')
# ----------------------
# Analyse user input
# ----------------------
    DirPattern, OwnersToConsider, filter_by_owner, open_animator, IgnorePattern = analyse_user_input()
# --------------------------
# Filter Runs by Pattern
# --------------------------
    ListOfRunsReducedByPattern = RunFilter(DirPattern, IgnorePattern)
# --------------------------
# Filter Runs by Owner
# --------------------------
    ListOfRunsReducedByOwner = FilterByOwner(filter_by_owner, OwnersToConsider, ListOfRunsReducedByPattern)
    ListOfRunsReduced = ListOfRunsReducedByOwner
# ----------------------------------------
# Terminal Output: Time to pre-filter
# ----------------------------------------
    elapsed = time.time() - t
    elapsed = round(elapsed, 2)
    print('')
    print("Time to filter: " + str(elapsed) + " seconds")
    print('')
# ------------------------
# Main Terminal Output
# ------------------------
    MainOutput()
