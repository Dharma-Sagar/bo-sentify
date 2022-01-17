import re

import yaml
from pathlib import Path

from .sentence_versions import generate_alternative_sentences, generate_versions
from .corpus_segment import Tokenizer
from .generate_to_simplify import generate_to_simplify
from .google_drive import RetrieveDriveFiles, PushDriveFiles
from .onto.leavedonto import LeavedOnto
from .dataval import DataVal
from .generate_to_tag import generate_to_tag


def create_onto(in_file, out_file):
    template = "legend: [lemma, level1, level2, level3]\nont:\n  to organize:\n"
    dump = in_file.read_text().replace('\n', ' ').lstrip('\ufeff').strip()
    dump = re.sub(r' +', ' ', dump)
    words = dump.split(' ')
    ont = '\n'.join([f'  - ["{w}"]' for w in words])
    ont = yaml.safe_load(template + ont)
    lo = LeavedOnto(ont, out_file)
    lo.convert2yaml()


def prepare_folders(content_path, sub_folders):
    if not content_path.is_dir():
        content_path.mkdir()
    for sub in sub_folders:
        if not (content_path / sub).is_dir():
            (content_path / sub).mkdir()


def current_state(paths_ids):
    state = {}
    # leaving aside "O resources"
    for path, _ in paths_ids[1:]:
        for f in path.glob('*'):
            stem = f.stem.split('_')[0]
            if stem not in state:
                state[stem] = {1: None, 2: None, 3: None, 4: None}
            step = int(f.parts[1][0])
            state[stem][step] = f

    resources = {f.stem.split('_')[0]: f for f in paths_ids[0][0].glob('*.yaml')}
    return state, resources


def sentify_local(path_ids, lang='bo', l_colors=None):
    state, resources = current_state(path_ids)
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
            out_file = path_ids[cur][0] / (in_file.stem + '_segmented.txt')
            T.tok_file(tok, in_file, out_file)
            new_files.append(out_file)

        # 2. manually correct the segmentation
            print('\t--> Please manually correct the segmentation.')

        # 3. create the _totag.xlsx in to_tag from the segmented .txt file from segmented
        elif cur == 3:
            print('\ncreating the file to tag...')
            # TODO: merge the base onto and all the ones from individual files, only add data validation to new words.
            in_file = steps[cur-1]
            out_file = path_ids[cur][0] / (in_file.stem.split('_')[0] + '_totag.xlsx')
            if not out_file.is_file():
                generate_to_tag(in_file, out_file, resources, l_colors=l_colors)

        # 4. manually POS tag the segmented text
            print('\t--> Please manually tag new words with their POS tag and level.')

        # 5. create .xlsx files in to_simplify from segmented .txt files from segmented
        elif cur == 4:
            print('\t creating the onto from the tagged file...')
            in_file = steps[cur-1]
            out_file = Path('content/0 resources') / (in_file.stem.split('_')[0] + '_onto.yaml')
            if not out_file.is_file():
                create_onto(in_file, out_file)

            print('\tcreating file to simplify...')
            in_file = steps[cur-1]
            out_file = path_ids[cur][0] / (in_file.stem.split('_')[0] + '.xlsx')
            generate_to_simplify(in_file, out_file, resources)
            new_files.append(out_file)

        # 6. manually process the .xlsx files in to_simplify
            print('\t--> Please manually simplify the sentences.')

        # 7. generate alternative sentences as _sents.xlsx files in simplified from .xlsx files in to_simplify
        elif cur == 5:
            print('\tgenerating the alternative sentences...')
            in_file = steps[cur-1]
            out_file = path_ids[cur][0] / (in_file.stem.split('_')[0] + '_sents.xlsx')
            generate_alternative_sentences(in_file, out_file, lang, format='xlsx')  # xlsx and docx are accepted
            new_files.append(out_file)

        # 8. Generate versions as _versions.docx in versions from .xlsx files in _simplified
        elif cur == 6:
            print('\tgenerating simplified versions')
            in_file = steps[cur-1]
            out_file = path_ids[cur][0] / (in_file.stem.split('_')[0] + '_versions.docx')
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


def sentencify(content_path, drive_ids, lang, mode='drive', subs=None, l_colors=None):
    if not subs:
        subs = ['0 resources', '1 to_segment', '2 segmented', '3 to_tag',
                '4 to_simplify', '5 simplified', '6 versions']

    path_ids = [(content_path / subs[i], drive_ids[i]) for i in range(6)]
    prepare_folders(content_path, subs)  # prepare the folder structure

    if mode == 'local':
        sentify_local(path_ids, lang=lang, l_colors=l_colors)
    elif mode == 'drive':
        download_drive(path_ids)
        sentify_local(path_ids, lang=lang, l_colors=l_colors)
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
        elif f.parts[1] == '3 to_tag':
            to_upload.append((driver_folders[2], f))
        elif f.parts[1] == '4 to_simplify':
            to_upload.append((driver_folders[3], f))
        elif f.parts[1] == '5 simplified':
            to_upload.append((driver_folders[4], f))
        elif f.parts[1] == '6 versions':
            to_upload.append((driver_folders[5], f))

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
    return struct['mode'], struct['lang'], struct['input'], struct['drive_folders'], struct['level_colors']


def sentify():
    mode, lang, content, driver_folders, level_colors = read_config()
    content = Path(content)
    if mode == 'local':
        sentencify(content, driver_folders, lang, mode=mode, l_colors=level_colors)
    elif mode == 'drive':
        sentencify(content, driver_folders, lang, mode=mode, l_colors=level_colors)
    elif mode == 'upload':
        upload_to_drive(driver_folders)
