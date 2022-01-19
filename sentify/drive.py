from pathlib import Path

from .google_drive import RetrieveDriveFiles, PushDriveFiles


def download_drive(path_ids):
    get = RetrieveDriveFiles()

    for sub, id_ in path_ids:
        get.download_folder(sub, id_)


def upload_to_drive(driver_folders):
    to_upload_file = Path("to_upload.txt")
    files_list = to_upload_file.read_text().strip().split("\n")
    files_list = [Path(f) for f in files_list]
    to_upload = []
    for f in files_list:
        if f.parts[1] == "2 segmented":
            to_upload.append((driver_folders[1], f))
        elif f.parts[1] == "3 to_tag":
            to_upload.append((driver_folders[2], f))
        elif f.parts[1] == "4 vocabulary":
            to_upload.append((driver_folders[3], f))
        elif f.parts[1] == "5 to_simplify":
            to_upload.append((driver_folders[4], f))
        elif f.parts[1] == "6 simplified":
            to_upload.append((driver_folders[5], f))
        elif f.parts[1] == "7 versions":
            to_upload.append((driver_folders[6], f))

    pf = PushDriveFiles()
    pf.push_files(to_upload)
    to_upload_file.unlink()
