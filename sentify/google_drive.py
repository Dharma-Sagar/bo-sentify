from pathlib import Path
import shutil
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


class RetrieveDriveFiles:
    def __init__(self):
        self.drive = self.__login()

    @staticmethod
    def __login():
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()  # client_secrets.json need to be in the same directory as the script
        return GoogleDrive(gauth)

    def download_content(self, name, id):
        c_path = Path(name)
        if c_path.is_dir():
            shutil.rmtree(c_path)
        if not c_path.is_dir():
            c_path.mkdir()

        file_list = self.drive.ListFile({'q': f"'{id}' in parents and trashed=false"}).GetList()
        for file in file_list:
            if 'spreadsheet' in file.attr['metadata']['mimeType']:
                file.GetContentFile(f'{name}/{file["title"]}.tsv', mimetype='text/tab-separated-values')
            else:
                file.GetContentFile(f'{name}/{file["title"]}.txt', mimetype='text/plain')
