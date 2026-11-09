from pathlib import Path
import re
import requests

HOME = Path.home()
TOOLS_URL = "https://ctueting.github.io/pymol_tools/tools.py"

OUTPUT_FILE = HOME / ".pymol_tools.py"
PYMOLRC_FILE = HOME / ".pymolrc"

BLOCK_START = "### PyMOL tools START ###"
BLOCK_END = "### PyMOL tools END ###"


def install(override=False, add_to_pymolrc=False):
    """Download PyMOL tools and optionally register them in .pymolrc."""

    # Fetch the tools index
    response = requests.get(TOOLS_URL, timeout=30)
    response.raise_for_status()

    # Extract URLs from quoted strings
    urls = re.findall(r"""["'](https?://[^"']+\.py)["']""", response.text)

    if not urls:
        print("ERROR: No Python tool URLs found.")
        return None

    # Check existing installation
    if OUTPUT_FILE.exists() and not override:
        print(f"ERROR: {OUTPUT_FILE} already exists. Use override=True.")
        return None

    # Download individual tools
    collected_tools = []

    for url in dict.fromkeys(urls):
        print(f"Downloading {url}")

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        collected_tools.append(response.text)

    # Save combined tools
    OUTPUT_FILE.write_text(
        "\n\n".join(collected_tools) + "\n",
        encoding="utf-8"
    )

    print(f"Installed: {OUTPUT_FILE}")

    # Optionally register in .pymolrc
    command = f"run {OUTPUT_FILE}"

    if add_to_pymolrc:
        content = (
            PYMOLRC_FILE.read_text(encoding="utf-8")
            if PYMOLRC_FILE.exists()
            else ""
        )

        block = f"{BLOCK_START}\n{command}\n{BLOCK_END}"

        if BLOCK_START in content and BLOCK_END in content:
            # Replace existing managed block
            content = re.sub(
                re.escape(BLOCK_START) + r".*?" + re.escape(BLOCK_END),
                lambda _: block,
                content,
                flags=re.DOTALL
            )
        elif command not in content.splitlines():
            # Append new block
            content = content.rstrip() + "\n\n" + block + "\n"

        PYMOLRC_FILE.write_text(content, encoding="utf-8")
        print(f"Updated: {PYMOLRC_FILE}")

    else:
        print(
            f"\nTo load automatically, add this line to your .pymolrc:\n"
            f"{command}\n\n"
            "Open File -> Edit pymolrc in PyMOL."
        )

    return OUTPUT_FILE
