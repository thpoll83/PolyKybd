#!/usr/bin/env python3
import ezodf
SRC = "/sessions/bold-festive-carson/mnt/uploads/Riskanalysis TEMPLATE_EN.ods"
OUT = "/sessions/bold-festive-carson/mnt/outputs/Riskanalysis_PolyKybd_EN.ods"
d = ezodf.opendoc(SRC)
S = d.sheets

def put(sheet, r, c, v):
    sheet[r, c].set_value(v)

# ---------- 0: Product data / Participants ----------
p = S[0]
put(p,0,4,"PolyKybd Split72")                 # Product name
put(p,1,4,"PK/S72-000001 ff. (per unit; -L/-R per half)")  # Serial No.
put(p,2,4,"PolyKybd Split72")                 # Type No.
put(p,5,1,"PolyKybd Split72 - wired USB mechanical keyboard")
put(p,6,1,"PolyKybd Split72")
put(p,7,1,"2026")
put(p,8,1,"PK/S72-000001 ff. (-L / -R per half)")
put(p,10,1,"1.0"); put(p,10,2,"Draft"); put(p,10,3,"2026-07-17"); put(p,10,4,"2026-07-17")
# authorized representative
put(p,13,1,"Thomas Pollak")
put(p,14,1,"PolyTasten GmbH")
put(p,15,1,"[Austrian address - TO CONFIRM]")
put(p,16,1,"Manufacturer / responsible for technical documentation")
# external consultant
put(p,19,1,"[CE consultant name - TO CONFIRM]")
put(p,20,1,"[Consultant company - TO CONFIRM]")
put(p,21,1,"[Address - TO CONFIRM]")
put(p,22,1,"External CE consultant")
# participants
put(p,25,1,"Thomas Pollak"); put(p,26,1,"PolyTasten GmbH")

# ---------- 1: borders (limits / intended use) ----------
b = S[1]
put(b,5,1,"Indoor use as a USB computer keyboard, powered only from a USB 5 V port (SELV). No mains, no battery, no radio.")
put(b,6,1,"Indoor, dry residential/office environment; connect only to a standard USB-C host/port.")
put(b,7,1,"Exposure to liquids; outdoor/wet use; connecting to a non-USB power source; disassembly by the user.")
put(b,8,1,"Use with non-USB power sources; use in wet or hazardous environments; modification of the design (voids conformity).")
put(b,11,1,"Private and commercial (residential/office). EMC Class B.")
# user group 1
put(b,14,1,"Consumer / keyboard user")
put(b,15,1,"Adults using a PC keyboard at a desk")
put(b,16,1,"Connecting, typing, cleaning")
put(b,17,1,"None required (consumer product)")
# user group 2 (kit assembler - mechanical only)
put(b,19,1,"Kit assembler (base product: mechanical assembly only, NO soldering; optional solder-in components are not shipped)")
put(b,20,1,"Insert hot-swap switches and keycaps, connect FPC cables, close the case")
put(b,21,1,"Basic manual dexterity; follows the build guide")
# other vulnerable people
put(b,28,1,"Children")
put(b,29,1,"Small parts (keycaps, stems, switches, screws) present a choking hazard; not a toy")
# spatial
put(b,32,1,"Desktop / workstation use")
put(b,34,1,"USB-C (host connection and inter-half link)")
put(b,36,1,"USB 5 V DC, SELV (max 500 mA, USB 2.0)")
# time
put(b,40,1,"Designed for multi-year desktop use; hot-swap parts replaceable")
put(b,41,1,"n/a (continuous desktop use)")
# materials
put(b,47,1,"Aluminium (top plate / case)"); put(b,48,1,"Structural plate/case"); put(b,49,1,"Metal (non-hazardous article)"); put(b,50,1,"n/a")
put(b,52,1,"Plastics (keycaps, case, switch housings)"); put(b,53,1,"Housing / keys"); put(b,54,1,"Polymer, RoHS-compliant"); put(b,55,1,"n/a")
put(b,57,1,"PCB assembly and electronic components"); put(b,58,1,"Electronics"); put(b,59,1,"Electronic assembly, RoHS-compliant"); put(b,60,1,"See RoHS compliance file")

# ---------- 2: Guidelines / Standards ----------
g = S[2]
std = [
 ("EN ISO 13849-1:2023","Safety-related parts of control systems","2023"),
 ("EN ISO 12100:2010","Safety of machinery - general principles for design","2010"),
 ("EN 55032","EMC of multimedia equipment - emission (Class B)","[edition - confirm]"),
 ("EN 55035","EMC of multimedia equipment - immunity","[edition - confirm]"),
 ("EN IEC 63000:2018","Technical documentation for RoHS assessment","2018"),
 ("EN 62368-1","Safety of audio/video, IT and communication equipment","[edition - confirm]"),
 ("Directive 2014/30/EU","Electromagnetic Compatibility (EMC) Directive","-"),
 ("Directive 2011/65/EU","RoHS Directive (as amended by (EU) 2015/863)","-"),
 ("Regulation (EU) 2023/988","General Product Safety Regulation (GPSR)","-"),
]
row=5
for idv,desig,rev in std:
    put(g,row,1,idv); put(g,row+1,1,desig); put(g,row+2,1,rev); row+=4

