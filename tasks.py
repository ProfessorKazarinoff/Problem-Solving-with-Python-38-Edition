# tasks.py
"""
An invoke script to run build tasks for the book

invoke build # this builds the mkdocs website website

then cd into website directory and run mkdocs serve to view
"""

from invoke import task
from pathlib import Path
from shutil import copyfile, rmtree, copytree
from os import chdir, getcwd

@task
def build(c):
    """
    a task to build an mkdocs website from the src notebooks
    """
    print("Building...")
    if Path('website').is_dir():
        print("Found website directory, deleting...")
        rmtree('website')
    print("Creating empty website directory...")
    Path('website').mkdir(parents=True, exist_ok=True)
    mkdocs_config_template = Path('templates','mkdocs','mkdocs.yml')
    mkdocs_build_config = Path('website','mkdocs.yml')
    preamble_template = Path('templates','mkdocs','preamble.py')
    preamble_file = Path('website','preamble.py')
    print("Copying mkdocs.yml and preamble.py from templates/mkdocs/ to website/")
    copyfile(mkdocs_config_template,mkdocs_build_config)
    copyfile(preamble_template,preamble_file)
    print("Copying src/ into website/docs/")
    copytree(Path('src'),Path('website','docs'))
    print("Changing to website directory")
    chdir('website')
    print(f'Current working directory {getcwd()}')
    print("running mkdocs build...")
    print()
    c.run("mkdocs build")
