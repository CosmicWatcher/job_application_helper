import os
import re
import subprocess
from datetime import datetime

from config import ROOT_PATH
from utils import print_error


def parse_resume_latex(resume_path):
    """
    Parse the resume.tex file to extract job experience items.

    Returns a chronological list of jobs containing a dictionary
    with job titles as keys and lists of items as values.
    """
    with open(resume_path, "r") as file:
        content = file.read()

    # Find the Experience section
    experience_section = re.search(
        r"\\section\*\{Experience\}(.*?)\\section\*", content, re.DOTALL
    )
    if not experience_section:
        print_error(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error: Could not find Experience section in resume.tex"
        )
        return []

    experience_content = experience_section.group(1)

    # Extract job blocks
    job_blocks = re.findall(
        r"\\textbf\{(.*?)\}.*?\\begin\{itemize\}(.*?)\\end\{itemize\}",
        experience_content,
        re.DOTALL,
    )

    jobs = []
    for job_title, items_block in job_blocks:
        # Clean up job title (remove trailing comma and any location/date info)
        job_title = job_title.split(",")[0].strip()

        # Extract items
        items = re.findall(r"\\item\s+(.*?)(?=\\item|\s*$)", items_block, re.DOTALL)
        # Clean up items (remove newlines and extra spaces)
        items = [re.sub(r"\s+", " ", item).strip() for item in items]

        jobs.append({job_title: items})

    return jobs


def generate_resume_pdf(resume_path, selected_items):
    """
    Generate a PDF version of the resume.

    Returns the path to the generated PDF file.
    """
    resume_root = os.path.dirname(resume_path)

    # Get the original resume content
    with open(resume_path, "r") as file:
        content = file.read()

    # Parse selected items into a dictionary of job titles and items
    selected_job_items = {}
    for selected in selected_items:
        parts = selected.split(":", 1)
        if len(parts) == 2:
            job_title, item = parts
            # Clean up item text - escape any unescaped percent symbols
            item = re.sub(r"(?<!\\)%", r"\\%", item)
            if job_title not in selected_job_items:
                selected_job_items[job_title] = []
            selected_job_items[job_title].append(item)

    print(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Parsed selected job items: {selected_job_items}"
    )

    # Find the Experience section
    experience_section = re.search(
        r"(\\section\*\{Experience\})(.*?)(\\section\*)", content, re.DOTALL
    )
    if not experience_section:
        raise Exception("Could not find Experience section in resume")

    section_start = experience_section.group(1)
    original_section_content = experience_section.group(2)
    section_end = experience_section.group(3)

    # Create a new section content with only the selected jobs and items
    new_section_content = ""

    # Extract job blocks from the original content
    job_blocks = re.findall(
        r"(\\textbf\{(.*?)\}.*?\\begin\{itemize\})(.*?)(\\end\{itemize\})",
        original_section_content,
        re.DOTALL,
    )

    for full_header, job_title_with_info, items_content, end_tag in job_blocks:
        # Extract the job title (remove trailing comma and any location/date info)
        job_title = job_title_with_info.split(",")[0].strip()

        # Check if this job has any selected items
        if job_title in selected_job_items:
            # Start building this job block
            new_job_block = full_header

            # Add only the selected items for this job
            for item in selected_job_items[job_title]:
                # Make sure the item has the \item prefix
                if not item.strip().startswith("\\item"):
                    item = "\\item " + item.strip()
                new_job_block += item + "\n"

            # Add the end tag
            new_job_block += end_tag

            # Add this job block to the new section content
            new_section_content += new_job_block

    # Reconstruct the content
    new_content = content.replace(
        experience_section.group(0),
        section_start + new_section_content + section_end,
    )

    # Add \vspace{-18.5pt} before the Education section
    if "\\section*{Education}" in new_content:
        new_content = new_content.replace(
            "\\section*{Education}", "\\vspace{-18.5pt}\n\\section*{Education}"
        )

    resume_tmp_path = os.path.join(resume_root, "tmp.tex")
    with open(resume_tmp_path, "w") as file:
        file.write(new_content)

    # Compile to PDF
    try:
        result = subprocess.run(
            [
                "pdflatex",
                "-output-directory=" + resume_root,
                resume_tmp_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,  # Add a timeout to prevent hanging
        )

        if result.returncode != 0:
            raise Exception("Error converting LaTeX to PDF: " + result.stderr)

        # Path to the generated PDF
        pdf_path = os.path.join(resume_root, "tmp.pdf")

        # Ensure the static directory exists
        static_dir = os.path.join(
            ROOT_PATH,
            "src",
            "static",
        )
        os.makedirs(static_dir, exist_ok=True)

        # Create a symlink to the PDF in the static directory for serving
        static_pdf_path = os.path.join(static_dir, "resume.pdf")
        if not os.path.exists(static_pdf_path):
            os.symlink(pdf_path, static_pdf_path)
            print(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - PDF symlink created at: {static_pdf_path}"
            )

        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - PDF generated at: {pdf_path}"
        )

        return static_pdf_path

    except subprocess.TimeoutExpired:
        raise Exception(
            "Timeout while converting LaTeX to PDF. The process took too long."
        )
    except FileNotFoundError:
        raise Exception(
            "pdflatex command not found. Please make sure LaTeX is installed."
        )
