# fea_tools
Useful scripts for pre- and post-processing of FEA simulations will be shared here.

SearchNestedIncludes.py
  - Large FEA projects often have simulation solver input decks referencing files which are referencing other files and so on.
  - The purpose of the script is to find all includes referenced in the input deck and subsequently all other includes which may be nested.
  - This version is made for the LS-Dyna solver which uses the keyword "\*INCLUDE" to import FEA files(includes).
  - The script is to be called with the main solver input deck as an argument.
  - The script produces terminal output with absolute paths to all found includes.
  - The user can choose whether he wishes to copy all found files to a specific directory.

Result_Checker.py
 - Script for checking LS-Dyna simulation results:
 - checks all subfolders of current working directory for results
 - search filtering through string patterns, user etc.
 - can load filtered simulations into Animator
  
Excel2Impact.py
  - This script will help you in comparing your FEA simulation with real world crash test.
  - The impact points from a real world crash test are usually documented in an Excel.
  - This script produces Animator session file that will create impact points from the coordinates saved in the Excel.
  - Additional information and a "how to" inside the script file.
