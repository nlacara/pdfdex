#!/usr/bin/python3

"""
Core functions for pdfdex (which is a dumb name).

The goal for these is for them to be more-or-less backend functions
that can be used with different interfaces. Hopefully there will be
a simple (but functional) GUI someday, but for now there will be a
console interface.
"""

import pdftotext    # For extracting text from PDFs
import re           # For making that text useful
import json         # For saving and loading the dictionary.

from nltk.corpus import stopwords   
from nltk import word_tokenize

# This a temporary dictionary that will store PDF text.
# The goal is to eventually replace this with a file
# that can be loaded and saved to. But one thing at a time...
pdf_dict = {}

# This stores the path of the current database file
# if one is opened.
dict_file = ""

# Loading and saving databases
def load_pdf_dict(input_file_path):
    with open(input_file_path, 'r') as input_file:
        return json.load(input_file)

def save_pdf_dict(output_file_path):
    with open(output_file_path, 'w') as output_file:
        json.dump(pdf_dict, output_file)


# Tools for building pdf_dict:

def proc_pdf(pdf_path, generate_keywords = False):
    """Processes an individual PDF file. Takes the text from each
    page of the pdf and makes a list of (page, text) tuples so that
    searches can return page numbers from individual pdf files.
    
    """
    
    # Read the contents of the file using pdftotext. This used
    # to be PyPDF4, but the output of pdftotext works *much*
    # better and works with far more PDFs than PyPDF did.
    pdf_file = open(pdf_path, 'rb')
    pdf_reader = pdftotext.PDF(pdf_file)
    
    # We need to know how many pages the pdf file has.
    pdf_len = len(pdf_reader)
    
    # We then extract each page, keeping track of the
    # page number:
    #no_punct =
    pdf_pages = []
    
    # Now we normalize some of the text, removing new lines,
    # regularizing spaces, and removing most punctuation.
    for page_no in range(pdf_len):
        page_text = re.sub( "[\n\r]", " ",
                               pdf_reader[page_no])
        page_text = re.sub("\s+", " ", page_text)
        page_text = re.sub("- ", "", page_text) 
        page_text = re.sub( "[^\w\s\'-]", "", page_text)
        
        pdf_pages.append( (page_no, page_text) )
        
    # Older and faster, but doesn't let me process
    # with regex's. Might try to rework it someday...
    #pdf_pages = [(page_no, 
                  #"".join([char.lower() 
                        #for char in pdf_reader.getPage(page_no).extractText()
                        #if char.isalpha()
                        #or char.isnumeric()
                        #or char in ['-', ' ']
                    #]))
             #for page_no in range(pdf_len)]
    
    
    # Close the file, just in case...
    pdf_file.close()
    
    # Generate keywords
    if generate_keywords:
        pdf_keywords = get_keywords(pdf_pages)
    else:
        pdf_keywords = []
        
    pdf_data = {
            "pages": pdf_pages,
            "path": pdf_path,
            "keywords": pdf_keywords,
            "user_keywords": []
        }
    
    return pdf_data

## Keywording tools ##

# Generate keywords for a pdf file:
def get_keywords(pdf_pages):
    """ Read data from a pdf_pages entry and return
    the most frequent tokens as keywords. This doesn't 
    always yield great results, but it kind of works."""
    
    # We'll need this for keyword detection
    stop_words = stopwords.words('english')

    # We will put each word token in words:
    words = []
    
    # Now looking at the text of each page:
    for page in [page[1] for page in pdf_pages]:
        
        # We remove any punctuation and lower-case everything:
        no_punct = "".join([char.lower() for char in page
                    if char.isalpha()
                    or char.isnumeric()
                    or char in ['-', ' ']
                    ])
        
        # We add the words to the words list 
        # if they aren't stop words.
        # Also I get a lot of junk short words
        # so putting a word length requirement.
        for word in no_punct.split():
            if word not in stop_words and len(word) > 2:
                words.append(word)
    
    # At this point, we start checking counts:
    words_types = set(words)
    type_counts = []
    for word_type in words_types:
        count = 0
        for word in words:
            if word == word_type:
                count += 1
        #type_counts.append( (count, word_type) )
        type_counts.append( (count / len(words), word_type) )
        
    type_counts.sort(reverse=True)
    
    return [word for (freq, word) in type_counts if freq >= 0.0035]
    #return set(word for word in type_counts[:25])

def pages_to_string(pdf):
    """Converts the pages of a pdf into just a string of text."""
    text = " ".join([page_text for (page_num, page_text) in pdf_dict[pdf]["pages"]])
    return text


# Generate similarity score based on full text:
def get_text_similarity(pdf0, pdf1):
    """Calculates the Jacquard similiarity of two texts.
    This is very simplistic and should be replaced with
    something a bit more robust."""
    pdf0_text = pages_to_string(pdf0)
    pdf1_text = pages_to_string(pdf1)
    
    pdf0_tokens = pdf0_text.split()
    pdf1_tokens = pdf1_text.split()
    
    #pdf0_tokens = word_tokenize(pdf0_text)
    #pdf1_tokens = word_tokenize(pdf1_text)
    
    intersect = set(pdf0_tokens).intersection(set(pdf1_tokens))
    union = set(pdf0_tokens).union(set(pdf1_tokens))
        

    return len(intersect) / len(union)

