"""Compose two native KiCad trace SVGs for review; does not edit the PCB."""
from pathlib import Path
import xml.etree.ElementTree as E

P=Path(__file__).resolve().parents[1]/'previews/routed'
ns='http://www.w3.org/2000/svg'
E.register_namespace('',ns)
def el(tag,attrs=None,text=None):
    e=E.Element('{'+ns+'}'+tag,attrs or {})
    if text is not None:e.text=text
    return e
root=el('svg',{'width':'1240','height':'1080','viewBox':'0 0 1240 1080'})
root.append(el('rect',{'width':'1240','height':'1080','fill':'#f3f5f6'}))
root.append(el('text',{'x':'40','y':'51','font-family':'sans-serif','font-size':'30','font-weight':'700','fill':'#18232d'},'Pit Claw carrier · routed PCB'))
root.append(el('text',{'x':'40','y':'82','font-family':'sans-serif','font-size':'17','fill':'#52616c'},'60 × 92 mm · two copper layers · relay retained: USB-PD on NC, wall on NO'))
for x,filename,title,color in [(40,'carrier-front-copper.svg','Front / component side','#C83434'),(640,'carrier-back-copper.svg','Back / solder side (mirrored)','#4D7FC4')]:
    root.append(el('rect',{'x':str(x),'y':'111','width':'560','height':'857','rx':'10','fill':'white','stroke':'#d9e0e5'}))
    root.append(el('text',{'x':str(x+22),'y':'144','font-family':'sans-serif','font-size':'21','font-weight':'600','fill':color},title))
    child=E.parse(P/'traces'/filename).getroot()
    # Native layer export origin for this 60 x 92 mm carrier includes the
    # fabrication notes above/below; crop only those notes in this overview.
    child.attrib={'x':str(x+25),'y':'164','width':'510','height':'783','viewBox':'0 9.765 60.0456 92.05'}
    root.append(child)
root.append(el('text',{'x':'40','y':'1005','font-family':'sans-serif','font-size':'18','fill':'#18232d'},'Ground fills hidden here to make the tracks easy to follow.'))
root.append(el('text',{'x':'40','y':'1034','font-family':'sans-serif','font-size':'16','fill':'#52616c'},'Both ground pours are present in the PCB; back reference labels are a review overlay.'))
E.ElementTree(root).write(P/'carrier-routing-overview.svg',encoding='unicode',xml_declaration=True)
