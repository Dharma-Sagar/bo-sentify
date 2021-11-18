from pathlib import Path

from sentify import generate_sentence_versions, tok_corpus, generate_xlsx


if __name__ == '__main__':
    in_path = Path('input')
    out_path = Path('output')

    # tokenize .txt files in ./input/, tokenized in ./output/ as _segmented.txt files
    tok_corpus(in_path, out_path)

    # manually correct the segmentation

    # create .xlsx files in ./input/ from segmented .txt files from ./output/
    generate_xlsx(out_path, in_path)

    # manually process the .xlsx files in ./input/

    # generate alternative sentences as _sents.xlsx files in ./output/ from .xlsx files in ./input/
    generate_sentence_versions(in_path, out_path)
