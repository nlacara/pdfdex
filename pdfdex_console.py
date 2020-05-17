#!/usr/bin/python3

"""
Console interface functions for PDFdex.
"""

import os           # For some file management stuff

from pdfdex_core import *
from colorama import Fore, Style

# Some formatting stuff:
def file_path(path):
    return Fore.LIGHTRED_EX + path + Style.RESET_ALL

def highlight(element):
    return Fore.LIGHTCYAN_EX + element + Style.RESET_ALL

# Start menu:
def menu_title(title, menu_width):
    title_width = int((menu_width - len(title) - 2) / 2)
    if len(title) % 2 != 0 and menu_width % 2 == 0:
        fudge = 1
    else:
        fudge = 0
    print("\n" + "╒" + "═" * title_width + " " + title + " " + "═" * (title_width + fudge) + "╕")

def menu_item(item, menu_width):
    space = menu_width - len(item)
    print("│" + item + " " * space + "│")
    
def menu_sep(menu_width, title = ""):
    print("│" + " " * menu_width + "│")
    title_width = int((menu_width - len(title)) / 2)
    fudge = 0
    if len(title) + (title_width * 2) != menu_width:
        fudge += 1

    print("├" + "─" * title_width + title + "─" * (title_width + fudge) + "┤")
    print("│" + " " * menu_width + "│")

def menu_end(menu_width):
    print("│" + " " * menu_width + "│")
    print("└" + "─" * menu_width + "┘")


def make_menu(title, menu_items):
    
    width = max(max(len(element) for element in menu_items) + 2, len(title) + 2)
    
    menu_title(title, width)
    for element in menu_items:
        if element.startswith("sep_"):
            title = re.findall(r"sep_(.*)", element)[0]
            menu_sep(width, title)
        else:
            menu_item(" " + element, width)
    menu_end(width)


def menu():
    menu_items = ["sep_Search", 
                    "(1) Search PDF texts      (2) Search keywords", 
                  "sep_Keyword", 
                    "(3) Generate keywords     (4) View keywords", 
                  "sep_PDF Management",
                    "(5) Add file to database  (6) Remove file from database",
                  "sep_Experimental!",
                    "(7) Similarity            (8) View in-line citations",
                  "sep_Load/Save database",
                    "(9) Load database         (0) Save database",
                  "sep_Misc",
                    "(Q) Quit                  (M) Repeat menu"
                ]
    make_menu("Main menu", menu_items)
    width = 32
    quit = False    
    while quit == False:
        
        selection = input("\nSelect option: ")
        
        if selection == '1':
            string_search()
        elif selection == '2':
            keyword_search()
        elif selection == '3':
            generate_keywords_menu()
        elif selection == '4':
            display_keywords_menu()
        elif selection == '5':
            add_file_menu()
        elif selection == '6':
            remove_file_menu()
        elif selection == '7':
            find_similar_menu()
        elif selection == '8':
            display_cites_menu()
        elif selection == '9' or selection.lower() == 'l':
            load_menu()
        elif selection == '0':
            save_menu()
        elif selection.lower() == 'v':
            list_menu()
        elif selection.lower() == 'm':
            make_menu("Main menu", menu_items)
        elif selection.lower() == 'q':
            print("Exiting")
            quit = True
        else:
            print("Invalid selection")
        
    

# String search code
def string_search():
    """ Console front end for searching pages in pdf_dict database """
    search_string = input("Enter a string to search for: ")
    results = search_pages(search_string, pdf_dict)
    display_string_search_result(search_string, results)
    
def display_string_search_result(string, results):
    """Displays search results in a console."""
    if len(results) > 0:
        print('\nMatches for string',
              '"{}" found in {} PDF(s).'.format(highlight(string), 
                                                                len(results)))
        
        # To get nice numerical indices for each key:
        result_keys = [key for key in results.keys()]
        
        # Show each result:
        for key in result_keys:
            print("\n{:>3} {} ({} matching pages found)".format(str(result_keys.index(key) + 1) + ')', 
                                                                file_path(key), 
                                                                len(results[key])))
            print("    Pages:", [result + 1 for result in results[key]])
        
        # Ask to see if the user wants to see results in a concordance
        concordance = True
        while concordance:
            print("\nSelect number to see in concordance,")
            option = input("or press enter to continue: ")
            if option == "":
                concordance = False
            elif int(option) - 1 < len(result_keys):
                display_concordance(result_keys[int(option) - 1], string)
            else:
                print("Invalid option!")
            
    else:
        print("No matches found.")
    

# Keyword search code        
def keyword_search():
    """Console front-end for searching auto-generated keywords."""
    search_string = input("Enter keyword to search for: ")
    results = search_keywords(search_string, pdf_dict)
    display_keyword_search_result(search_string, results)
    
def display_keyword_search_result(search_string, results):
    if len(results) > 0:
        print('\nMatches for keyword "{}" found in {} PDF(s).'.format(search_string, len(results)))
        for result in results:
            print("{:>3}) {}".format(results.index(result) + 1, file_path(result)))
    else:
        print("No matches found.")
    
        
