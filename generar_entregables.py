from pathlib import Path
import math, os, xml.etree.ElementTree as ET, zipfile, textwrap, json, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, Polygon, FancyArrowPatch, Circle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter

BASE=Path('/mnt/data/Unidad_2_Bases_Datos')
C={'ink':'#20304a','navy':'#12243b','blue':'#315f9a','light':'#e9f1fb','aqua':'#dff4ec','green':'#15765f','gold':'#fcf0d8','red':'#a54d3d','soft':'#eff2f6','muted':'#617187','white':'#ffffff'}
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',FONT));pdfmetrics.registerFont(TTFont('DVB',FONTB))

class Diagram:
 def __init__(self,name,W=1800,H=1150):
  self.name=name;self.W=W;self.H=H;self.elements=[]; self.edges=[]; self.labels=[]
  self.fig,self.ax=plt.subplots(figsize=(18,11.5));self.ax.set_xlim(0,W);self.ax.set_ylim(H,0);self.ax.set_aspect('equal');self.ax.axis('off');self.fig.patch.set_facecolor('white')
 def txt(self,x,y,t,sz=16,bold=False,color=None,ha='center',valign='center',rot=0):
  self.ax.text(x,y,t,fontsize=sz,fontfamily='DejaVu Sans',weight='bold' if bold else 'normal',color=color or C['ink'],ha=ha,va=valign,rotation=rot,zorder=10)
  self.labels.append((x,y,t,sz,bold,color or C['ink'],ha))
 def rect(self,id,x,y,w,h,text='',fill=None,stroke=None,fontsize=17,kind='rect',bold=True):
  fill=fill or C['light'];stroke=stroke or C['blue']
  self.ax.add_patch(Rectangle((x,y),w,h,facecolor=fill,edgecolor=stroke,linewidth=2.2,zorder=3))
  if text:self.txt(x+w/2,y+h/2,text,fontsize,bold)
  self.elements.append((id,x,y,w,h,text,kind,fill,stroke,fontsize))
 def diamond(self,id,cx,cy,w,h,text='',fill=None,fontsize=13):
  fill=fill or C['gold'];pts=[[cx,cy-h/2],[cx+w/2,cy],[cx,cy+h/2],[cx-w/2,cy]]
  self.ax.add_patch(Polygon(pts,closed=True,facecolor=fill,edgecolor=C['red'],linewidth=1.9,zorder=4))
  if text:self.txt(cx,cy,text,fontsize,True)
  self.elements.append((id,cx-w/2,cy-h/2,w,h,text,'diamond',fill,C['red'],fontsize))
 def ellipse(self,id,cx,cy,w,h,text,fill=None,fontsize=13,stroke=None,dashed=False,double=False,under=False):
  fill=fill or C['white'];stroke=stroke or C['blue']
  self.ax.add_patch(Ellipse((cx,cy),w,h,facecolor=fill,edgecolor=stroke,linewidth=1.8,linestyle='--' if dashed else '-',zorder=4))
  if double: self.ax.add_patch(Ellipse((cx,cy),w-10,h-10,fill=False,edgecolor=stroke,lw=1.3,zorder=5))
  self.txt(cx,cy,text,fontsize,under)
  self.elements.append((id,cx-w/2,cy-h/2,w,h,text,'ellipse_dash' if dashed else ('ellipse_double' if double else 'ellipse'),fill,stroke,fontsize))
 def circle(self,id,cx,cy,rad,text='',fill=None,fontsize=13):
  self.ax.add_patch(Circle((cx,cy),rad,facecolor=fill or C['aqua'],edgecolor=C['green'],lw=2,zorder=4)); self.txt(cx,cy,text,fontsize,True)
  self.elements.append((id,cx-rad,cy-rad,rad*2,rad*2,text,'ellipse',fill or C['aqua'],C['green'],fontsize))
 def line(self,id,pts,color=None,lw=2.1,dashed=False,label=None,labelpos=None,labelsiz=13,arrow=False):
  color=color or C['muted'];xs=[p[0] for p in pts];ys=[p[1] for p in pts]
  self.ax.plot(xs,ys,color=color,lw=lw,linestyle='--' if dashed else '-',zorder=1)
  if arrow:
   a,b=pts[-2],pts[-1]
   self.ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=13,color=color,lw=2,zorder=2))
  self.edges.append((id,pts,color,dashed))
  if label and labelpos:self.txt(*labelpos,label,labelsiz,False,C['red'])
 def note(self,x,y,w,h,text,sz=12):
  self.ax.add_patch(Rectangle((x,y),w,h,facecolor=C['soft'],edgecolor='#ced7e2',linewidth=1.2,zorder=2))
  self.elements.append(('note'+str(len(self.elements)),x,y,w,h,'','note',C['soft'],'#ced7e2',sz))
  for i,ln in enumerate(text.split('\n')): self.txt(x+12,y+16+21*i,ln,sz,False,C['muted'],ha='left')
 def title(self,heading,subtitle=''):
  self.txt(self.W/2,50,heading,25,True,C['navy']);self.txt(self.W/2,90,subtitle,13,False,C['muted'])
 def save(self,folder):
  folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
  for fmt in ['png','pdf','svg']:
   self.fig.savefig(folder/(self.name+'.'+fmt),dpi=200,facecolor='white',bbox_inches='tight',pad_inches=.15)
  plt.close(self.fig)
  self.drawio(BASE/'Diagramas_Editables'/(self.name+'.drawio'))
 def drawio(self,path):
  root=ET.Element('mxfile',host='app.diagrams.net',modified='2026-11-07T00:00:00.000Z',agent='ChatGPT',version='24.7.17',type='device')
  d=ET.SubElement(root,'diagram',id=self.name,name=self.name)
  mx=ET.SubElement(d,'mxGraphModel',dx='1600',dy='1200',grid='1',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='1',pageScale='1',pageWidth=str(self.W),pageHeight=str(self.H),math='0',shadow='0')
  cells=ET.SubElement(mx,'root');ET.SubElement(cells,'mxCell',id='0');ET.SubElement(cells,'mxCell',id='1',parent='0')
  for id,x,y,w,h,t,kind,fill,stroke,fs in self.elements:
   style=f'rounded=0;whiteSpace=wrap;html=1;strokeColor={stroke};fillColor={fill};fontColor={C["ink"]};fontFamily=DejaVu Sans;fontStyle=1;fontSize={fs};align=center;verticalAlign=middle;'
   if kind=='diamond':style+='shape=rhombus;'
   if kind.startswith('ellipse'):style+='ellipse;shape=ellipse;'
   if kind=='ellipse_dash':style+='dashed=1;'
   if kind=='ellipse_double':style+='double=1;'
   if kind=='uml':style+='align=left;spacingLeft=9;fontStyle=0;'
   if kind=='note':style+='rounded=0;'
   if kind=='enclosure':style+='fillColor=none;dashed=1;strokeWidth=3;' 
   cell=ET.SubElement(cells,'mxCell',id=id,value='',style=style,vertex='1',parent='1')
   ET.SubElement(cell,'mxGeometry',x=str(round(x,2)),y=str(round(y,2)),width=str(round(w,2)),height=str(round(h,2)),**{'as':'geometry'})
  for id,pts,color,dashed in self.edges:
   style=f'edgeStyle=orthogonalEdgeStyle;html=1;rounded=0;orthogonalLoop=1;jettySize=auto;strokeWidth=2;strokeColor={color};'
   if dashed:style+='dashed=1;'
   cell=ET.SubElement(cells,'mxCell',id=id,value='',style=style,edge='1',parent='1')
   geo=ET.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
   ET.SubElement(geo,'mxPoint',x=str(pts[0][0]),y=str(pts[0][1]),**{'as':'sourcePoint'})
   ET.SubElement(geo,'mxPoint',x=str(pts[-1][0]),y=str(pts[-1][1]),**{'as':'targetPoint'})
   if len(pts)>2:
    arr=ET.SubElement(geo,'Array',**{'as':'points'})
    for x,y in pts[1:-1]: ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
  for k,(x,y,t,sz,bold,color,ha) in enumerate(self.labels):
   maxlen=max(len(line) for line in str(t).split('\n'))
   width=min(self.W, max(55, sz*0.69*maxlen+12))
   height=max(24, len(str(t).split('\n'))*sz*1.65)
   left=x if ha=='left' else x-width/2
   val=escape_xml_label(t)
   style=f'text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align={"left" if ha=="left" else "center"};verticalAlign=middle;fontSize={sz};fontColor={color};fontStyle={1 if bold else 0};fontFamily=DejaVu Sans;spacing=0;'
   cell=ET.SubElement(cells,'mxCell',id=f'label_{k}',value=val,style=style,vertex='1',parent='1')
   ET.SubElement(cell,'mxGeometry',x=str(round(left,2)),y=str(round(y-height/2,2)),width=str(round(width,2)),height=str(round(height,2)),**{'as':'geometry'})
  s=ET.tostring(root,encoding='utf-8',xml_declaration=True)
  path.write_bytes(s)