# ---------- LP sheets ----------
def fill_lp(sheet, phase, blocks):
    sheet[5,0].set_value(phase)
    bases=[7,17,27]
    for base,blk in zip(bases, blocks):
        put(sheet,base,1,blk["task"])
        put(sheet,base+1,1,blk["hazard"])
        put(sheet,base+2,1,blk["event"])
        put(sheet,base+3,1,blk["solution"])
        put(sheet,base+4,1,blk["guideline"])
        put(sheet,base+5,1,blk["standard"])
        put(sheet,base+7,1,blk["S"]); put(sheet,base+7,2,blk["F"])
        put(sheet,base+7,3,blk["P"]); put(sheet,base+7,4,blk["PL"])
        put(sheet,base+8,1,blk["reason"])

def blk(task,hazard,event,solution,guideline,standard,Sv,Fv,Pv,PL,reason):
    return dict(task=task,hazard=hazard,event=event,solution=solution,guideline=guideline,
                standard=standard,S=Sv,F=Fv,P=Pv,PL=PL,reason=reason)

fill_lp(S[4],"Transport",[
 blk("Transport and storage of the packaged product","Mechanical shock/vibration during handling",
     "Product/parts not damaged; no injury during handling","Protective packaging; small, light, passive item",
     "GPSR (EU) 2023/988; PPWR","-","S1","F1","P1","a","Low-energy passive item; no residual transport hazard"),
])
fill_lp(S[5],"Final Production",[
 blk("Assembly of the keyboard by the manufacturer","Mechanical (pinch) and ESD to electronics during assembly",
     "No product damage; worker safety","Controlled assembly; ESD precautions. Base product ships WITHOUT solder-in optional parts, so no soldering is required.",
     "GPSR (EU) 2023/988","EN 62368-1","S1","F1","P1","a","Controlled environment; no user soldering"),
])
fill_lp(S[6],"Installation",[
 blk("Connecting the keyboard (halves and host) via USB-C","Cable strain / trip; connector damage",
     "No trip injury or connector damage","Standard USB-C cabling; routing advice in the manual",
     "GPSR (EU) 2023/988","EN 62368-1","S1","F1","P1","a","Low hazard; addressed by user information"),
 blk("Handling before first use","Electrostatic discharge (ESD) to USB / electronics",
     "No damage or malfunction","ESD protection (TPD4E05) on USB; manual advises normal ESD care",
     "Directive 2014/30/EU","EN 55035","S1","F1","P1","a","Protected inputs; immunity to EN 55035"),
])
fill_lp(S[7],"Commissioning",[
 blk("First power-up over USB","Electric shock","No shock","5 V SELV from USB only; no mains, no battery",
     "GPSR (LVD not applicable)","EN 62368-1","S1","F1","P1","a","SELV - inherently safe"),
 blk("Displays / LEDs initialise","ESD or immunity glitch","No malfunction or damage",
     "ESD protection; EMC immunity by design","Directive 2014/30/EU","EN 55035","S1","F1","P1","a","Immunity tested"),
])
fill_lp(S[8],"Operation",[
 blk("Normal desktop use and handling","Sharp edges of the metal plate / case","No cuts or abrasion",
     "Deburr / chamfer edges; QC check; note in manual","GPSR (EU) 2023/988","EN 62368-1","S1","F2","P1","b","Edges finished; residual low"),
 blk("Handling keys / keycaps","Small parts (keycaps, stems, switches) - choking","No choking of young children",
     "Not a toy; 'keep away from children under 3' warning; small-parts note on packaging","GPSR (EU) 2023/988","-","S2","F1","P1","c","Warning; not intended for children"),
 blk("Use near liquids","Liquid ingress -> short / malfunction","No hazard from wet electronics (5 V)",
     "Manual: keep liquids away; disconnect and dry before reuse","GPSR (EU) 2023/988","EN 62368-1","S1","F1","P1","a","SELV; user instruction"),
])
fill_lp(S[9],"Decommissioning",[
 blk("Disconnecting the keyboard","No significant hazard (unplug USB-C)","Safe disconnection",
     "Simply unplug the USB-C cable; no stored energy","GPSR (EU) 2023/988","-","S1","F1","P1","a","Passive item, no stored energy"),
])
fill_lp(S[10],"Disassembly",[
 blk("Opening the case (repair / switch swap)","Sharp edges; small parts","No cuts; parts not lost or swallowed",
     "Hot-swap switches (no soldering); care with edges; guidance provided","GPSR (EU) 2023/988","EN 62368-1","S1","F1","P1","a","Occasional, low energy"),
])
fill_lp(S[11],"Disposal",[
 blk("End-of-life disposal","Improper disposal of electronics / materials","Correct WEEE recycling; no environmental harm",
     "WEEE marking (crossed-out bin); RoHS-compliant materials; disposal info in manual","WEEE 2012/19/EU; RoHS 2011/65/EU","EN IEC 63000","S1","F1","P1","a","Marked and RoHS-compliant"),
])
fill_lp(S[12],"Additional life phases",[
 blk("Prolonged typing","Ergonomic strain (RSI-type)","Minimise strain",
     "Split/tenting design supports neutral posture; manual advises breaks","GPSR (EU) 2023/988","-","S1","F2","P1","b","Design plus guidance"),
 blk("Continuous operation","Overheating","No burns or fire",
     "Low power (<~2.5 W); USB host current limiting; no battery; flame-rated PCB","GPSR (EU) 2023/988","EN 62368-1","S1","F1","P1","a","Very low power"),
 blk("Foreseeable misuse","Wrong power source / outdoor use / modification","No hazard or damage",
     "Manual states intended use (USB 5 V, indoor); 'modifications void conformity'","GPSR (EU) 2023/988","-","S1","F1","P1","a","Instructions plus SELV design"),
])

d.saveas(OUT)
print("saved", OUT)
