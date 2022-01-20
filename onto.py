from sentify.onto.leavedonto import LeavedOnto

in_file = "content/0 resources/master_onto.yaml"
lo = LeavedOnto(in_file)
lo.convert2xlsx()