def escape_xml_label(t):return str(t).replace('\n','<br>')
EXP=BASE/'Diagramas_Exportados'
# Diagram 1 ER core
D=Diagram('ER_Conceptual',1800,1180)
D.title('DIAGRAMA E-R CONCEPTUAL | BIBLIOTECA ESCOLAR','Notación Chen simplificada: entidades, relaciones y cardinalidades min..max (cada extremo describe las instancias que corresponden a la entidad opuesta)')
D.rect('autor',85,200,210,85,'AUTOR',C['light']);D.diamond('escribe',420,243,170,92,'ESCRIBE');D.rect('libro',585,200,230,85,'LIBRO',C['light']);D.diamond('tiene',965,243,170,92,'TIENE');D.rect('ejemplar',1115,200,240,85,'EJEMPLAR',C['light'])
D.rect('coleccion',585,505,230,85,'COLECCIÓN',C['aqua']);D.diamond('agrupa',700,390,180,90,'AGRUPA',C['aqua'])
D.rect('persona',85,780,245,85,'PERSONA',C['light']);D.diamond('realiza',460,823,170,92,'REALIZA');D.rect('prestamo',660,780,245,85,'PRÉSTAMO',C['light']);D.diamond('sobre',1040,823,175,92,'SOBRE');D.rect('incidencia',660,1020,245,85,'INCIDENCIA',C['aqua']);D.diamond('genera',782,945,185,88,'GENERA',C['aqua'])
D.line('a1',[(295,243),(335,243)],label='1..*',labelpos=(312,210));D.line('a2',[(505,243),(585,243)],label='0..*',labelpos=(546,210))
D.line('a3',[(815,243),(880,243)],label='1',labelpos=(842,211));D.line('a4',[(1050,243),(1115,243)],label='0..*',labelpos=(1080,210))
D.line('a5',[(700,285),(700,345)],label='0..*',labelpos=(758,316));D.line('a6',[(700,435),(700,505)],label='0..*',labelpos=(760,462))
D.line('a7',[(330,823),(375,823)],label='1',labelpos=(350,795));D.line('a8',[(545,823),(660,823)],label='0..*',labelpos=(590,790))
D.line('a9',[(905,823),(952,823)],label='0..*',labelpos=(928,788));D.line('a10',[(1128,823),(1235,823),(1235,285)],label='1',labelpos=(1277,525))
D.line('a11',[(782,865),(782,901)],label='1',labelpos=(845,889));D.line('a12',[(782,989),(782,1020)],label='0..*',labelpos=(834,1006))
D.note(1400,205,355,207,'REGLAS COMPLEMENTARIAS\nPersona -> estudiante o docente\n(total y disjunta). Ver E-RE.\nUn ejemplar puede tener muchos\npréstamos HISTÓRICOS, pero\nsolo uno activo a la vez.',11)
D.note(1390,560,375,176,'LECTURA\n0..* = cero o muchos\n1..* = uno o muchos\n1 = exactamente uno\nLa participación obligatoria se\nindica donde el mínimo es 1.',12)
D.save(EXP)