# Generate similarity score based on keywords:
def get_keyword_similarity(pdf1, pdf2):
    
    # We have to convert these to sets since JSON cannot save
    # set data types and they have to be stored as lists:
    pdf1_keywords = set(pdf_dict[pdf1]["keywords"])
    pdf2_keywords = set(pdf_dict[pdf2]["keywords"])
    
    # Find out how many tags each has in common
    # and how many tags there are in total.
    intersect = pdf1_keywords.intersection(pdf2_keywords)
    union = pdf1_keywords.union(pdf2_keywords)
    

    return len(intersect) / len(union)


# Find in-line citations!
def get_cites(pdf):
    """ Attempts to isolate citations in a document. It's still a bit
    experimental. It does not yet handle things like 'et al'. 
    
    It does not exclude material in references sections or bibliographies.
    It's not clear that that's even possible. Part of the issue here is that 
    some bibliography styles have things like 'Smith, John (1234)' and there is
    no real way to make the regex behave like 'John (1234)' is not an in-line
    citation. Still, I hope this kind of search function provides some sort of
    utility to the user."""
    
    # This pattern picks out various name--date combos.
    # TODO:
    #       - Get et als.
    #       - Get possessives -- Chomsky's (1965) view...
    pattern = r"(((\w+\,\s)?\w+\,?\s(and|&)\s)?\w+\s)\(?(\d{4})\)?"
    cites_found = set()
    
    # Search each page of the PDF for the citations.
    for page in pdf_dict[pdf]["pages"]:
        results = re.findall(pattern, page[1])
        
        # Attempt to regularize the formatting.
        for result in results:
            strings = [result[0], result[-1]]
            joined = " ".join(strings)
            joined = re.sub("\s+", " ", joined)
            joined = re.sub("\,?\s&", " and", joined)
            cites_found.add(joined)

    return list(sorted(cites_found))


def add_pdf(pdf_path, pdf_dict, keywords = False):
    """Processes a pdf file and adds it to a dictionary 
    base with all the text of every pdf file."""
    pdf_dict[pdf_path] = proc_pdf(pdf_path, generate_keywords = keywords)
    # Eventually, what this should do is check this against a
    # previously generated database and not process the pdf
    # if the pdf is already in the database.


# Search operations over pdf_dict
def dict_searcher(search_term, pdf_dict):
    return search_pages(search_term, pdf_dict)

def search_pages(search_string, pdf_dict):
    """Search the database of pdf text for a specific string"""
    
    # This will hold the pdf titles and the matching pages:
    pdf_matches = {}
    
    # Now we look through each PDF and its text:
    for pdf in pdf_dict.keys():
        
        # This will hold page matches for each PDF:
        page_matches = []
        
        # Now we search the text of each page of the pdf
        # and append any matching pages to page_matches:
        for page in pdf_dict[pdf]["pages"]:
            if search_string.lower() in page[1].lower():
                page_matches.append(page[0])
                
        # If there are no matching pages in the pdf at all,
        # then don't add the pdf to pdf_matches.
        if len(page_matches) > 0:
            pdf_matches[pdf] = page_matches
            
    # Return matching pdfs with matching page numbers.
    return pdf_matches

def search_keywords(keyword, pdf_dict):
    
    # This will hold the pdf paths for matching pdfs
    pdf_matches = []
    
    for pdf in pdf_dict.keys():
        if keyword in pdf_dict[pdf]["keywords"]:
            pdf_matches.append(pdf)
    
    return pdf_matches

# For concordancing
def multi_find(string, substring):
    """
    Find the starting index for a substring in a given string. 
    Essentially, an extension of the .find() string method.
    """
    # This will store the indices of matches.
    indices = []
    
    # Now we use .find() to see if there is a match in the string.
    index = string.find(substring)
    
    # If there is, we store the index that we've found.
    # Then we slice the remainder of the string and search
    # through that and collect the results recursively.
    # (.find() returns -1 if it finds nothing.)
    if index >= 0:
        indices.append(index)
        # The +1 avoids an infinite recursive loop.
        for next_index in multi_find(string[index + 1:], substring):
            indices.append(next_index + index + 1)
        
    return indices

def concordance(pdf, term, surrounding_text = 30):
    """ 
    Generates data for displaying a concordance. The indicated pdf
    is searched for the given term, and the function returns a tuple
    containg the page at which that term has been found, the text
    that appears immediately before the term, the term as it appears
    in the text, and the test immediately following the term.
    
    The length of the material before and following the term
    is determined with the surrounding_text argument and can
    be adjusted if necessary.
    """
    pdf_pages = pdf_dict[pdf]['pages']
    
    results = []
    
    for page in pdf_pages:
        #print("Page:", page[0], "\tLength:", len(page[1]))                      #####
        page_text_lower = page[1].lower()
        
        # Make sure the term is actually on this page.
        if term.lower() in page_text_lower:
            # If it is, look for it
            # This will need to be made a bit more complex, since
            # find() only returns the first index value.
            term_indices = multi_find(page_text_lower, term.lower())
            #print("Term '{}' found at indices {}.".format(term, term_indices))      #####
            
            # Get the preceding material. If the search term is toward the 
            # beginning of the page, we want to make sure that the preceding
            # text is long enough.
            for term_index in term_indices:
                term_text = page[1][term_index:term_index + len(term)]
                if term_index > surrounding_text:
                    preceding_text = page[1][term_index - surrounding_text:term_index]
                else:
                    preceding_text = page[1][0:term_index]
                    
                # We do the same thing for the following text...
                if (term_index + len(term) + surrounding_text) > len(page):
                    following_text = page[1][term_index + len(term) : term_index + len(term) + surrounding_text]
                else:
                    following_text = page[1][term_index + len(term):]
                    
                results.append( (page[0], preceding_text, 
                                 term_text, following_text) )
                
    return results
            
