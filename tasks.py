# tasks.py
"""
An invoke script to run build tasks for the book

invoke build website # this builds the mkdocs website website
 -- then cd into website directory and run mkdocs serve to view

invoke build pdf # this will eventually output a pdf/.tex file to complile with LaTeX to build a pdf
 -- then cd into pdf directory and use MikTek or other LaTeX complier to output a .pdf

"""

from pathlib import Path
from shutil import copyfile, rmtree, copytree
from os import chdir, getcwd, listdir
import os
import re
import sys

from invoke import task
import nbformat
from nbformat import NotebookNode
from nbconvert import LatexExporter
from nbconvert.writers import FilesWriter
from nbconvert.preprocessors import RegexRemovePreprocessor
from pandocfilters import applyJSONFilters, RawInline


@task
def build(c):
    """
    a task to house the build command
    """
    print("Building...")
    print()


@task
def website(c):
    """
    a task to build an mkdocs website from the src notebooks
    """
    print("Building mkdocs website from src notebooks...")
    if Path("website").is_dir():
        print("Found website directory, deleting...")
        rmtree("website")
    print("Creating empty website directory...")
    Path("website").mkdir(parents=True, exist_ok=True)
    mkdocs_config_template = Path("templates", "mkdocs", "mkdocs.yml")
    mkdocs_build_config = Path("website", "mkdocs.yml")
    preamble_template = Path("templates", "mkdocs", "preamble.py")
    preamble_file = Path("website", "preamble.py")
    print("Copying mkdocs.yml and preamble.py from templates/mkdocs/ to website/")
    copyfile(mkdocs_config_template, mkdocs_build_config)
    copyfile(preamble_template, preamble_file)
    print("Copying src/ into website/docs/")
    copytree(Path("src"), Path("website", "docs"))
    print("Changing to website directory")
    chdir("website")
    print(f"Current working directory {getcwd()}")
    print("running mkdocs build...")
    print()
    c.run("mkdocs build")


@task
def pdf(c):
    """
    a task to build a LaTeX .tex doc from the src notebooks
    """
    print("Building LaTeX .tex doc from src/ notebooks...")
    # create empty pdf/ and pdf/images/ directories
    make_empty_dir("pdf")
    print("Copying all images from src/subdir/images/ to pdf/images/")
    src_dir_path = Path("src")
    dest_images_dir_path = Path("pdf", "images")
    # copy all images from src/subdirs/images/ to pdf/images/
    copy_all_images(src_dir_path, dest_images_dir_path)
    # Build a list of all of the notebook paths.
    print("Creating a list of all notebook paths")
    nb_path_lst = iter_notebook_paths(src_dir_path)
    # merge all of the notebooks into one big notebook node.
    print("Merging all notebooks into one big notebook...")
    nbnode = merge_notebooks(nb_path_lst)
    # export notebook node into a .tex file using templates
    output_file_path = Path(os.getcwd(), "pdf", "out.tex")
    template_file_path = Path(os.getcwd(), "templates", "latex", "book38.tplx")
    print("Attempting to produce a .tex file from the big combined notebook...")
    export_tex(nbnode, output_file_path, template_file_path)
    # modify TOC in .tex file so that chapter numbering works
    convert_TOC(output_file_path)
    # copy the copywrite and dedication page .tex files to the pdf/ dir
    f_names = ["copywrite_page.tex", "dedication_page.tex"]
    for f_name in f_names:
        copyfile(
            Path(os.getcwd(), "templates", "latex", f_name),
            Path(os.getcwd(), "pdf", f_name),
        )
        print(f"Coppied {f_name} to pdf/ directory")
    # Print the final output
    print(
        f"Conversion complete.... \n Find the exported .tex file in: \n {output_file_path}"
    )


def convert_TOC(output_file_path: Path):
    pass


def export_tex(
    combined_nb_node: NotebookNode, output_file_path: Path, template_file_path=None
):
    resources = {}
    resources["unique_key"] = "combined"
    resources["output_files_dir"] = "combined_files"
    exporter = MyLatexExporter()
    if template_file_path is not None:
        exporter.template_file = str(template_file_path)
    mypreprocessor = RegexRemovePreprocessor()
    mypreprocessor.patterns = ["\s*\Z"]
    exporter.register_preprocessor(mypreprocessor, enabled=True)
    writer = FilesWriter(build_directory=str(output_file_path.parent))
    output, resources = exporter.from_notebook_node(combined_nb_node, resources)
    writer.write(output, resources, notebook_name=output_file_path.stem)


