from pathlib import Path

from .sentence_versions import generate_alternative_sentences, generate_versions
from .generate_to_simplify import generate_to_simplify
from .google_drive import download_drive, upload_to_drive


def sentencify(
    content_path,
    drive_ids,
    lang,
    mode="local",
    subs=None,
    l_colors=None,
):
    if not subs:
        subs = [
            "0 resources",
            "1 to_simplify",
            "2 simplified",
            "3 versions",
        ]

    path_ids = [(content_path / subs[i], drive_ids[i]) for i in range(len(drive_ids))]
    abort = prepare_folders(content_path, subs)  # prepare the folder structure
    if abort and mode == "local":
        print(
            'Exiting: "content" folder did not exist. Please add some files to segment and rerun.'
        )
        return

    if mode == "local":
        sentencify_local(path_ids, lang=lang, l_colors=l_colors)
    elif mode == "drive":
        sentencify_local(path_ids, lang=lang, l_colors=l_colors)
        upload_to_drive(drive_ids)
    elif mode == "download":
        download_drive(path_ids)
    elif mode == "upload":
        upload_to_drive(drive_ids)
    else:
        raise ValueError('either one of "local", "drive", "download" and "upload".')


def sentencify_local(path_ids, lang="bo", l_colors=None, basis_onto=None):
    state, resources = current_state(path_ids)
    new_files = []

    for file, steps in state.items():
        print(file)
        cur = 0
        # starting at step 2: segmented text. (segmentation should be done with corpus_segment.py
        while cur <= 3 and cur in steps and steps[cur]:
            cur += 1

        # 3. create .xlsx files in to_simplify from segmented .txt files from segmented
        if cur == 1:
            print("\tcreating file to simplify...")
            in_file = steps[cur - 1]
            out_file = path_ids[cur][0] / (
                in_file.stem.split("_")[0] + "_simplify.xlsx"
            )
            generate_to_simplify(
                in_file, out_file, resources, l_colors, basis_onto=basis_onto
            )
            new_files.append(out_file)

            # 8. manually process the .xlsx files in to_simplify
            print("\t--> Please manually simplify the sentences.")

        # 9. generate alternative sentences as _sents.xlsx files in simplified from .xlsx files in to_simplify
        elif cur == 2:
            print("\tgenerating the alternative sentences...")
            in_file = steps[cur - 1]
            out_file = path_ids[cur - 1][0] / (
                in_file.stem.split("_")[0] + "_sents.xlsx"
            )
            generate_alternative_sentences(
                in_file, out_file, lang, format="xlsx"
            )  # xlsx and docx are accepted
            new_files.append(out_file)

        # 10. Generate versions as _versions.docx in versions from .xlsx files in _simplified
        elif cur == 3:
            print("\tgenerating simplified versions")
            in_file = steps[cur - 1]
            out_file = path_ids[cur - 1][0] / (
                in_file.stem.split("_")[0] + "_versions.docx"
            )
            generate_versions(in_file, out_file, lang, format=True)
            new_files.append(out_file)

        else:
            print("\tfile processed.")

    write_to_upload(new_files)


def current_state(paths_ids):
    file_type = {
        "1 to_simplify": ".xlsx",
        "2 simplified": ".xlsx",
        "3 versions": ".docx",
    }

    resources = {p.stem.split('_')[0]: p for p in paths_ids[0][0].glob('*.yaml')}
    initial = {p.stem.split('_')[0]: p for p in paths_ids[0][0].glob('*.xlsx')}
    intersect = resources.keys() & initial.keys()
    state = {e: {i: None for i in range(0, len(paths_ids) + 1)} for e in intersect}
    for stem, file_ in initial.items():
        state[stem][0] = file_

    for path, _ in paths_ids[1:]:
        for f in path.glob("*"):
            if f.suffix != file_type[path.stem]:
                continue
            # add file to state
            stem = f.stem.split("_")[0]
            if stem not in state:
                state[stem] = {i: None for i in range(2, len(paths_ids) + 1)}
            step = int(f.parts[1][0])
            state[stem][step] = f

    return state, resources


def write_to_upload(files):
    file = Path("to_upload.txt")
    if not file.is_file():
        file.write_text("")

    content = file.read_text().strip().split("\n")
    files = [str(f) for f in files]
    for f in files:
        if f not in content:
            content.append(f)

    file.write_text("\n".join(content))


def prepare_folders(content_path, sub_folders):
    missing = False
    if not content_path.is_dir():
        missing = True
        print(f'folder "{content_path}" does not exist. Creating it...')
        content_path.mkdir()
    for sub in sub_folders:
        if not (content_path / sub).is_dir():
            print(f'folder "{(content_path / sub)}" does not exist. Creating it...')
            (content_path / sub).mkdir()
    return missing
