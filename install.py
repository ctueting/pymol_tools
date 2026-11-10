from pathlib import Path
from urllib.request import urlopen
import re

HOME = Path.home()
TOOLS_URL = "https://ctueting.github.io/pymol_tools/tools.py"

OUTPUT_FILE = HOME / ".pymol_tools.py"
PYMOLRC_FILE = HOME / ".pymolrc"

BLOCK_START = "### PyMOL tools START ###"
BLOCK_END = "### PyMOL tools END ###"


def download(url):
    """Download a UTF-8 text file using Python's standard library."""
    with urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8")


def install(override=False, add_to_pymolrc=False):
    """Download PyMOL tools and optionally register them in .pymolrc."""

    # Check existing installation
    if OUTPUT_FILE.exists() and not override:
        print(
            f"ERROR: {OUTPUT_FILE} already exists.\n"
            "Use install(True) to overwrite."
        )
        return None

    # Fetch the tools index
    try:
        code = download(TOOLS_URL)
    except Exception as e:
        print(f"ERROR: Could not download tools index: {e}")
        return None

    # Extract Python script URLs
    urls = re.findall(
        r"""["'](https?://[^"']+\.py)["']""",
        code
    )

    urls = list(dict.fromkeys(urls))

    if not urls:
        print("ERROR: No Python tool URLs found.")
        return None

    # Download individual tools
    collected_tools = []

    try:
        for url in urls:
            print(f"Downloading: {url}")
            collected_tools.append(download(url))

    except Exception as e:
        print(f"ERROR: Download failed: {e}")
        return None

    # Save combined tools
    try:
        OUTPUT_FILE.write_text(
            "\n\n".join(collected_tools) + "\n",
            encoding="utf-8"
        )
    except OSError as e:
        print(f"ERROR: Could not write {OUTPUT_FILE}: {e}")
        return None

    print(f"Installed: {OUTPUT_FILE}")

    # Run the code immediatelly, so the User does not need to restart PyMOL. This is independent of writing the command in the pymolrc file
    cmd.run(str(OUTPUT_FILE))

    # Optionally register in .pymolrc
    command = f"run {OUTPUT_FILE}"

    if add_to_pymolrc:
        try:
            content = (
                PYMOLRC_FILE.read_text(encoding="utf-8")
                if PYMOLRC_FILE.exists()
                else ""
            )

            block = (
                f"{BLOCK_START}\n"
                f"{command}\n"
                f"{BLOCK_END}"
            )

            if BLOCK_START in content and BLOCK_END in content:
                # Replace existing managed block
                content = re.sub(
                    re.escape(BLOCK_START)
                    + r".*?"
                    + re.escape(BLOCK_END),
                    lambda _: block,
                    content,
                    flags=re.DOTALL
                )

            elif command not in content.splitlines():
                # Append new managed block
                content = content.rstrip() + "\n\n" + block + "\n"

            PYMOLRC_FILE.write_text(
                content,
                encoding="utf-8"
            )

            print(f"Updated: {PYMOLRC_FILE}")

        except OSError as e:
            print(f"ERROR: Could not update .pymolrc: {e}")
            return OUTPUT_FILE

    else:
        print(
            "\nTo load the tools automatically, add this line "
            "to your .pymolrc:\n\n"
            f"{command}\n\n"
            "Open File -> Edit pymolrc in PyMOL."
        )

    return OUTPUT_FILE
