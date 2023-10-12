import argparse
from distutils.util import strtobool
import os
import openai
import yaml
from clone_source import clone_source, copy_py_files
from summarize_repo import summarize_repo
from create_docstrings import create_docstrings
from insert_docstrings import insert_docstrings
from check_config import check_config
from cost_estimator import cost_estimator
import traceback


def main(source_path: str, cost: str, write_gpt_output: bool, max_lno, Model: str) -> None:
    """
    Orchestrates the process of generating and inserting docstrings into a given repository.
    
    This function performs the following steps:
    1. Clones the source code from the provided URL/path.
    2. Analyzes the repository.
    3. Generates docstrings for each Python file in the repository.
    4. Inserts the generated docstrings back into the respective files.
    5. If enabled, writes the generated docstrings into a separate file.
    
    Args:
        source_path (str): The URL/path of the GitHub repository to be analyzed and documented.
        cost (str, optional): The cost of the GPT model used for docstring generation. Defaults to 'expensive'.
        write_gpt_output (bool, optional): If True, writes the GPT output/docstrings into a separate file. 
            Defaults to True.
        detailed_repo_summary (bool, optional): If True, generates a detailed summary of the repository. 
            Defaults to True.
        max_lno (int, optional): The maximum number of lines to split the code. Defaults to 1200.
        Model (str, optional): The GPT model used for docstring generation. Defaults to 'gpt-4-32k'.
    
    Returns:
        None
    """
    # CHECK INPUT
    if max_lno == None:
        if Model == 'gpt-4-32k':
            max_lno = 1200
        elif Model == 'gpt-4':
            max_lno = 300

    # CLONE SOURCE
    target_dir = os.path.join(os.getcwd(), "edited_repository")
    clone_source(source_path, target_dir)
    path_dest = os.path.join(target_dir, 'gpt_output') #path to the gpt_output folder

    # ESTIMATE COSTS
    detailed_repo_summary = cost_estimator(max_lno = max_lno, target_dir = target_dir, model = Model, cost = cost) #also checks if combinded .md/.rst files are too long for gpt-3.5-16k


    # CHECK CONFIG
    check_config() #and get api_key


    # PRINT PARAMETERS
    print('Parameters:')
    print(f'    Source path: {source_path}')
    print(f'    cost: {cost}')
    print(f'    write gpt output: {write_gpt_output}')
    print(f'    detailed analysis/summary of repository: {detailed_repo_summary}')
    print(f'    max. snippet length: {max_lno} lines')
    print(f'    Model: {Model}')
        

    # INFO ABOUT REPOSITORY
    try:
        info_repo = summarize_repo(target_dir, Model='gpt-3.5-turbo-16k', detailed=detailed_repo_summary)
    except Exception:
        info_repo = summarize_repo(target_dir, Model='gpt-3.5-turbo-16k', detailed=False)


    # CREATE DOCSTRINGS
    print('\nAnalyzing files:')
    for root, dirs , files in os.walk(target_dir):
        if 'gpt_output' in dirs:
            dirs.remove('gpt_output') #exlude gpt_output folder from analysis
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                gpt_path = os.path.join(path_dest, os.path.relpath(file_path, target_dir))

                #in the next line the file is analyzed (if file > man_lno), docstrings are generated and saved in gpt_output (if enabled)
                docstrings = create_docstrings(file_path, additional_info=info_repo, 
                                              max_lno=max_lno, Model=Model, cost=cost,
                                              write_gpt_output=write_gpt_output, gpt_path=gpt_path)

                # inserts docstrings
                try:
                    insert_docstrings(file_path, docstrings) 
                except Exception as err:
                    print(f'    Error: {err}')
                    traceback.print_exc()
                    print('    Could not insert docstrings.')
                    print('    The file will be skipped.')
                    continue
                
    #also copy info_repo in gpt_output
    if write_gpt_output and info_repo != None:
        dest_path = os.path.join(target_dir, 'gpt_output')
        with open(os.path.join(dest_path, 'info_repo'), "w") as file:
            file.write(info_repo)


    print('\nFinished!')
    print('You can see your edited repository in the folder "edited_repository" of your current working directory')



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process repositories/folder/files and optional variables.")
    
    # Positional argument
    parser.add_argument("source_path", type=str, help="(GitHub_repository_URL/directory_path/file_path)\n  specify the source to be edited with docstrings")
    
    # Optional arguments
    parser.add_argument("--cost", type=str, default='expensive', help="('expensive'/'cheap'); expensive: always uses gpt-4-32k; cheap: uses gpt-3.5-turbo-16k for files < 300 lines and gpt-4-32k for files > 300 lines")
    parser.add_argument("--write_gpt_output", dest='write_gpt_output', type=lambda x: bool(strtobool(x)), default=True, help="(True/False); writes the GPT output/docstrings into a folder 'gpt-output' within the folder eddited repository ")
    parser.add_argument("--max_lno", type=int, help="(int_number); length [in lines] from which a code is split into snippets (max_lno is also approx. the length of the snippets)")
    parser.add_argument("--Model", type=str, default='gpt-4', help="(gpt-4-32k/gpt-4); gpt-model used for docstring generation (if cost = 'expensive' for all files, if cost = 'cheap' only for ones > 300 lines) ")

    args = parser.parse_args()
    
    main(
        args.source_path,
        cost=args.cost,
        write_gpt_output=args.write_gpt_output,
        max_lno=args.max_lno,
        Model=args.Model
    )