# Keyword display        
def display_keywords_menu():
    """Lists individual PDFs in order to display keywords. """
    print("Select PDF to get associated keywords.")
    selection = get_pdf_from_list()
    display_keywords(selection)
        
def display_keywords(key):
    """Displays keywords from an associated PDF in the database."""
    if len(pdf_dict[key]["keywords"]) == 0:
        print("File {} has no keywords associated with it.".format(key))
        generate = input("Do you want to generate keywords? Enter Y for yes: ")
        if generate == "Y":
            pdf_keywords = get_keywords(pdf_dict[key]["pages"])
            for keyword in pdf_keywords:
                pdf_dict[key]["keywords"].append(keyword)
            print("\nKeywords for file {}:".format(file_path(key)))
            print([word for (freq, word) in sorted(pdf_dict[key]["keywords"])])
        else:
            pass
    else:
        print("\nKeywords for file {}:".format(file_path(key)))
        print(sorted(pdf_dict[key]["keywords"], reverse=True))
    

# Generate keywords
def generate_keywords_menu():
    """
    Menu item for attempting to automatically geneate keywords.
    """
    print("\nDo you want to generate keywords for a specific file,")
    print("or do you want to generate keywords for all files that")
    print("currently lack keywords (which might take awhile)?")
    
    ask = True
        
    while ask == True:
        all_or_one = input("1) Specific file \t 2) All files \t Choice: ")

        # Get list of files without keywords
        # you need it either way
        pdfs_without_keywords = []
        if all_or_one == "1" or all_or_one == "2":
            for key in pdf_dict.keys():
                if len(pdf_dict[key]["keywords"]) == 0:
                    pdfs_without_keywords.append(key)
        
        # If there are no pdfs without keywords, then go back to the menu.
        if len(pdfs_without_keywords) == 0:
            print("\nAll indexed PDFs have keywords!")
            ask = False
            
        # If there are PDFs without keywords,
        # then we can generate them.
        else:
            # If the user wants a specific PDF:
            if all_or_one == "1":
                
                # Choose a file from those that lack keywords:
                file_choice = get_pdf_from_list(pdfs_without_keywords)
                
                # Find and add keywords
                pdf_keywords = get_keywords(pdf_dict[file_choice]["pages"])
                for keyword in pdf_keywords:
                    pdf_dict[file_choice]["keywords"].append(keyword)
                    
                print("\n{} keywords added for file {}!".format(len(pdf_keywords), file_path(file_choice)))
                ask = False
            
            # If the user wants to keyword all eligble PDFs
            elif all_or_one == "2":
                for pdf in pdfs_without_keywords:
                    pdf_keywords = get_keywords(pdf_dict[pdf]["pages"])
                    for keyword in pdf_keywords:
                        pdf_dict[pdf]["keywords"].append(keyword)
                    print("\n{} keywords added for file {}!".format(len(pdf_keywords), file_path(pdf)))
                ask = False

            else:
                ask == False

# Add and remove files:

def add_file_menu():
    """
    Menu option that adds file(s) to the database. Allows user
    to add a single PDF file or all PDF files in a directory.
    
    TODO:
        - Make sure the same file (path) cannot be added more than once.
        - Probably separate out code for adding a single file.
    """
    print("\nAdd 1) single file or 2) whole directory? ")    
    single = input("Press Enter to cancel: ")
    
    if single == "2":
        add_directory_menu()
    elif single == "1":
        file_to_add = input("Enter file name to add to database (press enter to cancel): ")
        if file_to_add.upper() == '':
            pass
        else:
            make_keywords = input("Autogenerate keywords? Enter 'Y' for yes: ")
            
            if make_keywords.upper() == 'Y':
                gen_keywords = True
            else:
                gen_keywords = False
            
            try:
                pdf_data = add_pdf(file_to_add, pdf_dict, keywords = gen_keywords)
                
            except FileNotFoundError:
                print("File {} not found!".format(file_path(file_to_add)))
    else:
        pass
            
def add_directory_menu():
    """
    Add all of the pdfs in a given directory.
    
    TODO:
        - Throw warning if attempting to add file already in DB
        - Warning if path not found
        - Make it so paths don't have to end in /
    """
    dir_path = input("\n Path: ")
    pdfs = [pdf_file for pdf_file in os.listdir(dir_path) if pdf_file.endswith(".pdf")]
    add = input("Add {} PDF files to database?".format(len(pdfs)))
    if add.lower() == "y":
        for pdf in pdfs:
            pdf_data = add_pdf(dir_path + pdf, pdf_dict)
            print("File {} added!".format(file_path(dir_path + pdf)))
    
def remove_file_menu():
    print("Remove file not implemented.")
     
def find_similar_menu():
    """
    Calculates the Jacquard similarity of texts. More 
    advanced mechanisms should replace this at some point; 
    this is a stand-in for better, later functionality.
    """
    
    print("Would you like to do keyword similarity (faster, less accurate)")
    print("Or full text similarity (longer, might also be inaccurate)?")
    choice = input("1) Keyword\t2) full text")
    
    if choice == "1":
        find_keyword_similar_menu()
    elif choice == "2":
        find_text_similar_menu()
    else:
        pass

