from sentify.onto.leavedonto import LeavedOnto

in_file = "content/4 vocabulary/general_onto.yaml"
lo = LeavedOnto(in_file)
lo.convert2xlsx()
