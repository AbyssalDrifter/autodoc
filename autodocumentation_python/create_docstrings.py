# -*- coding: utf-8 -*-
# autodoc - automatic documentation for Python code
#
# Copyright (c) 2023 - now
# Max-Planck-Institute of biological Intelligence, Munich, Germany
# Authors: Karl Heggenberger, Joergen Kornfeld

import ast
import os
from autodocumentation_python.gptapi import gptapi
from autodocumentation_python.summarize_file import code_info, node_info
from autodocumentation_python.make_snippets import make_snippets


def class_or_func_present(code):
    """
    This function checks if a Python file contains any class or function definitions.
    
    Args:
        code (str): The code to be analyzed.
    
    Returns:
        bool: Returns True if the code contains class or function definitions, otherwise False.
    """
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            return True
    return False


def create_docstrings(file_path: str, gpt_path: str, additional_info: str = None, max_lno: int = 300, Model: str = "gpt-4-32k", 
                 cost: str = 'cheap', write_gpt_output: bool = True):
    """
    This function generates detailed Google format docstrings for each function and class in a given Python file using the 
    gptapi. It handles large files by splitting them into smaller snippets and generating docstrings for each snippet separately. 
    
    Args:
        file_path (str): The path to the Python file for which to generate docstrings.
        gpt_path (str): The path to the GPT model used for generating the docstrings.
        additional_info (str, optional): Additional information about the repository that the code is embedded in. 
                                          This can help in generating more accurate docstrings. Defaults to None.
        max_lno (int, optional): The maximum number of lines that the function can handle in a single file. If the file 
                                  is larger than this, it will be split into smaller snippets. Defaults to 500.
        Model (str, optional): The model to use for generating the docstrings. Defaults to "gpt-3.5-turbo".
        cost (str, optional): The cost of generating the docstrings, if the file is not split into snippets. 'cheap' 
                               will use gpt-3.5-turbo and the output will be the whole file (code+docstrings). 
                               'expensive' will use gpt-4 and the output will be only the docstrings. Defaults to 'cheap'.
        write_gpt_output (bool, optional): Whether to write the GPT output/docstrings to a file. Defaults to True.
    
    Returns:
        str: The generated docstrings.
    """
    with open(file_path, "r") as file:
        code = file.read()
        file.seek(0)
        no_lines = len(file.readlines())


    if no_lines <= 300 and cost == 'cheap':
        Model = 'gpt-3.5-turbo-16k'
        print(f'Analyze file directly using {Model}: ', file_path)
        if not class_or_func_present(code):
            print('    No class- or function-definitions found. No docstrings are generated.')
            return ''
        command = """
Output this same code with DETAILED docstrings (or try to improve if one already exists)
in google format for all 
function and class. Never try to generate docstrings for the imports.
Begin a new line if an individual line of the docstring is longer than 90 characters.
Additional information is provided by the summary
of the repository this code is embedded in.
As an answer, only output the expanded code as a string, since your answer will be 
directly inserted into a python file which must be executable.
And keep any white spaces, indentation, and new lines in the code.
Just print out the source code with the generated docstrings.
"""
        command = ' '.join(line.strip() for line in command.split('\n')).strip()
        print("    Docstrings are generated. Waiting for a gpt response...")
        edited_code = gptapi(code, command, additional_info=additional_info, Model=Model) #gptapi(code, command, additional_info=additional_info, Model = 'gpt-3.5-turbo')
        code_lines = edited_code.split('\n')
        if code_lines[0].startswith('\'\'\'python'):
            del code_lines[0]
        if code_lines[-1].startswith('\'\'\''):
            del code_lines[-1]
        edited_code = '\n'.join(code_lines)

        if write_gpt_output:
            os.makedirs(os.path.dirname(gpt_path), exist_ok=True)
            with open(gpt_path, "w") as file:
                file.write(edited_code)

        return edited_code

    
    if (no_lines <= max_lno and cost == 'expensive') or (300<no_lines<=max_lno and cost == 'cheap'):
        print(f'Analyze file directly using {Model}: ', file_path)
        if not class_or_func_present(code):
            print('    No class- or function-definitions found. No docstrings are generated.')
            return ''
        

#NEW more readable COMMAND:

        # For the given python file below "code to be edited:" output ONLY the newly defined classes 
        # and functions (keeping the structure/indentation) as they are in the original code but with 
        # detailed generated docstrings and without the code inside. The rules are:
#         command = '''
# For the given python file below "code to be edited:" generate detailed docstrings for the 
# newly defined function and classes. The rules are:
# 1. Generate Docstrings: Provide detailed docstrings for each new class and function, formatted 
# according to the Google style guide, with a line width not exceeding 90 characters.
# 2. Exclusions: Do not generate docstrings for import statements or functions/classes that are 
# only called but not defined within the provided code.
# 3. Docstring Improvement: If a function or class already includes a docstring, the software 
# should attempt to enhance it. If the existing docstring is already comprehensive, it can be 
# reused.
# 4. Output Format: The output should be formatted to include only the names of the classes or 
# functions followed by their arguments (no return type annotations) and their corresponding docstrings, 
# without including any of the actual code. Like this:
# class ClassName(args):
#     """ Detailed docstring in Google format. """
#     def function_name(args): 
#     """ Detailed docstring in Google format. """
# 5. AST Module Readability: Ensure that the output is compatible with and readable by the ast 
# module in Python.
# 6. Handling No Code: If no code is provided to the software, it should output an empty string "".
# 7. Output Delimiters: The output should begin with the word "start" and end with "end" to denote 
# the start and finish of the processed docstring output.
# 8. Additional Information: (If any additional context about the repository or the code snippet is 
# provided, it should be considered to better understand the variables and context. However, no 
# docstrings should be generated for this part.)