# Attribute view
D=Diagram('ER_Atributos',1800,1200)
D.title('ATRIBUTOS EN NOTACIÓN CHEN | TIPOS Y DEPENDENCIAS','Ejemplos de atributos clave, compuestos, multivalorados y derivados. La lista completa se encuentra en el reporte.')
D.rect('personaA',300,545,260,100,'PERSONA',C['light'])
D.ellipse('pkpersona',160,420,290,78,'id_persona (PK)',C['gold'],14,under=False)
D.line('pk_underline',[(72,442),(247,442)],color=C['navy'],lw=1.5)
D.ax.plot([72,247],[442,442],color=C['navy'],lw=1.5,zorder=12)
D.ellipse('nombre',445,360,260,82,'nombre',C['light'],16)
D.ellipse('telefonos',760,585,260,85,'{teléfonos}',C['aqua'],15,double=True)
D.ellipse('correo',160,835,210,76,'correo',C['white'],15)
D.ellipse('nombres',310,206,190,70,'nombres',fontsize=14)
D.ellipse('paterno',550,206,210,70,'apellido_paterno',fontsize=12)
D.ellipse('materno',795,206,210,70,'apellido_materno',fontsize=12)
D.line('c1',[(255,440),(355,545)]);D.line('c2',[(445,401),(445,545)]);D.line('c3',[(560,585),(630,585)]);D.line('c4',[(260,810),(343,645)])
D.line('c5',[(310,241),(377,320)]);D.line('c6',[(550,241),(470,320)]);D.line('c7',[(795,241),(552,350)])
D.rect('libroA',1150,550,240,100,'LIBRO',C['light'])
D.ellipse('isbn',1060,420,210,75,'isbn (PK)',C['gold'],14,under=False)
D.line('isbn_underline',[(1010,443),(1110,443)],color=C['navy'],lw=1.5)
D.ax.plot([1010,1110],[443,443],color=C['navy'],lw=1.5,zorder=12)
D.ellipse('titulo',1460,420,220,75,'título',fontsize=15)
D.ellipse('anio',1050,840,270,75,'año_publicación',fontsize=14)
D.ellipse('edad',1490,840,265,75,'edad_obra',C['soft'],14,dashed=True)
D.line('c8',[(1110,457),(1200,550)]);D.line('c9',[(1440,457),(1330,550)]);D.line('c10',[(1170,650),(1090,804)]);D.line('c11',[(1340,650),(1440,804)])
D.note(85,985,1640,128,'LEYENDA: CLAVE = atributo subrayado (PK) · COMPUESTO = nombre con tres componentes\nMULTIVALORADO = doble óvalo · DERIVADO = óvalo discontinuo',14)
D.txt(900,1154,'Ejemplo: edad_obra = año de consulta - año_publicación  ·  teléfonos: 0..* por persona',13,False,C['muted'])
D.save(EXP)

# Extended ER
D=Diagram('ER_Extendido',1800,1100)
D.title('E-R EXTENDIDO (E-RE) | GENERALIZACIÓN Y AGREGACIÓN','Dos recursos de abstracción complementarios al diagrama de entidades y relaciones')
D.txt(425,160,'A · JERARQUÍA DE PERSONAS',18,True,C['blue'])
D.rect('personaE',320,245,230,88,'PERSONA',C['light']);D.circle('isa',435,488,63,'ISA\nd / T',C['aqua'],14)
D.rect('estudiante',145,670,240,92,'ESTUDIANTE',C['light']);D.rect('docente',485,670,240,92,'DOCENTE',C['light'])
D.line('e1',[(427,333),(427,425)]);D.line('e2',[(442,333),(442,425)]);D.line('e3',[(395,543),(265,670)]);D.line('e4',[(475,543),(605,670)])
D.note(110,825,650,165,'d = disjunta: una persona no es estudiante y docente a la vez.\nT = total: toda persona debe ser de uno de los dos subtipos.\nEstudiante aporta matrícula/semestre; Docente aporta núm. empleado/depto.',13)
D.txt(1280,160,'B · AGREGACIÓN DEL EVENTO DE PRÉSTAMO',17,True,C['blue'])
D.ax.add_patch(Rectangle((815,240),910,360,fill=False,lw=2.8,ec=C['green'],linestyle='--'))
D.elements.append(('ag_enclosure',815,240,910,360,'','enclosure','none',C['green'],14))
D.txt(1270,270,'AG_EVENTO_PRÉSTAMO',15,True,C['green'])
D.rect('personaAgg',840,355,175,85,'PERSONA',C['light'],fontsize=14);D.diamond('reaAgg',1090,397,138,84,'REALIZA',fontsize=11);D.rect('prestAgg',1175,355,170,85,'PRÉSTAMO',C['light'],fontsize=14);D.diamond('sobAgg',1440,397,125,84,'SOBRE',fontsize=11);D.rect('ejAgg',1580,355,120,85,'EJEMPLAR',C['light'],fontsize=12)
D.line('ag1',[(1015,397),(1021,397)]);D.line('ag2',[(1159,397),(1175,397)]);D.line('ag3',[(1345,397),(1378,397)]);D.line('ag4',[(1502,397),(1580,397)])
D.rect('incAgg',1100,770,270,85,'INCIDENCIA',C['aqua'],fontsize=15);D.diamond('relAgg',1230,681,154,78,'REGISTRA',C['aqua'],11)
D.line('ag5',[(1230,600),(1230,642)]);D.line('ag6',[(1230,720),(1230,770)])
D.note(855,901,860,140,'El agregado representa el hecho de préstamo vinculado a una incidencia.\nNo crea una tabla independiente; Incidencia referencia id_préstamo.',13)
D.save(EXP)

# UML
D=Diagram('UML_Clases',1800,1300)
D.title('DIAGRAMA DE CLASES UML | BIBLIOTECA ESCOLAR','Transformación del mismo modelo E-R/E-RE · atributos encapsulados · multiplicidades y tipos de asociación explícitos')

def cls(id,x,y,w,header,attrs,fill='#edf3fb'):
 lineh=30;h=54+lineh*len(attrs)
 D.rect(id,x,y,w,h,'',fill,fontsize=14,kind='uml')
 D.ax.plot([x,x+w],[y+48,y+48],c=C['blue'],lw=1.5,zorder=5)
 D.txt(x+w/2,y+23,header,15,True,C['navy'])
 for i,a in enumerate(attrs):D.txt(x+15,y+64+30*i,a,12,False,C['ink'],ha='left')
 # add text to drawio vertex to retain editable labels
 j=next(k for k,e in enumerate(D.elements) if e[0]==id)
 D.elements[j]=(id,x,y,w,h,header+'\n'+'\n'.join(attrs),'uml',fill,C['blue'],14)
 return (x,y,w,h)
