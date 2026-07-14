const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, BorderStyle } = require('docx');

const BLUE = "1F4E78";
const GREY = "606060";

function h(text){return new Paragraph({spacing:{after:120},children:[new TextRun({text,bold:true,size:22,color:BLUE})]});}
function p(runs,opts={}){return new Paragraph({spacing:{after:100},...opts,children:runs});}
function t(text,o={}){return new TextRun({text,size:20,...o});}
function field(label,value){
  return new Paragraph({spacing:{after:60},children:[
    new TextRun({text:label+"  ",bold:true,size:20}),
    new TextRun({text:value,size:20,color: value.includes("[")?"C00000":"000000"}),
  ]});
}
function bullet(text){return new Paragraph({bullet:{level:0},spacing:{after:40},children:[t(text)]});}
function rule(){return new Paragraph({border:{bottom:{color:"BFBFBF",style:BorderStyle.SINGLE,size:6}},spacing:{after:120}});}

const doc = new Document({
  creator:"PolyKybd",
  title:"EU Declaration of Conformity",
  styles:{ default:{ document:{ run:{ font:"Arial" } } } },
  sections:[{
    properties:{page:{margin:{top:1000,bottom:1000,left:1100,right:1100}}},
    children:[
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:40},children:[new TextRun({text:"EU DECLARATION OF CONFORMITY",bold:true,size:32,color:BLUE})]}),
      new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:200},children:[new TextRun({text:"in accordance with EMC Directive 2014/30/EU and RoHS Directive 2011/65/EU",size:18,italics:true,color:GREY})]}),
      rule(),

      field("DoC No.:","[TO CONFIRM — e.g. PK-DOC-2026-001]"),
      field("Revision / date:","[TO CONFIRM]"),
      new Paragraph({spacing:{after:120},children:[]}),

      h("1. Manufacturer"),
      field("Name:","[TO CONFIRM — legal manufacturer name]"),
      field("Address:","[TO CONFIRM — full postal address]"),
      field("Contact:","[TO CONFIRM — email / phone]"),
      field("EU Responsible Person (if manufacturer is outside the EU):","[TO CONFIRM — name & EU address]"),

      h("2. This declaration of conformity is issued under the sole responsibility of the manufacturer."),

      h("3. Object of the declaration"),
      field("Product:","PolyKybd Split72 — mechanical split keyboard (USB, HID)"),
      field("Model / type:","[TO CONFIRM — model/type designation; variants: left half, right half]"),
      field("Description:","RP2040-based split mechanical keyboard with per-key OLED displays and addressable LEDs, powered from USB (5 V DC), connected by USB-C. No radio/wireless function."),
      field("Batch / serial:","[TO CONFIRM — serial or batch traceability]"),

      h("4. The object described above is in conformity with the relevant Union harmonisation legislation:"),
      bullet("Directive 2014/30/EU (Electromagnetic Compatibility)"),
      bullet("Directive 2011/65/EU (Restriction of Hazardous Substances) as amended by Delegated Directive (EU) 2015/863"),

      h("5. References to the relevant harmonised standards used"),
      bullet("EN 55032:[TO CONFIRM edition] — Electromagnetic compatibility of multimedia equipment — Emission requirements (Class B)"),
      bullet("EN 55035:[TO CONFIRM edition] — Electromagnetic compatibility of multimedia equipment — Immunity requirements"),
      bullet("EN IEC 63000:2018 — Technical documentation for the assessment of electrical and electronic products with respect to the restriction of hazardous substances"),
      p([new TextRun({text:"Note: EN 61000-3-2 / EN 61000-3-3 are not applicable (the apparatus is USB-powered and not connected to the public mains).",size:18,italics:true,color:GREY})]),

      h("6. Additional information"),
      p([t("Conformity assessment for the EMC Directive is by internal production control (Annex II); no notified body was involved. Supporting technical documentation (RoHS compliance file per EN IEC 63000, schematics, PCB layer documentation, EMC test report(s), and risk assessment) is held by the manufacturer and available to market surveillance authorities for 10 years after the last unit is placed on the market.")]),
      p([new TextRun({text:"Outstanding before signing: attach EMC test report(s) to EN 55032 / EN 55035 and confirm the standard editions above.",size:18,italics:true,color:"C00000"})]),

      rule(),
      h("Signed for and on behalf of the manufacturer"),
      field("Place of issue:","[TO CONFIRM]"),
      field("Date of issue:","[TO CONFIRM]"),
      field("Name:","[TO CONFIRM]"),
      field("Function:","[TO CONFIRM]"),
      new Paragraph({spacing:{before:200},children:[t("Signature: _______________________________")]}),
    ],
  }],
});

Packer.toBuffer(doc).then(b=>{fs.writeFileSync("/sessions/bold-festive-carson/mnt/outputs/EU-Declaration-of-Conformity.docx",b);console.log("written");});