# After processing, verify that all the rules have been met and make necessary adjustments to the 
# output to ensure compliance with the above specifications.
# '''


        command = '''
For the given python file below "code to be edited:" output ONLY the newly defined classes and functions
(keeping the structure/indention!!!) as they are in the original code but with detailed generated
docstrings and without the code inside. The rules are:
1. generate detailed docstrings in google format (max 90 characters per line)
2. just for EVERY newly defined functions and classes - if not existing: output the string: " "
3. dont write any imports, called functions or other code or comments
4. if function/class already has a docstring, try to improve or if already very well written reuse it
5. format: only output docstrings with corresponding name of function/class 
    and its args in brackets: def/class name(args):\n"""\ndocstring\n""" . So dont print the code
6. your output must be readable to the ast module!
7. if no code provided, output an empty string ""
8. Start your output with "start" and end with "end".

Maybe you be given additional information about the repository this code is embedded in
under "additional information:" to better construe the variables and context of the code.

In the end check if all rules are fulfilled and adjust if necessary.
'''
        #command = '\n'.join(line.strip() for line in command.split('\n')).strip()

        print("    Docstrings are generated. Waiting for a gpt response...")
        docstrings = gptapi(code, command, additional_info=additional_info, Model=Model)

        if write_gpt_output:
            os.makedirs(os.path.dirname(gpt_path), exist_ok=True)
            with open(gpt_path, "w") as file:
                file.write(docstrings)

        return docstrings

    elif no_lines > max_lno:
        print(f'analyzing file by splitting it into snippets (Model: {Model}): ', file_path)

        info_file = f'info about file: \n{code_info(file_path)}'
        info = (additional_info + '\n' + info_file) if additional_info else info_file
        code_snippets = make_snippets(file_path, max_lno=max_lno)
        #See how code is divided into snippets
        # for i, snippet in enumerate(code_snippets):
        #     print(f"{i+1}; lines: {snippet['lines']} ----------------------------")
        #     print(snippet['code'])


#NEW more readable COMMAND:

#         command = '''
# For the given python file below "code to be edited:" generate detailed docstrings for the 
# newly defined function and classes. The rules are:
# 1. Generate Docstrings: Provide detailed docstrings for each new class and function, formatted 
# according to the Google style guide, with a line width not exceeding 90 characters.
# 2. Exclusions: Do not generate docstrings for import statements or functions/classes that are 
# only called but not defined within the provided code.
# 3. Docstring Improvement: If a function or class already includes a docstring, the software 
# should attempt to enhance it. If the existing docstring is already comprehensive, it can be 
# reused.
# 4. Output Format: The output should be formatted to include only the names of the classes or 
# functions followed by their arguments (no return type annotations) and their corresponding docstrings, 
# without including any of the actual code. Like this:
# class ClassName(args):
#     """ Detailed docstring in Google format. """
#     def function_name(args): 
#     """ Detailed docstring in Google format. """
# 5. AST Module Readability: Ensure that the output is compatible with and readable by the ast 
# module in Python.
# 6. Handling No Code: If no code is provided to the software, it should output an empty string "".
# 7. Output Delimiters: The output should begin with the word "start" and end with "end" to denote 
# the start and finish of the processed docstring output.
# 8. Additional Information: (If any additional context about the repository or the code snippet is 
# provided, it should be considered to better understand the variables and context. However, no 
# docstrings should be generated for this part.)

# After processing, verify that all the rules have been met and make necessary adjustments to the 
# output to ensure compliance with the above specifications.
# '''

        command = '''
For the given python file below "code to be edited:" output ONLY the newly defined classes and functions
(keeping the structure/indention!!!) as they are in the original code but with detailed generated
docstrings and without the code inside. The rules are:
1. generate detailed docstrings in google format (max 90 characters per line)
2. for EVERY defined functions and classes - if not existing: output the string: " "
3. not for imports or called functions/classes
4. if function/class already has a docstring, try to improve or if already very well written reuse it
5. format: only output docstrings with corresponding name of function/class 
    and empty brackets: def/class name(args):\n"""\ndocstring\n""" . So dont print the code
6. your output must be readable to the ast module!
7. if no code provided, output an empty string ""
8. Start your output with "start" and end with "end".

Maybe you be given additional information about the repository this code is embedded in
under "additional information:" to better construe the variables and context of the code snippet.
Dont create docstrings for this part.

In the end check if all rules are fulfilled and adjust if necessary.
'''

        #command = ' '.join(line.strip() for line in command.split('\n')).strip()
        docstrings = '' #this will be a str of the edited func/classes
        line_start = 1
        for i, code_snippet in enumerate(code_snippets):
            print(f'    Docstrings are generated for snippet {i+1} (line {line_start}-{line_start+code_snippet["lines"]}) ...')
            try:
                if not class_or_func_present(code_snippet['code']):
                    print('    '*2 + 'No class- or function-definitions found in snippet. No docstrings are generated.')
                    line_start += code_snippet['lines']
                    continue
            except Exception:
                pass
                
            docstring = gptapi(code_snippet['code'], command, additional_info=info, Model=Model) + '\n'
            if write_gpt_output:
                os.makedirs(os.path.dirname(gpt_path), exist_ok=True)
                with open(gpt_path, "a") as file:
                    file.write(docstring+'\n')
            docstrings += docstring
            line_start += code_snippet['lines']

        
        
        return docstrings


