import yaml
from pathlib import Path

from .sentencify import sentencify
from .drive import upload_to_drive


def sentify():
    mode, lang, content, driver_folders, level_colors = read_config()
    content = Path(content)
    if mode == "local":
        sentencify(content, driver_folders, lang, mode=mode, l_colors=level_colors)
    elif mode == "drive":
        sentencify(content, driver_folders, lang, mode=mode, l_colors=level_colors)
    elif mode == "upload":
        upload_to_drive(driver_folders)


def read_config():
    default = """# "local", "drive" or "upload"
mode: local
# "bo" and "en" are currently supported 
lang: bo
# the relative path to the folder containing the 5 folders of the data
input: content
# Google Drive folder ids.
# add the ids right after each "- ". keep the order from 1 to 5 from the drive folders
# to find the id, open the folder, take everything following the last "/" in the url
drive_folders: 
- 
- 
- 
- 
- """
    in_file = Path("config.yaml")
    if not in_file.is_file():
        print("No config file, creating it.\n" 'Please review "config.yaml"\n')
        in_file.write_text(default)

    struct = yaml.safe_load(in_file.read_text())
    return (
        struct["mode"],
        struct["lang"],
        struct["input"],
        struct["drive_folders"],
        struct["level_colors"],
    )


__all__ = {sentify}
