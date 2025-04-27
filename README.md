# TTS_ebook_preprocessing
small program to help preprocess ebooks to fix issues such as word pronouciation, heteronyms, and a few otheres.
Synopsis of the bookfix.py Program: Read Pronunciation Tool

Description:

Brief Synopsis of the bookfix.py Program
The bookfix.py script is a GUI application (using Tkinter) designed to clean and standardize text from files like TXT, HTML, and XHTML, often to prepare them for text-to-speech.

Here's what it does:

File Selection: Starts by prompting the user to select an input file via a standard file dialog.
Loads Rules: Reads processing rules (interactive choices, automatic replacements, abbreviations) from a .data.txt file in the script's directory.
Interactive Replacement:
Finds specific words listed in .data.txt.
Highlights each word occurrence in a text area.
Presents buttons with replacement options for the user to click.
Replaces the word based on the user's choice.
Includes a progress bar and logs choices to debug.txt.
Automatic Processing: After interactive steps, it automatically applies transformations:
Runs find-and-replace rules from .data.txt.
Removes detected pagination (page numbers), logging removals to pagination_debug.txt.
Converts uppercase Roman numerals to Arabic numbers.
Converts all text to lowercase.
Save Output: Once processing is done, a "Save" button appears, allowing the user to save the final cleaned text to a new .txt file (e.g., input_file_output.txt).
User Interface: Provides a text display, status updates, and control buttons.
Essentially, it's a semi-automated text cleaning tool that combines user guidance for tricky cases with predefined automatic cleanup rules.

Data Loading (load_data_file):

The run_processing() function, called by main() after GUI setup, starts by reading the content of the selected input file.
It then calls load_data_file(). This crucial function reads a local data file named .data.txt located in the same directory as the script.
The data file contains rules for processing the text, divided into sections:
#CHOICE: Lists words where the program should pause and ask the user to choose the correct form from a predefined list.
#REPLACE: Contains simple find-and-replace rules that are applied automatically without user intervention.
#PERIODS: Lists abbreviations where periods should be automatically inserted (e.g., "Mr" might become "M.r.").
The function parses these rules and returns them as dictionaries and sets.