def convert_link(key, val, fmt, meta):
    if key == "Link":
        target = val[2][0]
        # Links to other notebooks
        m = re.match(r"(\d+\-.+)\.ipynb$", target)
        if m:
            return RawInline("tex", "Chapter \\ref{sec:%s}" % m.group(1))

        # Links to sections of this or other notebooks
        m = re.match(r"(\d+\-.+\.ipynb)?#(.+)$", target)
        if m:
            # pandoc automatically makes labels for headings.
            label = m.group(2).lower()
            label = re.sub(r"[^\w-]+", "", label)  # Strip HTML entities
            return RawInline("tex", "Section \\ref{%s}" % label)

    # Other elements will be returned unchanged.


def convert_links(source):
    return applyJSONFilters([convert_link], source)


class MyLatexExporter(LatexExporter):
    def default_filters(self):
        yield from super().default_filters()
        yield ("resolve_references", convert_links)


def copy_all_images(source_dir_path, dest_images_dir_path):
    """
    a function to copy all the images from a main source dir that has sub dirs with images
    to a dest dir
    """
    REG_nb_dir = re.compile((r"(\d\d)-*"))
    REG_img_filename = re.compile(
        (r"([/|.|\w|\s|-])*\.(?:jpg|gif|png|tiff|jpeg|tif|pdf)")
    )

    if dest_images_dir_path.is_dir():
        print(f"Found {dest_images_dir_path} directory, deleting")
        rmtree(dest_images_dir_path)
    print(f"Creating empty {dest_images_dir_path} directory...")
    dest_images_dir_path.mkdir(parents=True, exist_ok=True)

    for sub_dir in listdir(source_dir_path):
        if REG_nb_dir.match(sub_dir):
            if os.path.exists(os.path.join(source_dir_path, sub_dir, "images")):
                sub_dir_path = Path(source_dir_path, sub_dir, "images")
                for f in os.listdir(sub_dir_path):
                    try:
                        if REG_img_filename.match(f):
                            copyfile(
                                Path(sub_dir_path, f), Path(dest_images_dir_path, f)
                            )
                            print(f"coppied image file {f}")
                    except IOError as e:
                        print(f"Unable to copy file. {f}")
                        exit(1)
                    except:
                        print("Unexpected error:", sys.exc_info())
                        exit(1)


def merge_notebooks(nb_path_lst):
    """
    a function that creates a single notebook node object from a list of notebook file paths
    :param filename_lst: lst, a list of .ipynb file paths
    :return: a single notebookNode object
    """
    merged = None
    for fname in nb_path_lst:
        with open(fname, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)
        if merged is None:
            merged = nb
        else:
            merged.cells.extend(nb.cells)
    if not hasattr(merged.metadata, "name"):
        merged.metadata.name = ""
    merged.metadata.name += "_merged"
    # print(nbformat.writes(merged))
    return merged


def iter_notebook_paths(src_dir_path):
    REG_nb = re.compile(r"(\d\d)-(\d\d)-(.*)\.ipynb")
    REG_nb_dir = re.compile((r"(\d\d)-*"))
    nb_path_lst = []

    for sub_dir in listdir(src_dir_path):
        if REG_nb_dir.match(sub_dir):
            sub_dir_path = Path(src_dir_path, sub_dir)
            print(f"identified sub dir {sub_dir_path}")
            for f in os.listdir(sub_dir_path):
                if REG_nb.match(f):
                    nb_path_lst.append(Path(sub_dir_path, f))
                    print(f"added {f} to source notebook path list")
    return sorted(nb_path_lst)


def make_empty_dir(new_dir_name):
    """
    a function to create a new empty directory relative to the current working directory
    input:
        new_dir_name: string
    """
    if Path(new_dir_name).is_dir():
        print(f"Found {new_dir_name} directory, deleting...")
        rmtree(new_dir_name)
    print(f"Creating empty {new_dir_name} directory...")
    Path(new_dir_name).mkdir(parents=True, exist_ok=True)
