# fea_tools
Useful scripts for pre- and post-processing of FEA simulations will be shared here.

SearchNestedIncludes.py
  - Large FEA projects often have simulation solver input decks referencing files which are referencing other files and so on.
  - The purpose of the script is to find all includes referenced in the input deck and subsequently all other includes which may be nested.
  - This version is made for the LS-Dyna solver which uses the keyword "\*INCLUDE" to import FEA files(includes).
  - The script is to be called with the main solver input deck as an argument.
  - The script produces terminal output with absolute paths to all found includes.
  - The user can choose whether he wishes to copy all found files to a specific directory.
  - Currently bugs may occur if a file is referenced by a relative path.
