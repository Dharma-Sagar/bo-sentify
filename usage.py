from pathlib import Path
import yaml

from sentify import generate_alternative_sentences, Tokenizer, generate_xlsx, generate_versions
from sentify import RetrieveDriveFiles, PushDriveFiles


def prepare_folders(content_path, sub_folders):
    if not content_path.is_dir():
        content_path.mkdir()
    for sub in sub_folders:
        if not (content_path / sub).is_dir():
            (content_path / sub).mkdir()


def current_state(paths_ids):
    state = {}
    for path, _ in paths_ids:
        for f in path.glob('*'):
            stem = f.stem.split('_')[0]
            if stem not in state:
                state[stem] = {1: None, 2: None, 3: None, 4: None}
            step = int(f.parts[1][0])
            state[stem][step] = f
    return state


def sentify_local(path_ids, lang='bo'):
    state = current_state(path_ids)
    new_files = []
    T = Tokenizer(lang=lang)
    tok = None

    for file, steps in state.items():
        print(file)
        cur = 1
        while cur <= 4 and steps[cur]:
            cur += 1

        # 1. tokenize .txt files in to_segment, tokenized are in segmented as _segmented.txt files
        if cur == 2:
            print('\tsegmenting...')
            if not tok:
                tok = T.set_tok()

            in_file = steps[cur-1]
            out_file = path_ids[cur-1][0] / (in_file.stem + '_segmented.txt')
            T.tok_file(tok, in_file, out_file)
            new_files.append(out_file)

        # 2. manually correct the segmentation
            print('\t--> Please manually correct the segmentation.')

        # 3. create .xlsx files in to_simplify from segmented .txt files from segmented
        elif cur == 3:
            print('\tcreating file to simplify...')
            in_file = steps[cur-1]
            out_file = path_ids[cur-1][0] / (in_file.stem.split('_')[0] + '.xlsx')
            generate_xlsx(in_file, out_file)
            new_files.append(out_file)

        # 4. manually process the .xlsx files in to_simplify
            print('\t--> Please manually simplify the sentences.')

        # 5. generate alternative sentences as _sents.xlsx files in simplified from .xlsx files in to_simplify
        elif cur == 4:
            print('\tgenerating the alternative sentences...')
            in_file = steps[cur-1]
            out_file = path_ids[cur - 1][0] / (in_file.stem.split('_')[0] + '_sents.xlsx')
            generate_alternative_sentences(in_file, out_file, lang, format='xlsx')  # xlsx and docx are accepted
            new_files.append(out_file)

        # 6. Generate versions as _versions.docx in versions from .xlsx files in _simplified
        elif cur == 5:
            print('\tgenerating simplified versions')
            in_file = steps[cur-1]
            out_file = path_ids[cur - 1][0] / (in_file.stem.split('_')[0] + '_versions.docx')
            generate_versions(in_file, out_file, lang)
            new_files.append(out_file)

        else:
            print('\tfile processed.')

    write_to_upload(new_files)


def write_to_upload(files):
    file = Path('to_upload.txt')
    if not file.is_file():
        file.write_text('')

    content = file.read_text().strip().split('\n')
    files = [str(f) for f in files]
    for f in files:
        if f not in content:
            content.append(f)

    file.write_text('\n'.join(content))


def download_drive(path_ids):
    get = RetrieveDriveFiles()

    for sub, id in path_ids:
        get.download_folder(sub, id)


def sentify(content_path, drive_ids, lang, mode='drive', subs=None):
    if not subs:
        subs = ['1 to_segment', '2 segmented', '3 to_simplify', '4 simplified', '5 versions']

    path_ids = [(content_path / subs[i], drive_ids[i]) for i in range(5)]
    prepare_folders(content_path, subs)  # prepare the folder structure

    if mode == 'local':
        sentify_local(path_ids, lang=lang)
    elif mode == 'drive':
        download_drive(path_ids)
        sentify_local(path_ids, lang=lang)
    else:
        raise ValueError('either "local" or "drive"')


def upload_to_drive(driver_folders):
    to_upload_file = Path('to_upload.txt')
    files_list = to_upload_file.read_text().strip().split('\n')
    files_list = [Path(f) for f in files_list]
    to_upload = []
    for f in files_list:
        if f.parts[1] == '2 segmented':
            to_upload.append((driver_folders[1], f))
        elif f.parts[1] == '3 to_simplify':
            to_upload.append((driver_folders[2], f))
        elif f.parts[1] == '4 simplified':
            to_upload.append((driver_folders[3], f))
        elif f.parts[1] == '5 versions':
            to_upload.append((driver_folders[4], f))

    pf = PushDriveFiles()
    pf.push_files(to_upload)
    to_upload_file.unlink()


def read_config():
    default = '''# "local", "drive" or "upload"
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
- '''
    in_file = Path('config.yaml')
    if not in_file.is_file():
        print('No config file, creating it.\n'
              'Please review "config.yaml"\n')
        in_file.write_text(default)

    struct = yaml.safe_load(in_file.read_text())
    return struct['mode'], struct['lang'], struct['input'], struct['drive_folders']


def main():
    mode, lang, content, driver_folders = read_config()
    content = Path(content)
    if mode == 'local':
        sentify(content, driver_folders, lang, mode=mode)
    elif mode == 'drive':
        sentify(content, driver_folders, lang, mode=mode)
    elif mode == 'upload':
        upload_to_drive(driver_folders)


if __name__ == '__main__':
    main()
