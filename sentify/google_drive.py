import os
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

    def download_folder(self, name, id):
        c_path = Path(name)
        if c_path.is_dir():
            shutil.rmtree(c_path)
        if not c_path.is_dir():
            c_path.mkdir(parents=True, exist_ok=True)

        file_list = self.drive.ListFile({'q': f"'{id}' in parents and trashed=false"}).GetList()
        for file in file_list:
            if file['mimeType'].endswith('document'):
                file.GetContentFile(c_path / (file['title'] + '.txt'), mimetype='text/plain')
            else:
                print('')
                file.GetContentFile(c_path / (file['title'] + '.xlsx'), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


class PushDriveFiles:
    def __init__(self):
        self.drive = self.__login()

    @staticmethod
    def __login():
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()  # client_secrets.json need to be in the same directory as the script
        return GoogleDrive(gauth)

    def push_files(self, files_list):
        for folder, file in files_list:
            print(f'uploading {file}')
            params = {'title': file.stem}

            if file.suffix == '.xlsx':
                params['mimeType'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif file.suffix == '.txt':
                params['mimeType'] = 'text/plain'
            elif file.suffix == '.docx':
                params['mimeType'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                print(f'{file}\nfile format not supported for upload.')
                continue

            docs_list = self.drive.ListFile({'q': f"'{folder}' in parents and trashed=false"}).GetList()
            for f in docs_list:
                if f['title'] == file.stem:
                    params['id'] = f['id']

            if 'id' not in params:
                params['parents'] = [{'id': folder}]

            drive_file = self.drive.CreateFile(params)
            drive_file.SetContentFile(file)
            drive_file.Upload(param={'convert': True})
