from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

from .onto.leavedonto import OntoManager
from .dataval import DataVal
from .utils import resize_sheet


def generate_to_simplify(in_file, out_file, resources, l_colors):
    how_many_copied_lines = 12
    font = "Jomolhari"
    ft_sent = Font(font, size=12)
    alignmnt = Alignment(horizontal="left", vertical="center")

    wb = Workbook()
    wb.remove(wb.get_sheet_by_name("Sheet"))

    # add sentences to sheets
    lines = in_file.read_text().lstrip("\ufeff").split("\n")
    for s, sent in enumerate(lines):
        ws = wb.create_sheet(title=str(s))
        words = sent.split(" ")
        for i in range(2, how_many_copied_lines):
            for n, w in enumerate(words):
                cell = ws.cell(row=i, column=n + 1)
                cell.value = w
                cell.font = ft_sent
                cell.alignment = alignmnt
        resize_sheet(ws)

    # load ontos
    main_onto = resources["general_onto"]
    other_ontos = [r for r in resources.values() if r.stem != "general_onto"]

    om = OntoManager(main_onto)
    om.batch_merge_to_onto(other_ontos)
    onto = om.onto1

    # add data validation for synonyms and color cells according to levels
    dv = DataVal(wb)
    val_num = 0
    for name in wb.sheetnames:
        sheet = wb[name]
        row = 2
        for col in range(1, sheet.max_column + 1):
            cell = sheet.cell(row, col)
            word = cell.value

            # get all entries corresponding to word
            found = onto.find_word(word)

            # ## SYNONYMS ## #
            # extract all synonyms
            syns = [word]
            for path, entries in found:
                for e in entries:
                    syns.append(onto.get_field_value(e, "lemma"))
                    s = onto.get_field_value(e, "synonyms")
                    syns.extend([a for a in s.split(" ") if a])
            syns = list(set(syns))

            # pass if no synonyms
            if (len(syns) == 1 and syns[0] != word) or len(syns) > 1:
                # add synonyms as data validation to cell
                val_name = f"{val_num} {word}"
                dv.add_validator(val_name, syns)
                dv.add_val_to_cell(val_name, name, row=row, col=col)
                val_num += 1

            # TODO: decide not only based on first element of list, but use combination of POS + word to find entries
            if found:
                level = onto.get_field_value(found[0][1][0], "level")
                cell.fill = PatternFill("solid", fgColor=l_colors[level])

    wb.save(out_file)
