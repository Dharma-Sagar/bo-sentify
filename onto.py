from pathlib import Path
from sentify.onto.leavedonto import LeavedOnto, OntoManager, merge_ontos, export

om = OntoManager(Path('content/0 resources/master_onto.yaml'))
om.adjust_legends()
