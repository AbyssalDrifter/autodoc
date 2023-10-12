import os
import re
import sys
import shutil
import subprocess

def count_lines(file_path):
    """
    Counts the number of non-empty lines in a file.
    
    Args:
        file_path (str): The path to the file.
        
    Returns:
        int: The number of non-empty lines in the file.
    """
    with open(file_path, "r") as file:
        return sum(1 for line in file if line.strip() != "")

def count_words(file_path):
    """
    Counts the number of words in a file. A word is defined as a sequence of alphanumeric characters.
    
    Args:
        file_path (str): The path to the file.
        
    Returns:
        int: The number of words in the file.
    """
    with open(file_path, "r") as file:
        content = file.read()
        words = re.findall(r'\w+', content)
        return len(words)

def count_code_and_words(directory, max_lno):
    """
    Counts the total lines of code and words in all Python, .rst, and .md files in a directory.
    Also counts the number of files with lines of code above a maximum limit and the total lines in these files.
    
    Args:
        directory (str): The path to the directory.
        max_lno (int): The maximum limit for lines of code in a file.
        
    Returns:
        tuple: The total lines of code, total words, number of files with lines of code above max_lno, 
               and total lines in these files.
    """
    total_lines = 0
    total_words = 0
    num_files_above_max = 0
    lines_above_max = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".py"):
                lines = count_lines(file_path)
                total_lines += lines
                if lines > max_lno:
                    num_files_above_max += 1
                    lines_above_max += lines
            elif file.endswith((".rst", ".md")):
                total_words += count_words(file_path)
    
    return total_lines, total_words, num_files_above_max, lines_above_max

def cost_estimator(max_lno: int, target_dir: str, model, cost):
    # print(f"Total lines of code: {total_lines} -> {total_lines * 20} tokens")
    # print(f"Total words in .rst and .md files: {total_words} -> {total_words * 1.25} tokens (< 16k tokens!!! else detailed == False)")
    # print(f"Number of files with more than {max_lno} lines: {num_files_above_max}")
    # print(f"Total lines in files above {max_lno} lines: {lines_above_max} -> {lines_above_max * 20} tokens (with gpt4)")
    #     
    max_lno = 300
    
    #calculate for gpt4-32k (max_lno can be chooses freely (1200 is the default))
    total_lines, total_words, num_files_above_max, lines_above_max = count_code_and_words(target_dir, max_lno)
    expensive_gpt4_32k = (total_lines * 20 * 0.12 + total_words * 1.25 * 0.004) / 1000
    cheap_gpt4_32k = ((((total_lines - lines_above_max)*20*2) + (total_words *1.25)) * 0.004 + (lines_above_max * 20) * 0.12) / 1000

    total_lines, total_words, num_files_above_max, lines_above_max = count_code_and_words(target_dir, max_lno=300)
    expensive_gpt4= (total_lines * 20 * 0.06 + total_words * 1.25 * 0.004) / 1000
    cheap_gpt4 = ((((total_lines - lines_above_max)*20*2) + (total_words *1.25)) * 0.004 + (lines_above_max * 20) * 0.06) / 1000

    print('To estimate the costs, we assume that one line of code corresponds to 20 tokens.')
    print(f'Estimated costs with settings...')
    print(f"    --cost 'expensive' --Model 'gpt-4':      {expensive_gpt4:.2f}$")
    print(f"    --cost 'expensive' --Model 'gpt-4-32k':  {expensive_gpt4_32k:.2f}$")
    print(f"    --cost 'cheap' --Model 'gpt-4':          {cheap_gpt4:.2f}$")
    print(f"    --cost 'cheap' --Model 'gpt-4-32k':      {cheap_gpt4_32k:.2f}$")
    print('Keep in mind: these are just rough estimates!!!\n')

    if cost == 'expensive' and model == 'gpt-4':
        print(f'Your are going to spent about {expensive_gpt4:.2f}$')
    elif cost == 'expensive' and model == 'gpt-4-32k':
        print(f'Your are going to spent about {expensive_gpt4_32k:.2f}$')
    elif cost == 'cheap' and model == 'gpt-4':
        print(f'Your are going to spent about {cheap_gpt4:.2f}$')
    elif cost == 'cheap' and model == 'gpt-4-32k':
        print(f'Your are going to spent about {cheap_gpt4_32k:.2f}$')

    confirmation = input("\nDo you want to continue with the program? (yes[y]/no[n]): ")

    if confirmation.lower() not in ("yes", 'y'):
        shutil.rmtree(target_dir) # Clean up the cloned repository
        print("Program terminated.")
        sys.exit(0)


    if total_words * 1.25 < 16000:
        detailed_repo_summary = True
    else:
        detailed_repo_summary = False

    return detailed_repo_summary
