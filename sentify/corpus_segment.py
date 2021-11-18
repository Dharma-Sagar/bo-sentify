from pathlib import Path
import re

from botok import WordTokenizer, Config
import yaml


def set_tok():
    c = Config(dialect_name='general', base_path=Path('../output/tok_data'))
    return WordTokenizer(config=c)


def tokenize(tok, string):
    lemmatization_exceptions = ['བཅས་', 'མཁས་']
    tokens = tok.tokenize(string)
    words = []
    for t in tokens:
        if t.chunk_type == 'TEXT':
            if not t.lemma:
                text = t.text
            else:
                if t.pos == 'PART':
                    if t.affix:
                        text = '-' + t.text
                    else:
                        text = t.text
                else:
                    # Hack because of botok limitation:
                    if t.text_cleaned not in lemmatization_exceptions and t.affixation and 'aa' in t.affixation and t.affixation['aa']:
                        text = t.lemma
                    else:
                        text = t.text
            text = text.strip().replace('༌', '་')
            if not text.endswith('་'):
                text += '་'

            if t.pos == 'NON_WORD':
                text += '#'
            words.append(text)

        else:
            t = t.text.replace(' ', '_')
            words.append(t)

    tokenized = ' '.join(words)

    # do replacements
    repl_path = Path('../output/tok_data') / 'general' / 'adjustments' / 'rules' / 'replacements.txt'
    if not repl_path.is_file():
        repl_path.write_text('')
    for line in repl_path.read_text().split('\n'):
        if '—' in line:
            orig, repl = line.split('—')
            tokenized = tokenized.replace(orig, repl)

    return tokenized


def tok_file(tok, in_file, out_file):
    dump = in_file.read_text()
    out = []
    for line in dump.split('\n'):
        out.append(tokenize(tok, line))
    out_file.write_text('\n'.join(out))


def tok_corpus(in_path, out_path):
    if not out_path.is_dir():
        out_path.mkdir()
    tok = set_tok()
    for f in in_path.glob('*.txt'):
        out_file = out_path / (f.stem + '_segmented.txt')
        if out_file.is_file():
            print('passing: ', str(f), 'is already processed.')
            continue
        print(f)
        tok_file(tok, f, out_file)