a=cls('uautor',70,180,270,'Autor',['+ idAutor : int {id}','+ nombre : String'])
b=cls('ulibro',465,180,285,'Libro',['+ isbn : String {id}','+ titulo : String','+ anioPublicacion : int','/ edadObra : int'])
c=cls('uejemplar',890,180,295,'Ejemplar',['+ idEjemplar : int {id}','+ codigoInventario : String','+ estado : EstadoEjemplar'])
d=cls('ucoleccion',1405,180,315,'Coleccion',['+ idColeccion : int {id}','+ nombre : String'])
e=cls('upersona',70,685,340,'Persona {abstract}',['+ idPersona : int {id}','+ nombres : String','+ apellidoPaterno : String','+ apellidoMaterno : String','+ correo : String','+ telefonos : List<String>'])
f=cls('uprestamo',700,685,360,'Prestamo',['+ idPrestamo : int {id}','+ fechaSalida : Date','+ fechaLimite : Date','+ fechaDevolucion : Date?','/ diasAtraso : int'])
g=cls('uincidencia',1325,685,370,'Incidencia',['+ idIncidencia : int {id}','+ tipo : TipoIncidencia','+ fecha : Date','+ observacion : String'])
h=cls('uestudiante',100,1090,280,'Estudiante',['+ matricula : String {unique}','+ semestre : int'])
i=cls('udocente',425,1090,280,'Docente',['+ numeroEmpleado : String','+ departamento : String'])
# associations horizontal
D.line('u1',[(340,242),(465,242)],color=C['blue']);D.txt(407,218,'escribe',12,False);D.txt(366,267,'1..*',12);D.txt(444,267,'0..*',12)
D.line('u2',[(750,242),(890,242)],color=C['blue']);D.txt(820,218,'tiene',12);D.txt(775,265,'1',12);D.txt(869,265,'0..*',12)
# composition diamond at Libro
D.ax.add_patch(Polygon([[754,242],[769,233],[784,242],[769,251]],facecolor=C['blue'],edgecolor=C['blue'],zorder=7))
# aggregation catalog-> book routed over top
D.line('u3',[(1560,180),(1560,130),(607,130),(607,180)],color=C['green']);D.txt(1090,105,'agrupa (compartida) 0..* ↔ 0..*',12,False,C['green'])
D.ax.add_patch(Polygon([[1560,184],[1548,165],[1560,147],[1572,165]],facecolor='white',edgecolor=C['green'],zorder=7))
D.line('u4',[(410,750),(700,750)],color=C['blue']);D.txt(550,723,'realiza',12);D.txt(448,772,'1',12);D.txt(668,772,'0..*',12)
D.line('u5',[(1072,344),(1072,578),(890,578),(890,685)],color=C['blue']);D.txt(1150,475,'corresponde',12);D.txt(1115,376,'1',12);D.txt(921,661,'0..*',12)
D.line('u6',[(1060,754),(1325,754)],color=C['blue']);D.txt(1180,725,'registra',12);D.txt(1090,780,'1',12);D.txt(1297,780,'0..*',12)
D.ax.add_patch(Polygon([[1065,754],[1080,745],[1095,754],[1080,763]],facecolor=C['blue'],edgecolor=C['blue'],zorder=7))
# inheritance: subclass nodes to generalization branch
D.line('u7',[(240,1090),(240,1030),(260,1030),(260,913)],color=C['green'])
D.line('u8',[(565,1090),(565,1030),(260,1030)],color=C['green'])
D.ax.add_patch(Polygon([[260,902],[244,928],[276,928]],facecolor='white',edgecolor=C['green'],lw=2,zorder=7))
D.txt(438,1045,'{disjoint, complete}',11,False,C['green'])
D.note(70,1240,1600,48,'Símbolos: rombo negro = composición · rombo blanco = agregación compartida · triángulo blanco = generalización · / = derivado.',12)
D.save(EXP)

# Reports
sty=getSampleStyleSheet();sty.add(ParagraphStyle(name='T',fontName='DVB',fontSize=16,leading=20,textColor=colors.HexColor(C['navy']),spaceAfter=12))
sty.add(ParagraphStyle(name='H',fontName='DVB',fontSize=11.5,leading=16,spaceBefore=13,spaceAfter=6,textColor=colors.HexColor(C['blue'])))
sty.add(ParagraphStyle(name='BodyX',fontName='DV',fontSize=9.6,leading=15,spaceAfter=7,textColor=colors.HexColor(C['ink'])))
sty.add(ParagraphStyle(name='SmallX',fontName='DV',fontSize=8.2,leading=12,spaceAfter=4,textColor=colors.HexColor(C['muted'])))
sty.add(ParagraphStyle(name='CellX',fontName='DV',fontSize=8.1,leading=12,textColor=colors.HexColor(C['ink'])))
sty.add(ParagraphStyle(name='CellBX',fontName='DVB',fontSize=8.2,leading=12,textColor=colors.white))
sty.add(ParagraphStyle(name='CoverT',fontName='DVB',fontSize=22,leading=31,alignment=TA_CENTER,textColor=colors.HexColor(C['navy'])))
sty.add(ParagraphStyle(name='CoverS',fontName='DV',fontSize=12,leading=20,alignment=TA_CENTER,textColor=colors.HexColor(C['blue'])))

