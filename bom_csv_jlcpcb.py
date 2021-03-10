#
# Example python script to generate a BOM from a KiCad generic netlist
#
# Example: Sorted and Grouped CSV BOM
#

"""
    @package
    Generate a CSV BOM for use with JLCSMT service.
    Components are sorted by ref and grouped by value with same footprint
    Fields are (if exist).
    LCSC Part numbers are copied from the "LCSC Part" field, if exists.
    It is possible to hide components from the BOM by setting the 
    "JLCPCB BOM" field to "0" or "false".

    Output fields:
    'Comment', 'Designator', 'Footprint', 'LCSC Part #'

    Command line:
    python "pathToFile/bom_csv_jlcsmt.py" "%I" "%O.bom.csv"
"""

import kicad_netlist_reader
import csv
import sys

net = kicad_netlist_reader.netlist(sys.argv[1])

with open(sys.argv[2], 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['Designator', 'Quantity', 'Value', 'Footprint', 'LCSC Part #', 'Comment'])

    for group in net.groupComponents():
        refs = []

        lcsc_pn = ""
        for component in group:
            if component.getField('JLCPCB BOM') in ['0', 'false', 'False', 'FALSE']:
                continue
            #component.
            refs.append(component.getRef())
            lcsc_pn = component.getField("LCSC") or component.getField("LCSC Part #") or lcsc_pn
            c = component
            #if not lcsc_pn:
            #    print("Skipping part without LCSC#: " +  c.getRef() + " / " + c.getDescription())
            #    refs = []
            #    continue

        if len(refs) == 0:
            continue

        # Fill in the component groups common data
        out.writerow([str(refs).translate(str.maketrans("", "", "[]'")), len(group), c.getValue(), c.getFootprint().split(':')[1], lcsc_pn.strip(' \n\t'), '{name} {desc}'.format(name=c.getField("Cmp name").strip('"'), desc=c.getDescription())])

    f.close()