# Similarity based on keywords
def find_keyword_similar_menu():
    """
    Attempts to determine which PDFs are most similar to each other
    based on similarity of keywords. This is still experimental and
    needs to be improved as the current approach is quite facile.
    """
    
    print("We will compare the keyword")
    print("similarity between the PDF you")
    print("select and all other PDFs in the database.")
    choice = get_pdf_from_list()
    
    scores = [(get_keyword_similarity(choice, pdf), pdf) 
              for pdf in pdf_dict.keys()
              if pdf != choice]
    
    print("\nKeyword similarity scores for {}:".format(file_path(choice)))
    #longest_path = max([len(path) for (score, path) in scores])
    for score, pdf in sorted(scores, reverse = True):
        print(" {:35} {}".format(file_path(pdf), round(score, 3)))

# Similarity based on text
def find_text_similar_menu():
    """
    Attempts to determine which PDFs are most similar to each other
    based on similarity of keywords. This is still experimental and
    needs to be improved as the current approach is quite facile.
    """
    
    print("We will compare the text similarity")
    print("between the PDF you select and")
    print("all other PDFs in the database.")
    choice = get_pdf_from_list()
    
    scores = [(get_text_similarity(choice, pdf), pdf) 
              for pdf in pdf_dict.keys()
              if pdf != choice]
    
    print("\nText similarity scores for {}:".format(file_path(choice)))
    #longest_path = max([len(path) for (score, path) in scores])
    for score, pdf in sorted(scores, reverse = True):
        print(" {:35} {}".format(file_path(pdf), round(score, 3)))

# Display in-line citations
def display_cites_menu():
    """Lists all in-line citations in a given PDF.
    This is a bit experimental..."""
    print("Select PDF to search for in-line citations.")
    selection = get_pdf_from_list()
    display_cites(selection)
    
def display_cites(pdf):
    citations = get_cites(pdf)
    print("{} in-line citations found in {}!".format(len(citations), pdf))
    print(citations)
    

# List pdfs in the database
def get_pdf_from_list(pdf_list = 0, list_items = 10):
    
    if pdf_list == 0:
        pdfs = [key for key in pdf_dict.keys()]
    else:
        pdfs = pdf_list
    
    total_pdfs = len(pdfs)
    remainder = total_pdfs % list_items
    cycles = int((total_pdfs - remainder) / list_items)
    
    for cycle in range(cycles):
        for pdf in pdfs[cycle * list_items:(cycle + 1) * list_items]:
            print("{:>2}) {}".format(pdfs.index(pdf) - cycle * list_items + 1, file_path(pdf)))
        select = True
        while select:
            selection = input("Enter number or press enter to continue: ")
            if selection == "":
                select = False
            else:
                try:
                    return pdfs[int(selection) + (cycle * list_items) - 1]
                except ValueError:
                    print("Invalid selection")
                    
    # If we go through all the cycles of
    # list_items PDFs, list the remaining pdfs:
    for pdf in pdfs[-remainder:]:
        print("{:>2}) {}".format(pdfs.index(pdf) + 1 - cycles * list_items, file_path(pdf)))
    select = True
    while select:
        selection = input("Enter number or press enter to continue: ")
        if selection == "":
            select = False
        else:
            try:
                return pdfs[int(selection) - 1 + (cycles * list_items)]
            except ValueError:
                print("Invalid selection")

# Concordance
def concordance_menu():
    print("Select a PDF")
    selection = get_pdf_from_list()
    term = input("Enter a search term: ")
    
    display_concordance(selection, term)
    
def display_concordance(pdf, term):
    results = concordance(pdf, term)
    for result in results:
        print("{:>2} - {:>30} {} {:<30}".format(result[0] + 1, result[1], 
                                     highlight(result[2]),
                                     result[3]))

def list_menu():
    for pdf in pdf_dict.keys():
        print(file_path(pdf))


def load_menu():
    global dict_file
    if len(pdf_dict) > 0:
        print("Loading a new file will overwrite the current databse.")
        print("Do you want to save the current database first?")
        save = input("Enter 'Y' for yes: ")
        if save.upper() == 'Y':
            save_menu()
    
    load_path = input("\nEnter file name to load: ")
    
    try:
        pdf_dict.clear()
        pdf_dict.update(load_pdf_dict(load_path))
        dict_file = load_path
        print("\nFile {} loaded.".format(file_path(load_path)))
        print("Index contains {} entries.".format(len(pdf_dict)))
    except FileNotFoundError:
        print("File {} not found!".format(file_path(load_path)))



def save_menu():
    global dict_file
    if dict_file != "":
        print("\nCurrent database: {}".format(file_path(dict_file)))
        save = input("Save to this file? Enter Y for yes, or press enter for new file: ")
        if save.lower() == "y":
            save_path = dict_file
            
        else:
            save_path = input("Enter new file name, or press enter to cancel: ")
    else:
        save_path = input("Enter new file name, or press enter to cancel: ")
    
    if save_path != "":
        save_pdf_dict(save_path)
        print("File saved to {}.".format(file_path(save_path)))
        dict_file = save_path
