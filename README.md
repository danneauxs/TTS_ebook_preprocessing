# TTS_ebook_preprocessing
small program to help preprocess ebooks to fix issues such as word pronouciation, heteronyms, and a few otheres.
Synopsis of the bookfix.py Program: Read Pronunciation Tool

Description:

The bookfix.py script is a GUI tool for cleaning and standardizing text files (TXT, HTML, XHTML) to prepare them for uses like text-to-speech.

Key Features and Functions:

GUI Interface: Provides a graphical window using Tkinter for user interaction.
File Selection: Allows the user to browse for and select an input text file using a file dialog, with an option to show hidden files.
Data File Loading: Reads processing rules (interactive choices, automatic replacements, abbreviations for period insertion) from a .data.txt file located with the script.
Interactive Choices:
Identifies specific words in the text based on the .data.txt file.
Highlights each instance of these words in a text area.
Presents buttons with predefined replacement options for the user to choose from.
Replaces the word in the text with the user's selection.
Includes a progress bar for the interactive process.
Logs user choices to debug.txt.
Automatic Processing: Applies several transformations automatically after interactive choices:
Performs all find-and-replace rules from the .data.txt file.
Attempts to remove pagination (page numbers) from the text, with format-specific logic for HTML/XHTML and TXT. Logs removals to pagination_debug.txt.
Converts uppercase Roman numerals to Arabic integers, with some exceptions.
Converts the entire text to lowercase.
(Includes a function to insert periods into abbreviations, but it's currently commented out).
Output Save: Allows the user to save the final processed text to a new .txt file (named based on the input file) via a "Save" button that appears after processing.
Quit Function: Provides a button to cleanly exit the application.
In essence, the tool enables users to semi-automatically clean and standardize text content by combining guided manual decisions with automated find/replace and formatting tasks, driven by external configuration in the .data.txt file.


Detailed Description:

The bookfix.py script is a Python application with a graphical user interface (GUI) built using the Tkinter library. Its primary purpose is to assist a user in cleaning and standardizing text from various input file formats, such as plain text (.txt) and HTML/XHTML (.html, .xhtml), with a focus on preparing the text for potential text-to-speech (TTS) processing or improved readability.

The program works by guiding the user through interactive choices for specific words and applying a series of automatic text transformations based on predefined rules.

Here's a breakdown of its main components and how it functions:

Initialization and Setup:

The script starts by importing necessary libraries like tkinter for the GUI, re for regular expressions, os for file system interaction, BeautifulSoup for parsing HTML/XML, and modules for fonts and progress bars.
The main() function serves as the program's entry point. It first creates the main Tkinter window.
File Selection (select_file):

Before the main processing GUI appears, the select_file() function is called.
This function opens a standard file dialog, allowing the user to browse for and select an input text, HTML, or XHTML file.
It sets a default starting directory and includes settings to optionally show hidden files in the dialog.
If a file is selected, the program records the file path and changes the script's current working directory to that of the selected file. If the user cancels the dialog, the program exits.
GUI Setup (in main):

If a file is successfully selected, the main() function proceeds to set up the main GUI elements within the previously created window.
This includes a large text area (text_area) to display the text being processed, a status label (status_label) to provide feedback, a frame (choice_frame) where interactive choice buttons will appear, and a frame (button_frame) for action buttons like "Save" and "Quit". A variable (choice_var) is also initialized to help manage the interactive choice process.
Data Loading (load_data_file):

The run_processing() function, called by main() after GUI setup, starts by reading the content of the selected input file.
It then calls load_data_file(). This crucial function reads a local data file named .data.txt located in the same directory as the script.
The data file contains rules for processing the text, divided into sections:
#CHOICE: Lists words where the program should pause and ask the user to choose the correct form from a predefined list.
#REPLACE: Contains simple find-and-replace rules that are applied automatically without user intervention.
#PERIODS: Lists abbreviations where periods should be automatically inserted (e.g., "Mr" might become "M.r.").
The function parses these rules and returns them as dictionaries and sets.
Interactive Choice Processing (process_choices and Helpers):

After loading the data, run_processing() calls process_choices(). This is the core interactive part of the tool.
It iterates through each word specified in the #CHOICE section of the data file.
For the current word, update_matches() finds all its occurrences in the text using regular expressions.
highlight_current_match() then visually highlights the first instance of that word in the text area.
update_choice_buttons() dynamically creates buttons in the choice_frame, one for each replacement option listed for that word in the data file. For words with exactly two options, it also sets up keyboard shortcuts (1 and 2) to quickly select them.
The program then waits for the user to click one of the choice buttons.
The handle_choice() function is triggered when a button is clicked. It replaces the highlighted word in the text and the text area with the chosen option, moves to the next match of the same word, and updates the highlighting and status. It also logs the choice made to a file named debug.txt.
Once all occurrences of the current word have been processed, the process_choices function moves on to the next word from the #CHOICE list. A progress bar shows the overall progress through the list of words requiring choices.
Automatic Processing Steps:

After the interactive choices are complete, run_processing() applies several automatic transformations:
apply_automatic_replacements(): Goes through the rules loaded from the #REPLACE section of the data file and performs all specified find-and-replace operations.
remove_pagination(): Attempts to detect and remove common pagination patterns (like page numbers) from the text. It uses different logic for HTML/XHTML (using BeautifulSoup to find elements by class/ID or simple paragraph content) and plain text files (checking if lines contain only digits). It logs removed items to pagination_debug.txt.
convert_roman_numerals(): Finds uppercase Roman numerals in the text (excluding single 'I's or those attached to punctuation) and converts them into their Arabic integer equivalents.
convert_to_lowercase(): Converts the entire text content to lowercase.
(insert_periods_into_abbreviations() is present but commented out in the provided code).
After these steps, update_text_area() refreshes the display to show the final state of the processed text, and update_status_label() indicates completion.
Saving Output (save_file):

Once all processing is finished, display_save_button() makes the "Save" button visible.
Clicking the "Save" button triggers the save_file() function. This function saves the final, modified text content to a new plain text file in the same directory as the input file, adding "_output" to the original filename.
Quitting (quit_program):

The "Quit" button calls the quit_program() function, which closes the GUI window and exits the script.
In summary, bookfix.py provides a step-by-step process for cleaning and reformatting text documents, combining interactive user decisions based on a data file with a series of automated text manipulation routines, culminating in a saved, corrected text output.
