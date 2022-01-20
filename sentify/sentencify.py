from pathlib import Path

from .sentence_versions import generate_alternative_sentences, generate_versions
from .corpus_segment import Tokenizer
from .generate_to_simplify import generate_to_simplify
from .generate_to_tag import generate_to_tag
from .onto_from_tagged import onto_from_tagged
from .drive import download_drive


def sentencify(content_path, drive_ids, lang, mode="local", subs=None, l_colors=None, basis_onto=None):
    if not subs:
        subs = [
            "1 to_segment",
            "2 segmented",
            "3 to_tag",
            "4 vocabulary",
            "5 to_simplify",
            "6 simplified",
            "7 versions",
        ]

    path_ids = [(content_path / subs[i], drive_ids[i]) for i in range(len(drive_ids))]
    prepare_folders(content_path, subs)  # prepare the folder structure

    if mode == "local":
        sentencify_local(path_ids, lang=lang, l_colors=l_colors, basis_onto=basis_onto)
    elif mode == "drive":
        download_drive(path_ids)
        sentencify_local(path_ids, lang=lang, l_colors=l_colors, basis_onto=basis_onto)
    else:
        raise ValueError('either "local" or "drive"')


def sentencify_local(path_ids, lang="bo", l_colors=None, basis_onto=None):
    state, resources = current_state(path_ids)
    new_files = []
    T = Tokenizer(lang=lang)
    tok = None

    for file, steps in state.items():
        print(file)
        cur = 2
        # starting at step 2: segmented text. (segmentation should be done with corpus_segment.py
        while cur <= 7 and steps[cur]:
            cur += 1

        # 1. tokenize .txt files in to_segment, tokenized are in segmented as _segmented.txt files
        if cur == 2:
            print("\tsegmenting...")
            if not tok:
                tok = T.set_tok()

            in_file = steps[cur - 1]
            out_file = path_ids[cur][0] / (in_file.stem + "_segmented.txt")
            T.tok_file(tok, in_file, out_file)
            new_files.append(in_file)
            new_files.append(out_file)

            # 2. manually correct the segmentation
            print("\t--> Please manually correct the segmentation.")

        # 3. create the _totag.xlsx in to_tag from the segmented .txt file from segmented
        elif cur == 3:
            print("\ncreating the file to tag...")
            # TODO: merge the base onto and all the ones from individual files, only add data validation to new words.
            in_file = steps[cur - 1]
            out_file = path_ids[cur-1][0] / (in_file.stem.split("_")[0] + "_totag.xlsx")
            if not out_file.is_file():
                generate_to_tag(in_file, out_file, resources, basis_onto=basis_onto)
                new_files.append(out_file)

            # 4. manually POS tag the segmented text
            print(
                "\t--> Please manually tag new words with their POS tag and level. (words not tagged will be ignored)"
            )

        # 5. create .yaml ontology files from tagged .xlsx files from to_tag
        elif cur == 4:
            print("\t creating the onto from the tagged file...")
            in_file = steps[cur - 1]
            out_file = path_ids[cur - 1][0] / (
                in_file.stem.split("_")[0] + "_onto.yaml"
            )
            if not out_file.is_file():
                onto_from_tagged(in_file, out_file, resources, basis_onto=basis_onto)
                new_files.append(out_file)

            # 6. manually fill in the onto
            print(
                '\t--> Please integrate new words in the onto from "to_organize" sections and add synonyms.'
            )

        # 7. create .xlsx files in to_simplify from segmented .txt files from segmented
        elif cur == 5:
            print("\tcreating file to simplify...")
            in_file = steps[cur - 3]
            out_file = path_ids[cur - 1][0] / (in_file.stem.split("_")[0] + ".xlsx")
            generate_to_simplify(in_file, out_file, resources, l_colors, basis_onto=basis_onto)
            new_files.append(out_file)

            # 8. manually process the .xlsx files in to_simplify
            print("\t--> Please manually simplify the sentences.")

        # 9. generate alternative sentences as _sents.xlsx files in simplified from .xlsx files in to_simplify
        elif cur == 6:
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
        elif cur == 7:
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
    state = {}
    # starting from segmented
    for path, _ in paths_ids[1:]:
        for f in path.glob("*"):
            if f.suffix not in [".txt", ".xlsx", ".yaml", '.docx']:
                continue
            stem = f.stem.split("_")[0]
            if stem not in state:
                state[stem] = {i: None for i in range(2, len(paths_ids) + 1)}
            step = int(f.parts[1][0])
            state[stem][step] = f

    resources = {f.stem: f for f in paths_ids[3][0].glob("*.yaml")}
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
    if not content_path.is_dir():
        content_path.mkdir()
    for sub in sub_folders:
        if not (content_path / sub).is_dir():
            (content_path / sub).mkdir()
