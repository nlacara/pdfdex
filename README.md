# PDFdex

PDFdex is a program for searching and (perhaps someday) indexing collections of PDF files.

What you see here is more of a proof of concept than fully working code. Expect to see improvements in the future.

## Requirements

PDFdex currently relies on the Natural Language Toolkit (NLTK) and pdftotext for some of its functionality. All other libraries (json, re) are standard libraries.

## Usage

- Start the program by running `pdfdex.py`.
- Upon running the script the user will be greeted by a menu.
- The program starts with an empty database. To add a file to the database, choose option (5).
    - The user can add a single PDF file or all the PDF files in a given directory.
    - When adding PDFs, you will be asked if you want to autogenerate keywords. This can take a while, especially if you are working with long PDFs.
- Once you have some PDF file added, you can search them.
- If you didn't generate keywords when adding the PDFs to the database, you can do this with option (3).
    - To see automatically generated keywords for a PDF file, use option (4).
- To save the database, choose option (0). To load a previously created database, choose option (9).
- To display the menu again, type 'm'. To quit, enter 'q'.