def P(x,style='BodyX'): return Paragraph(x,sty[style])
def table(headers,rows,widths=None):
 data=[[P(str(z),'CellBX') for z in headers]]+[[P(str(z),'CellX') for z in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(C['blue'])),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f7fb')]),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),0.7,colors.HexColor('#17416f')),('LINEBELOW',(0,1),(-1,-1),0.25,colors.HexColor('#d6dfeb'))]))
 return t

def add_heading(story,title):story.append(P(title,'H'))
def bullets(story,ls):
 for s in ls: story.append(P('• '+s,'BodyX'))
def footer(canvas,doc):
 canvas.saveState();w,h=A4
 canvas.setStrokeColor(colors.HexColor('#d5e0ea'));canvas.line(42,40,w-42,40)
 canvas.setFont('DV',8);canvas.setFillColor(colors.HexColor(C['muted']))
 canvas.drawString(42,28,'Instituto Tecnológico Superior de Monclova | Fundamentos de Bases de Datos')
 canvas.drawRightString(w-42,28,f'Página {doc.page}')
 canvas.restoreState()
def cover(title,subtitle):
 st=[Spacer(1,100),P('TECNOLÓGICO NACIONAL DE MÉXICO','CoverS'),P('INSTITUTO TECNOLÓGICO SUPERIOR DE MONCLOVA','CoverS'),Spacer(1,44),HRFlowable(width='80%',thickness=3,color=colors.HexColor(C['blue'])),Spacer(1,38),P(title,'CoverT'),Spacer(1,14),P(subtitle,'CoverS'),Spacer(1,65)]
 for label,value in [('Asignatura','Fundamentos de Bases de Datos'),('Unidad','Unidad 2. Diseño de Bases de Datos con el modelo E-R'),('Alumno','Aldo Alberto Barajas Ancira'),('Número de control','I24050397'),('Docente','Rubén Riojas'),('Fecha','7 de noviembre de 2026')]:
  st.append(P('<b>'+label+':</b> '+value))
 st += [Spacer(1,45),P('Caso de estudio académico: biblioteca escolar de una institución de educación superior.','SmallX'),PageBreak()]
 return st

def make_pdf(filename,story,diagrams):
 textpath=filename.with_name('_temporal_'+filename.name)
 SimpleDocTemplate(str(textpath),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=56,bottomMargin=56,title=filename.stem,author='Aldo Alberto Barajas Ancira').build(story,onFirstPage=footer,onLaterPages=footer)
 writer=PdfWriter()
 for pg in PdfReader(str(textpath)).pages:writer.add_page(pg)
 for diagram in diagrams:
  for pg in PdfReader(str(EXP/(diagram+'.pdf'))).pages:writer.add_page(pg)
 with open(filename,'wb') as f:writer.write(f)
 textpath.unlink()
 return len(writer.pages)

s=cover('Tarea 2.1','Modelado conceptual E-R y E-R extendido: biblioteca escolar')
s+=[P('Índice de contenidos','T'),P('1. Resumen y objetivo\n2. Situación problemática y alcance\n3. Reglas de negocio\n4. Entidades y atributos\n5. Relaciones y cardinalidades\n6. E-R extendido: especialización y agregación\n7. Justificación y validación\n8. Conclusiones y fuentes\nAnexos A-C. Diagramas formales de alta resolución'),Spacer(1,12)]
add_heading(s,'1. Resumen y objetivo')
s.append(P('Se modela la administración de préstamos de ejemplares físicos en una biblioteca escolar. El producto es un esquema <b>conceptual</b> independiente del motor de base de datos y diseñado para describir libros, autores, colecciones, ejemplares, usuarios, préstamos e incidencias. Se identifican restricciones de integridad que pueden representarse gráficamente y otras que requieren reglas de aplicación o restricciones adicionales al convertirlo al modelo lógico.'))
s.append(P('Objetivo: documentar el dominio, describir entidades y atributos con notación Chen, precisar cardinalidad mínima y máxima, y extender el esquema mediante generalización y agregación.'))
add_heading(s,'2. Contexto, problemática y alcance')
s.append(P('En una biblioteca de educación superior pueden coexistir registros bibliográficos, múltiples ejemplares de un mismo título y préstamos con fechas de devolución distintas. Un control por hojas de cálculo dificulta identificar la disponibilidad real de una copia, asignar préstamos a personas concretas y conservar evidencia de daños o retrasos. El modelo propuesto es un <b>caso verosímil de estudio</b>; no se afirma que los datos pertenezcan a una institución real.'))
s.append(P('<b>Incluye:</b> catálogo bibliográfico, autores, colecciones temáticas, ejemplares físicos, personas con subtipo estudiante/docente, préstamos históricos e incidencias. <b>Excluye:</b> adquisiciones, pagos, multas monetarias, reservaciones y autenticación de usuarios. Se evita inflar el dominio con procesos ajenos a la competencia de esta tarea.'))
add_heading(s,'3. Reglas de negocio')
rs=[
'RN01. Cada libro se identifica de forma única por ISBN y puede tener cero o muchos ejemplares físicos; cada ejemplar corresponde a un solo libro.',
'RN02. Cada libro tiene al menos un autor registrado; un autor puede participar en varios libros y puede incorporarse antes de publicar un libro en el catálogo.',
'RN03. Una colección temática puede agrupar cero o varios libros y un mismo libro puede aparecer en varias colecciones.',
'RN04. Cada persona se identifica por id_persona y se especializa obligatoriamente en estudiante o docente; los subtipos son excluyentes.',
'RN05. Un estudiante tiene matrícula única; un docente tiene número de empleado único dentro del sistema.',
'RN06. Una persona puede tener cero o muchos préstamos históricos. Cada préstamo corresponde a una persona y un ejemplar físico.',
'RN07. Un ejemplar puede aparecer en múltiples préstamos a lo largo del tiempo, pero nunca en dos préstamos activos simultáneamente.',
'RN08. fecha_límite no puede ser anterior a fecha_salida; fecha_devolucion es opcional mientras la copia no se entregue.',
'RN09. Un préstamo puede ocasionar cero o varias incidencias; cada incidencia pertenece a un solo préstamo.',
'RN10. El historial de préstamos e incidencias se conserva: la baja operativa de libros o usuarios no debe borrar eventos históricos.',
'RN11. Los teléfonos son multivalorados; el nombre se analiza como atributo compuesto; edad_obra y días_atraso son atributos derivados.',
'RN12. La disponibilidad actual resulta del estado del ejemplar y de la ausencia de un préstamo activo, no de un campo redundante editable sin control.'
]
for x in rs:s.append(P(x,'BodyX'))
add_heading(s,'4. Catálogo de entidades y atributos')
s.append(table(['Entidad','Clave','Atributos relevantes / tipo'],[
['Persona','id_persona','nombre {nombres, apellido_paterno, apellido_materno}: compuesto; correo: simple; teléfonos: multivalorado'],
['Estudiante','id_persona (hereda)','matrícula: única; semestre: simple'],
['Docente','id_persona (hereda)','número_empleado: único; departamento: simple'],
['Libro','isbn','título y año_publicación: simples; /edad_obra: derivado'],
['Ejemplar','id_ejemplar','código_inventario: único; estado: simple'],
['Autor','id_autor','nombre: simple'],
['Colección','id_coleccion','nombre: simple'],
['Préstamo','id_prestamo','fecha_salida, fecha_límite, fecha_devolución: simples; /días_atraso: derivado'],
['Incidencia','id_incidencia','tipo, fecha, observación: simples']],widths=[95,100,302]))
s.append(Spacer(1,8));s.append(P('Convención: una barra / marca atributo derivado. Los identificadores de subtipos corresponden al identificador de Persona; no son claves independientes. Los atributos multivalorados se normalizarían posteriormente mediante una relación adicional.','SmallX'))
add_heading(s,'5. Relaciones, cardinalidad y participación')
s.append(P('Se utiliza la expresión (mínimo..máximo) en cada extremo: el valor cercano a una entidad indica cuántas instancias de esa entidad pueden estar relacionadas con una instancia del extremo opuesto. Por ejemplo, junto a Libro se indica 1 (un ejemplar pertenece a un libro) y junto a Ejemplar se indica 0..* (un libro admite muchos ejemplares).'))
s.append(table(['Relación','Cardinalidad y sentido','Participación / restricción'],[
['Autor - ESCRIBE - Libro','Autor: 0..* libros; Libro: 1..* autores','Libro total; Autor parcial'],
['Colección - AGRUPA - Libro','Colección: 0..* libros; Libro: 0..* colecciones','Ambos parcial; N:M'],
['Libro - TIENE - Ejemplar','Libro: 0..* ejemplares; Ejemplar: 1 libro','Ejemplar total'],
['Persona - REALIZA - Préstamo','Persona: 0..* préstamos; Préstamo: 1 persona','Préstamo total'],
['Ejemplar - SOBRE - Préstamo','Ejemplar: 0..* préstamos; Préstamo: 1 ejemplar','Préstamo total'],
['Préstamo - GENERA - Incidencia','Préstamo: 0..* incidencias; Incidencia: 1 préstamo','Incidencia total']],widths=[160,185,152]))
add_heading(s,'6. E-R extendido: especialización y agregación')
s.append(P('<b>Especialización / generalización.</b> Persona es supertipo conceptual abstracto; Estudiante y Docente son subtipos con atributos propios. La regla es <b>total</b> (toda persona del sistema pertenece a un subtipo) y <b>disjunta</b> (no puede pertenecer a los dos a la vez). La figura E-RE representa ambas restricciones con el conector ISA marcado d/T.'))
s.append(P('<b>Agregación.</b> El hecho de que una Persona realiza un Préstamo sobre un Ejemplar se trata como un agregado conceptual AG_EVENTO_PRÉSTAMO. Una Incidencia registra información relativa a ese hecho de negocio. Esto permite hablar de una relación entre una entidad y un hecho compuesto sin introducir una nueva tabla: en una implementación relacional, Incidencia conserva la referencia obligatoria a id_préstamo. La figura de agregación es una <b>vista conceptual adicional</b>, no un segundo préstamo independiente.'))
add_heading(s,'7. Justificación y control de consistencia')
s.append(P('Se separan Libro (obra bibliográfica) y Ejemplar (copia física) para evitar atribuir disponibilidad a un título cuando una sola copia está prestada. Préstamo se trata como entidad de evento, en lugar de esconder fechas y cambios de estado dentro de una relación N:M sin identidad. Los autores y las colecciones usan relaciones N:M porque un libro admite varias autorías y puede integrarse en varios agrupamientos.'))
s.append(P('Se conservan los préstamos históricos en lugar de sustituir el préstamo previo al devolver un libro. La participación obligatoria de Préstamo en Persona y Ejemplar permite impedir eventos huérfanos. El sistema lógico deberá añadir unicidad condicional de préstamos activos, validación temporal y restricciones de borrado, ya que la cardinalidad básica por sí sola no expresa esos invariantes.'))
add_heading(s,'7.1 Ejemplos de validación')
s.append(table(['Caso','Evaluación esperada'],[
['Crear ejemplar sin ISBN asociado','Rechazar: todo ejemplar referencia un Libro'],
['Registrar segundo préstamo activo del mismo ejemplar','Rechazar: no se permiten solapamientos activos'],
['Crear libro sin autores','Rechazar al confirmar alta definitiva; participación Libro 1..*'],
['Registrar persona sin subtipo','Rechazar: especialización total'],
['Registrar persona como docente y estudiante','Rechazar: especialización disjunta'],
['Eliminar préstamo con incidencia','Conservar historial o impedir borrado; evitar cascadas destructivas']],widths=[230,267]))
add_heading(s,'8. Conclusiones')
s.append(P('El modelo E-R aporta una representación verificable del dominio y sus cardinalidades; el E-RE permite formalizar jerarquías y hechos agregados. La principal conclusión es que la calidad del diseño no depende de dibujar muchas entidades sino de justificar claves, dependencias, mínimos de participación y restricciones que puedan verificarse con casos concretos. La conversión a tablas deberá preservar estas decisiones sin confundir propiedades derivadas con datos base.'))
add_heading(s,'Referencias técnicas')
s.append(P('IBM. (2024). <i>What is an entity relationship diagram?</i> https://www.ibm.com/think/topics/entity-relationship-diagram'))
s.append(P('Object Management Group. (2017). <i>Unified Modeling Language, Version 2.5.1.</i> https://www.omg.org/spec/UML/2.5.1/'))
s.append(P('Elaboración propia: caso, reglas de negocio y diagramas académicos en notación Chen simplificada (2026).'))
s.append(P('<b>Anexos:</b> A. E-R conceptual; B. tipos de atributos; C. E-R extendido. Los tres diagramas se entregan además en SVG, PNG, PDF y formato editable Draw.io.','SmallX'))
p1=BASE/'Tarea_2_1'/'Tarea_2_1_Reporte_Tecnico_ER_ERE.pdf';n1=make_pdf(p1,s,['ER_Conceptual','ER_Atributos','ER_Extendido'])

s=cover('Tarea 2.2','Transición del modelo E-R a diagrama de clases UML')
s+=[P('Índice de contenidos','T'),P('1. Propósito y punto de partida\n2. Comparativa E-R contra UML\n3. Conversión de entidades y atributos\n4. Relaciones y sus equivalentes UML\n5. Herencia, composición y agregación\n6. Pérdidas y transformaciones semánticas\n7. Verificación de coherencia\n8. Conclusiones y fuentes\nAnexo D. Diagrama de clases UML de alta resolución'),Spacer(1,12)]
add_heading(s,'1. Propósito y punto de partida')
s.append(P('Se toma <b>exactamente el caso de biblioteca escolar de la Tarea 2.1</b> y se expresa mediante clases UML. El objetivo no consiste en transformar cada tabla hipotética en una clase mecánica, sino en mantener significado, identidad, cardinalidades, subtipo y pertenencia entre objetos en una representación útil para desarrollo orientado a objetos. El modelo se basa en UML 2.5.1 publicado por OMG.'))
add_heading(s,'2. Cuadro comparativo: E-R frente a UML')
s.append(table(['Criterio','E-R / E-RE','Diagrama de clases UML'],[
['Finalidad','Organizar hechos, entidades, atributos y reglas de integridad de datos','Modelar tipos de objetos, propiedades, asociaciones y potencial comportamiento'],
['Unidad principal','Entidad: conjunto de instancias identificables','Clase: tipo de objetos con identidad y propiedades'],
['Propiedades','Atributos simples, compuestos, derivados y multivalorados','Atributos tipados, propiedades derivadas «/» y multiplicidad de colección'],
['Identificador','Atributo clave / clave candidata','Propiedad marcada {id} o restricción de unicidad; no hay PK relacional implícita'],
['Relación','Rombo en Chen, participación y cardinalidad min..max','Asociación con multiplicidades en ambos extremos y nombres de rol'],
['Relación N:M','Relación muchos a muchos entre tipos de entidad','Asociación *-*; en código suele requerir colección en ambos extremos'],
['Especialización','ISA total/parcial, disjunta/solapada','Generalización y conjunto de generalización {complete, disjoint}'],
['Agregación','Tratar una asociación como unidad conceptual de un hecho','No es equivalencia automática de rombo blanco; requiere semántica parte-todo'],
['Composición','Dependencia de existencia puede estar en reglas del dominio','Rombo negro y propiedad exclusiva/propiedad de ciclo de vida'],
['Restricciones','Reglas de negocio y participación sobre datos','Invariantes, multiplicidades, tipos y reglas de operaciones']],widths=[104,194,199]))
add_heading(s,'3. Conversión entidad a clase y atributo a propiedad')
s.append(P('Cada entidad fuerte se lleva a una clase con atributos tipados. Persona conserva el identificador único y se convierte en clase abstracta; Estudiante y Docente heredan su identidad, evitando duplicar idPersona. Préstamo permanece como clase de dominio con fechas e identidad propias, pues se consulta, se cierra y conserva historial.'))
s.append(table(['Entidad E-R','Clase UML','Correspondencia concreta'],[
['Persona','Persona {abstract}','id_persona → idPersona:int; nombre compuesto → nombres/apellidos:String; teléfonos → List&lt;String&gt;'],
['Estudiante','Estudiante','matrícula → matricula:String {unique}; semestre:int'],
['Docente','Docente','numero_empleado → numeroEmpleado:String; departamento:String'],
['Libro','Libro','isbn:String {id}; titulo:String; anioPublicacion:int; /edadObra:int'],
['Ejemplar','Ejemplar','idEjemplar:int; codigoInventario:String; estado:EstadoEjemplar'],
['Autor','Autor','idAutor:int; nombre:String'],
['Colección','Coleccion','idColeccion:int; nombre:String'],
['Préstamo','Prestamo','idPrestamo:int; fechas:Date; /diasAtraso:int'],
['Incidencia','Incidencia','idIncidencia:int; tipo:TipoIncidencia; fecha:Date']],widths=[105,120,272]))
add_heading(s,'3.1 Conversión de atributos especiales')
s.append(P('<b>Compuesto:</b> nombre se desglosa en propiedades simples de Persona; se podría usar un objeto valor Nombre, pero no se introduce una nueva entidad sin necesidad. <b>Multivalorado:</b> teléfonos se interpreta como colección de cadenas, con cardinalidad 0..*. <b>Derivado:</b> edadObra y diasAtraso se marcan con / y se calculan usando fecha de consulta o fecha de devolución; su presencia no obliga a persistirlas físicamente. <b>Claves:</b> {id} indica identidad conceptual; no es una palabra clave obligatoria de UML.'))
add_heading(s,'4. Correspondencia de relaciones con multiplicidad')
s.append(table(['Relación E-R','Asociación UML','Justificación'],[
['Autor - Libro (N:M)','Autor 0..* — 1..* Libro','Un libro requiere autor; autores pueden estar registrados previamente'],
['Colección - Libro (N:M)','Coleccion 0..* ◇— 0..* Libro','Agregación compartida por agrupación temática: el libro existe fuera de la colección'],
['Libro - Ejemplar (1:N)','Libro 1 ◆— 0..* Ejemplar','Composición: ejemplar es objeto contenido por la ficha bibliográfica en el sistema'],
['Persona - Préstamo (1:N)','Persona 1 — 0..* Prestamo','Cada evento corresponde a una persona identificada'],
['Ejemplar - Préstamo (1:N)','Ejemplar 1 — 0..* Prestamo','Las copias se prestan repetidamente en el tiempo, nunca dos veces activas a la vez'],
['Préstamo - Incidencia (1:N)','Prestamo 1 ◆— 0..* Incidencia','La incidencia existe y se administra en el contexto del préstamo']],widths=[160,162,175]))
s.append(P('Importante: el nombre junto a cada clase representa el tipo de objeto; los multiplicadores indican cuántos objetos opuestos corresponden a uno de ese tipo. La restricción de <b>un préstamo activo por ejemplar</b> permanece como invariante adicional y no se deduce de 0..* préstamos históricos.'))
add_heading(s,'5. Herencia, composición y agregación')
s.append(P('<b>Herencia.</b> Las flechas con triángulo vacío apuntan desde Estudiante y Docente hacia Persona. La anotación {disjoint, complete} representa que los subtipos son mutuamente excluyentes y exhaustivos en este dominio. UML no convierte la generalización, por sí sola, en una estrategia concreta de almacenamiento relacional.'))
s.append(P('<b>Composición.</b> Libro posee Ejemplar de manera exclusiva <i>dentro de este modelo de biblioteca</i>; Ejemplar no se registra como copia sin título y no puede pertenecer simultáneamente a dos libros. Asimismo, Incidencia se modela como parte dependiente del registro de Préstamo. Esta composición indica propiedad lógica y ciclo de vida coordinado, pero <b>no autoriza borrar el historial</b>: la aplicación prohíbe eliminación física de eventos auditables.'))
s.append(P('<b>Agregación compartida.</b> Colección agrupa Libros: una obra puede pertenecer a varias colecciones, y quitarla de una colección no destruye la obra. Por ello el rombo es vacío. La agregación E-RE del hecho de préstamo, por su parte, <b>no se traduce automáticamente</b> al rombo blanco UML: es una abstracción de relaciones; en UML el hecho se representa explícitamente con la clase Prestamo y sus asociaciones.'))
add_heading(s,'6. Análisis crítico de coincidencias y diferencias')
s.append(P('La correspondencia es sólida para entidades con identidad estable, atributos y asociaciones; no obstante, los diagramas cumplen roles diferentes. E-R se centra en persistencia e integridad informacional, mientras que UML también puede representar comportamiento, navegación, encapsulación y ciclo de vida de objetos. Por ello una clase no debe confundirse con una tabla: una clase puede representar un objeto valor o un servicio y una relación N:M puede requerir una tabla puente sin producir una clase de dominio adicional.'))
s.append(P('En E-R una participación mínima puede expresarse con números en cada extremo; en UML las multiplicidades usan 1, 0..1, 0..*, 1..*, etc. En ambos modelos la restricción temporal «mismo ejemplar no tiene dos préstamos activos» requiere expresión adicional: una regla de servicio, invariante formal o índice único condicional. Las restricciones de especialización también deben aplicarse en la lógica de negocio y, cuando sea posible, mediante restricciones en la base de datos.'))
add_heading(s,'7. Matriz de verificación de trazabilidad')
s.append(table(['Regla origen','Evidencia E-R','Evidencia UML / control adicional'],[
['RN01','Libro 0..* - Ejemplar 1','Composición Libro ◆— Ejemplar; idEjemplar obligatorio'],
['RN02','Autor 0..* - Libro 1..*','Asociación con multiplicidad mínima 1 del lado autor'],
['RN03','Colección 0..* - Libro 0..*','Agregación compartida, sin propiedad exclusiva de Libro'],
['RN04','Persona ISA Estudiante/Docente total-disjunta','Herencia {complete, disjoint} más validación de alta'],
['RN06/RN07','Préstamo pertenece a Persona y Ejemplar','Asociaciones obligatorias; impedir doble préstamo activo'],
['RN09/RN10','Incidencia 1 Préstamo, histórico conservado','Composición e invariante «no borrar eventos históricos»'],
['RN11','Multivalorado, compuesto, derivado','List<String>, atributos de nombre y propiedades /']],widths=[105,165,227]))
add_heading(s,'8. Conclusión')
s.append(P('La transición E-R → UML conserva entidades de negocio, identidad y multiplicidad sin necesidad de añadir tecnología o código. El cambio más relevante es semántico: al elegir composición y agregación se declaran reglas de propiedad del dominio, no simplemente relaciones de claves foráneas. Una conversión responsable deja registradas las restricciones que los diagramas no pueden garantizar por sí solos y conserva una relación de trazabilidad con las reglas del caso inicial.'))
add_heading(s,'Referencias técnicas')
s.append(P('Object Management Group. (2017). <i>Unified Modeling Language, Version 2.5.1.</i> https://www.omg.org/spec/UML/2.5.1/'))
s.append(P('IBM. (2024). <i>What is an entity relationship diagram?</i> https://www.ibm.com/think/topics/entity-relationship-diagram'))
s.append(P('Modelo y conversión UML de elaboración propia para fines académicos (2026).'))
s.append(P('<b>Anexo D:</b> diagrama completo UML; editable en el archivo UML_Clases.drawio y exportado también en PDF, SVG y PNG.','SmallX'))
p2=BASE/'Tarea_2_2'/'Tarea_2_2_Comparativa_ER_UML.pdf';n2=make_pdf(p2,s,['UML_Clases'])

# supplemental files
(BASE/'README.md').write_text('''# Unidad 2 — Modelado E-R y UML | Biblioteca escolar\n\n**Alumno:** Aldo Alberto Barajas Ancira · **No. control:** I24050397  \n**Asignatura:** Fundamentos de Bases de Datos · **Docente:** Rubén Riojas\n\n## Contenido\n\n- `Tarea_2_1/Tarea_2_1_Reporte_Tecnico_ER_ERE.pdf`: reporte conceptual y E-RE con diagramas anexos.\n- `Tarea_2_2/Tarea_2_2_Comparativa_ER_UML.pdf`: correspondencia E-R / UML y diagrama de clases.\n- `Diagramas_Editables/*.drawio`: cuatro archivos fuente editables para diagrams.net (uno por vista).\n- `Diagramas_Exportados/`: los cuatro diagramas en PDF vectorial, SVG y PNG de alta resolución.\n- `Guias/GUIA_GITHUB_YOUTUBE.md`: publicación de repositorio y grabación de dos videos.\n- `generar_entregables.py`: generador reproducible de los artefactos.\n\n## Cómo abrir/editar\n\n1. Ir a https://app.diagrams.net/ .\n2. Archivo > Abrir desde > Dispositivo y seleccionar un `.drawio`.\n3. Modificar los objetos, líneas y etiquetas editables.\n4. Archivo > Exportar como > PDF / PNG / SVG para obtener nuevas versiones.\n\n**Caso:** biblioteca escolar ficticia verosímil (no representa datos reales ni modifica el proyecto integrador de ferretería).\n\n**Aviso:** los diagramas impresos fueron generados desde un mismo esquema semántico; los ficheros `.drawio` recrean sus nodos y conexiones de forma editable.\n**Pendiente a cargo del alumno:** subir el contenido a un repositorio *público* de GitHub y grabar/publicar dos videos en un único canal público de YouTube con webcam inferior derecha.\n''',encoding='utf-8')
(BASE/'Guias'/'GUIA_GITHUB_YOUTUBE.md').write_text('''# Guía de publicación y defensa oral — Unidad 2\n\n## Repositorio GitHub público\n1. Crear repositorio `unidad-2-modelado-er-uml` con visibilidad **Public** en tu cuenta.\n2. Cargar las carpetas `Tarea_2_1`, `Tarea_2_2`, `Diagramas_Editables`, `Diagramas_Exportados`, `Guias` y `README.md`.\n3. Comprobar con sesión cerrada que los archivos `.drawio`, `.pdf` y `.png` puedan descargarse.\n4. Copiar enlace real del repositorio (sin inventar la URL). Usar el MISMO repositorio en ambas tareas si la rúbrica no exige dos.\n\n## Video público 2.1 (orientativo 6-9 minutos)\n- 0:00 Presentación y contexto de la biblioteca escolar.\n- 0:45 Problema realista: diferencia Libro frente a Ejemplar y préstamos históricos.\n- 1:50 Reglas RN01–RN12 y su relevancia.\n- 3:00 Abrir ER_Conceptual.drawio, explicar entidades y cardinalidades.\n- 4:30 Abrir ER_Atributos.drawio: clave, compuesto, multivalorado, derivado.\n- 5:30 Abrir ER_Extendido.drawio: ISA total-disjunta y agregación conceptual.\n- 6:30 Defender decisiones y explicar el control del préstamo activo.\n- 7:30 Resumen y conclusión.\n\n## Video público 2.2 (orientativo 6-8 minutos)\n- 0:00 Presentación y objetivo de conversión E-R a UML.\n- 0:45 Entidad → clase; clave → atributo con identificador.\n- 1:45 Contrastar cardinalidades en diagramas E-R y UML.\n- 3:00 Explicar herencia Persona → Estudiante / Docente.\n- 4:00 Explicar composición Libro-Ejemplar y Préstamo-Incidencia.\n- 4:50 Explicar agregación compartida Colección-Libro, frente a agregación E-RE del evento de préstamo.\n- 6:00 Distinguir modelo de información, código y restricciones adicionales.\n- 7:00 Conclusión.\n\n## Grabación recomendada (OBS)\n1. Crear escena con captura de pantalla y webcam.\n2. Colocar webcam visible en **esquina inferior derecha**; evitar tapar títulos del diagrama.\n3. Abrir PDFs y drawio durante la explicación; zoom para legibilidad.\n4. Verificar micrófono e imagen antes de grabar.\n5. Publicar ambos videos con visibilidad **Público** en el **mismo canal**.\n6. Pegar los enlaces reales en Teams junto a los PDF y GitHub.\n\n## Lista de comprobación\n- [ ] PDF tarea 2.1\n- [ ] PDF tarea 2.2\n- [ ] Repositorio GitHub público con editables y exportaciones\n- [ ] Video 2.1 público; webcam inferior derecha\n- [ ] Video 2.2 público; webcam inferior derecha\n- [ ] Ambos videos en el mismo canal\n''',encoding='utf-8')
# ZIP only final deliverables, exclude source generator? include since useful and reproducible
out=Path('/mnt/data/Unidad_2_Entregables_Completos.zip')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for path in sorted(BASE.rglob('*')):
  if path.is_file() and not path.name.startswith('_'):z.write(path,path.relative_to(BASE.parent))
print('DONE',n1,n2,out,round(out.stat().st_size/1024/1024,2),'MB')
print('pdfs:',p1,p1.stat().st_size,p2,p2.stat().st_size)
