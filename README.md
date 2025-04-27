# TTS_ebook_preprocessing
small program to help preprocess ebooks to fix issues such as word pronouciation, heteronyms, and a few otheres.
Synopsis of the bookfix.py Program: Read Pronunciation Tool

Description:

Synopsis of the bookfix.py Program: Read Pronunciation Tool
The bookfix.py script is a GUI tool built with the Tkinter library, designed to help users clean and standardize text from input files like plain text (.txt) and HTML/XHTML (.html, .xhtml). Its main goal is to prepare the text, potentially for text-to-speech (TTS) applications, by providing a way to handle inconsistent wording and apply automatic cleanup rules.

The program guides the user through making decisions for specific words and then performs a series of automatic text transformations based on rules read from a separate data file.

Here's a breakdown of its main components and how it functions:

Program Flow and GUI
The script starts by importing necessary libraries (tkinter, re, os, BeautifulSoup, etc.) for GUI creation, text processing, and file handling.
The main() function is the program's starting point. It begins by creating the main Tkinter window.
Before displaying the main processing interface, the select_file() function is called to open a file dialog. This allows the user to choose the input file (.txt, .html, or .xhtml). The dialog includes options to show hidden files. If a file is selected, the program notes its path and changes the working directory; if cancelled, the program exits.
If a file is chosen, main() sets up the core GUI elements: a large text area (text_area) for displaying and interacting with the text, a status_label for user feedback, a choice_frame to hold replacement buttons, and a button_frame for general actions like "Save" and "Quit".
Data Loading and Rules
Inside the run_processing() function (which is called by main() after file selection), the content of the input file is read.
The load_data_file() function is then executed. It reads rules from a local data file named .data.txt, which must be in the same directory as the script.
This .data.txt file is structured into sections:
#CHOICE: Lists words or phrases for which the program should pause and present the user with predefined replacement options.
#REPLACE: Defines simple find-and-replace rules that are applied automatically.
#PERIODS: Specifies abbreviations (like "Mr") that should have periods automatically inserted (e.g., "M.r.").
The function parses these sections and returns the rules as Python dictionaries and sets.
Interactive Choice Processing
After loading rules, run_processing() calls process_choices(). This function handles the interactive cleanup.
It iterates through each item listed in the #CHOICE section of the .data.txt file.
For the current word needing a choice, update_matches() finds all occurrences in the text using regular expressions.
highlight_current_match() then highlights the first occurrence in the GUI's text area and scrolls it into view.
update_choice_buttons() creates specific buttons in the choice_frame, each representing a possible replacement option from the data file. For words with two options, keyboard shortcuts (1 and 2) are bound for quick selection.
The program pauses, waiting for the user to click a choice button.
The handle_choice() function is triggered by a button click. It replaces the currently highlighted word in the text and the text area with the selected option, finds the next match for the same word, and updates the highlight. It also writes the choice made (original -> chosen) to a debug.txt file.
Once all instances of a particular word from the #CHOICE list are processed, the function moves to the next word in the list. A Progressbar indicates the overall progress through the list of words requiring choices.
Automatic Processing
After all interactive choices are completed, run_processing() executes several functions for automatic text cleanup:
apply_automatic_replacements(): Goes through the rules from the #REPLACE section and performs all simple find-and-replace operations throughout the text.
remove_pagination(): Attempts to identify and remove common page number patterns. It uses BeautifulSoup to parse HTML/XHTML for specific classes/IDs or paragraph content and simpler line checks for .txt files. Removals are logged to pagination_debug.txt.
convert_roman_numerals(): Finds uppercase Roman numerals (like "XII") and converts them to their Arabic integer equivalents ("12"), with logic to avoid single "I"s or potential false positives near punctuation.
convert_to_lowercase(): Converts the entire text content to lowercase.
(The insert_periods_into_abbreviations() function is present in the code but commented out, so it is not executed).
Output and Exit
Once all processing steps are finished, update_text_area() displays the final state of the text in the GUI, and update_status_label() indicates that processing is complete.
display_save_button() makes the "Save" button visible.
Clicking the "Save" button calls save_file(), which saves the processed text to a new plain text file. The output file is placed in the same directory as the input file and named by adding "_output" to the original filename (e.g., mybook.txt becomes mybook_output.txt). A message box confirms the save location.
The "Quit" button calls quit_program(), which gracefully closes the application window and exits the script.
In summary, the bookfix.py tool streamlines the process of cleaning and standardizing text from ebook formats. It uses a configuration file to define interactive and automatic replacement rules, provides a GUI for user guidance on specific wording issues, and performs several automated cleanup tasks like pagination removal and numeral conversion before allowing the user to save the final, corrected text.

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
