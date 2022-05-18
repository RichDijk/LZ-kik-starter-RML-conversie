# Create sparql query UI
# aantal triples na query

# TODO: Wijzig paden voor testbestanden nadat de RML is aangemaakt
# TODO: Verplaats draaien van de query's naar in de buurt van de conversie knop.
# TODO: Allign left van  query result tabel
# TODO: Parse converted data without running a conversion.

import sys

from PyQt5.QtCore import right
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import * #QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtGui import QPainter, QPen

from rdflib import Graph, RDF, RDFS, SH, OWL, XSD
import yaml
from yaml.loader import SafeLoader

import petl as etl
#from petl import dateparser
import io, csv, os, sys, subprocess, datetime
import dateparser #https://dateparser.readthedocs.io/en/latest/introduction.html
import traceback
import pandas as pd

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.testMode = False
        self.statusBar().showMessage(f"Test mode: False")

        # self.graph = Graph().parse("kennedys.ttl")
        self.curFile = ''
        self.queryEdit = QTextEdit()
        self.graph = None
        self.rdfdata = None
        # self.graph_type = dict(model=None, constrained=None, data=None)
        self.configTxt = QTextBrowser()
        self.rmlmappingTxt = QTextBrowser()
        self.execButton = QPushButton('Draai conversie.')
        self.execButton.setCheckable(True)
        self.execButton.clicked.connect(self.draaiConversie)

        self.resultPane = QTextBrowser()

        self.tabs = QTabWidget()
        self.tab_table = QTableWidget()
        self.tab_table.setSortingEnabled(True)
        self.tab_basisquery = QTextBrowser()
        self.tab_analyse = QTextBrowser()
        self.tab_validatie = QTextBrowser()

        page_layout = QGridLayout()
        # top_layout = QHBoxLayout()      
        # middle_layout = QHBoxLayout()  
        # bottom_layout = QHBoxLayout()

        self.tabs.addTab(self.tab_table,"RDF data (max 1000 triples)")
        self.tabs.addTab(self.tab_validatie,"Validatie resultaat")
        self.tabs.addTab(self.tab_basisquery,"Basis query resultaat") #tab_json
        self.tabs.addTab(self.tab_analyse, "Technische data analyse")

        page_layout.addWidget(self.configTxt, 0, 0)
        page_layout.addWidget(self.rmlmappingTxt, 0, 1)
        # page_layout.addWidget(self.queryEdit, 0, 1)
        page_layout.addWidget(self.execButton, 1, 0, 1, 2)
        page_layout.addWidget(self.tabs, 2, 0, 1, 2)
        
        # page_layout.addWidget(top_layout)
        # page_layout.addWidget(middle_layout)
        # page_layout.addWidget(bottom_layout)
        
        widget = QWidget()
        widget.setLayout(page_layout)
        self.setCentralWidget(widget)

        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()

        self.readSettings()

        self.queryEdit.document().contentsChanged.connect(self.documentWasModified)

        self.setCurrentFile('')
        self.setUnifiedTitleAndToolBarOnMac(True)

        # Lees config, bij start niet in test mode
        try:
            with open('config.yaml') as f:
                self.config = yaml.load(f, Loader=SafeLoader)

            self.configTxt.setText(yaml.dump(self.config))
        except: 
            traceback.print_exception()
            QMessageBox.about(self, "Fout",
               "config.yaml staat niet bij de exe")

        # Lees RML mapping
        try:
            rmlbestand = self.lees_uit_config('rmlbestand')
            path_rml_mapping = self.lees_uit_config('path_rml_mapping')
            self.rmlMapping = Graph().parse(f"{path_rml_mapping}/{rmlbestand}")
            self.rmlmappingTxt.setText(self.rmlMapping.serialize())
        except:
            traceback.print_exception()
            QMessageBox.about(self, "Fout",
                "RML mapping kan niet gevonden worden.")

    def toggletestmode(self):
        # And update config file
        if self.testMode: 
            self.unsetTestMode()
        else:
            self.setTestMode()
        
    def setTestMode(self):
        # And update config file
        self.testMode = True
        self.updateConfig()
        self.updateRmlMapping()
        self.statusBar().showMessage(f"Test mode: True, config and RML updated")
        self.toggleTestModeAct.setFont(QFont("Segoe UI", 9, QFont.Bold))
        
    def unsetTestMode(self):
        # And update config file
        self.testMode = False
        self.updateConfig()
        self.updateRmlMapping()
        self.statusBar().showMessage(f"Test mode: False, config and RML updated")
        self.toggleTestModeAct.setFont(QFont("Segoe UI", 9, QFont.Normal))
        
    def createTestRMLfromProdRML(self):
        """Vervang de testpaden door productiepaden."""
        # setTestMode en lees parameters
        # unsetTestMode en lees parameters
        # Lees path_bron_data
        # Lees path_update_data
        # path_bron_inrichting

        def remove_dotslash(path):
            if path[0:2] == './':
                return path[2:]
            else:
                return path
        # path_rml_mapping
        print('Changing RML file')
        self.unsetTestMode()
        #print(self.testMode,self.config)
        #path_bron_data = remove_dotslash(self.lees_uit_config('path_update_data'))
        path_update_data = remove_dotslash(self.lees_uit_config('path_bron_data'))
        path_inrichting = remove_dotslash(self.lees_uit_config('path_inrichting'))

        path_rml_mapping = self.lees_uit_config('path_rml_mapping')
        rmlbestand = self.lees_uit_config('rmlbestand')
        #self.rmlMapping = Graph().parse(f"{path_rml_mapping}/{rmlbestand}")
        
        self.setTestMode()
        #print(self.testMode,self.config)
        #path_bron_data_test = remove_dotslash(self.lees_uit_config('path_bron_data'))
        path_update_data_test = remove_dotslash(self.lees_uit_config('path_bron_data'))
        path_inrichting_test = remove_dotslash(self.lees_uit_config('path_inrichting'))

        path_rml_mapping_test = self.lees_uit_config('path_rml_mapping')
        rmlbestand_test = self.lees_uit_config('rmlbestand')
        print(f"{path_rml_mapping_test}/{rmlbestand_test}")
        f1 = open(f"{path_rml_mapping}/{rmlbestand}", 'r')
        f2 = open(f"{path_rml_mapping_test}/{rmlbestand_test}", 'w')
        for line in f1:
            print(path_update_data_test, line)
            if path_update_data_test in line or path_inrichting_test in line:
                print('found!')
                if path_update_data_test in line:
                    f2.write(line.replace(path_update_data_test, path_update_data))
                if path_inrichting_test in line:
                    f2.write(line.replace(path_inrichting_test, path_inrichting))
            else:
                f2.write(line)
        f1.close()
        f2.close()

    def closeEvent(self, event):
        if self.maybeSave():
            self.writeSettings()
            event.accept()
        else:
            event.ignore()

    def newFile(self):
        if self.maybeSave():
            self.queryEdit.clear()
            self.setCurrentFile('')

    def open(self):
        if self.maybeSave():
            fileName, filtr = QFileDialog.getOpenFileName(self)
            if fileName:
                self.loadFile(fileName)

    def save(self):
        if self.curFile:
            return self.saveFile(self.curFile)

        return self.saveAs()

    def saveAs(self):
        fileName, filtr = QFileDialog.getSaveFileName(self)
        if fileName:
            return self.saveFile(fileName)

        return False

    def about(self):
        QMessageBox.about(self, "About RDF app",
                "This <b>RDF app</b> gives functions for working with RDF graphs."
                "Queries and graphs can be loaded.")

    def display_config(self):
        pass

    def updateConfig(self):
        #try:
        if self.testMode:
            with open('config_test.yaml') as f:
                self.config = yaml.load(f, Loader=SafeLoader)        
        else:
            with open('config.yaml') as f:
                self.config = yaml.load(f, Loader=SafeLoader)        

        self.configTxt.setText(yaml.dump(self.config))
        #except:
        #    QMessageBox.about(self, "Fout",
        #        "config.yaml en/of config_test.yaml staat(n) niet bij de exe")

    def updateRmlMapping(self):
        #try:
        path_rml_mapping = self.lees_uit_config('path_rml_mapping')
        rmlbestand = self.lees_uit_config('rmlbestand')
        #if self.testMode:
        #rmlbestand = self.lees_uit_config('rmlbestand')
        self.rmlMapping = Graph().parse(f"{path_rml_mapping}/{rmlbestand}")
        #else:
        #self.rmlMapping = Graph().parse('mapping.rml.ttl')
        self.rmlmappingTxt.setText(self.rmlMapping.serialize())
        #except:
        #    QMessageBox.about(self, "Fout",
        #        "RML mapping bestand staat niet bij de exe")

    def lees_uit_config(self, par):
        # dict_keys(['new-col', 'col1', 'col2', 'files'])
        # dict_keys(['rmlbestand'])
        # dict_keys(['rdfdata'])
        # dict_keys(['rmlmapper'])
        result = False
        for item in self.config:
            for itemkeys in item.keys():
                if par in itemkeys:
                    result = item[par]
        return result

    def lees_dict_uit_config(self,par):
        result = False
        for item in self.config:
            for itemkeys in item.keys():
                if par in itemkeys:
                    result = item
        return result

    def draaiValideerRDF(self):
        """Lees ahscl shapes en draai shacl engine"""
        from pyshacl import validate
        import pandas as pd

        try:
        #data_graph = Graph().parse('data_import/rdf-lz-20220505.nt')
            print('Start validatie: ', datetime.datetime.now())
            shape_graph = Graph().parse('personeleSamenstellingShapes.ttl')

            # Read shapes file and offer a node selection model window

            shapes = shape_graph.triples((None, RDF.type, SH.NodeShape ))
            print(shapes)

            r = validate(self.rdfdata,
                shacl_graph=shape_graph,
                ont_graph=None,
                inference='rdfs',
                abort_on_first=False,
                allow_infos=False,
                allow_warnings=False,
                meta_shacl=False,
                advanced=True,
                js=False,
                debug=False)
            conforms, results_graph, results_text = r

            self.tab_validatie.setText(results_graph.serialize())
            results_graph.serialize('rdfdata-validatie-result.ttl')
            print('Einde validatie: ', datetime.datetime.now())

        except:
            QMessageBox.warning(self, 'Info', 'Geen RDF data beschikbaar, draai de conversie.' )

    def draaiBasisQuerys(self):
        """Draai enkele tel en sommatie basis query's om 
        gevoel voor de data te krijgen.
        Graaf analyse:
        - aantal instanties per klasse
        - aantal instanties per propertie
        """
        if self.rdfdata:
            # sparql = self.queryEdit.toPlainText()
            print(os.curdir)
            # os.chdir('sparql')
            allresulttxt = ""
            for file in os.listdir('sparql'):
                with open(f"sparql/{file}", 'r') as f:
                    qtxt = f.read()
                    try:
                        result = self.rdfdata.query(qtxt)
                        df = pd.DataFrame([t for t in result], columns=result.vars)
                        df.style.set_properties(**{'text-align': 'left'})
                        allresulttxt += f"{file[:-3]}\n"
                        allresulttxt += f"{df.to_string(justify='right')}\n\n"
                    except:
                        print('Fout in query', file, '\n')
                        print(file)
                        allresulttxt += f"Fout in {file}\n\n"
                        traceback.print_exc()

            # variables are unknown
            self.tab_basisquery.setText(allresulttxt)
        else:
            QMessageBox.warning(self, 'Info', 'Geen RDF data beschikbaar, draai de conversie.' )

    def draaiAnalyseQuerys(self):
        """Draai technische query's die op iedere graaf van toepassing zijn.
        Graaf analyse:
        - aantal instanties per klasse
        - aantal instanties per propertie
        """
        prefix_part = self.lees_uit_config('unique_data_prefix_part')
        if self.rdfdata:
            #sparql = self.queryEdit.toPlainText()
            analysis_querys = {
            'aantal triples' : """
            SELECT (count(*) AS ?aantal) 
            WHERE {
                ?s ?p ?o
            }
            """ ,

            'aantal classes' : """
            SELECT ?clss (count(?clss) AS ?clsscount)  
            WHERE {
                ?s a ?clss
                #FILTER ( contains(str(?s), 'lz'))
                #FILTER (!isBlank(?clss))
            }
            GROUP BY ?clss
            """ ,

            'aantal properties' : """
            SELECT ?prop (count(?prop) AS ?propcount)  
            WHERE {
                ?s ?prop ?clss
                #FILTER ( contains(str(?s), 'lz'))
                #FILTER (!isBlank(?cass))
            }
            GROUP BY ?prop
            """
            }

# d = [ ["Mark", 12, 95],
#      ["Jay", 11, 88],
#      ["Jack", 14, 90]]
     
# print ("{:<8} {:<15} {:<10}".format('Name','Age','Percent'))

# for v in d:
#     name, age, perc = v
#     print ("{:<8} {:<15} {:<10}".format( name, age, perc))

            resultText = ""
            for q in analysis_querys:
            #resultText = "Aantal triples: "
                qresult = self.rdfdata.query(analysis_querys[q])
                df = pd.DataFrame([t for t in qresult], columns=qresult.vars)
                resultText += f"{q}\n"
                resultText += f"{df.to_string()}\n\n"                
            self.tab_analyse.setText(resultText)
        else:
            QMessageBox.warning(self, 'Info', 'Geen RDF data beschikbaar, draai de conversie.' )


    def bronDataTransformatie(self):
        # Varianten
        # 1-15-2021 12:00:00 AM
        # 1-15-2021 12:00:00
        # 1-4-2021 00:00
        # 1-15-2021

        def transform_date_time_dash(row):
            """Kijk naar datum velden in het formaat d-m-J hh:mmm:(ss) (AM) en zet dez om in J-m-d"""
            row_updated = []
            for value in row:
                if (value.count('-') == 2 and ',' not in value) or value.count('/') == 2:
                    date = dateparser.parse(value).strftime("%Y-%m-%d") # Parse and write
                    if value != date:
                        row_updated.append(date)
                    else:
                        row_updated.append(value)
                else:
                    row_updated.append(value)
            return row_updated 


        def transform_decimal(row):
            """Kijk naar , in string en zet deze om naar ."""
            row_updated = []
            for value in row:
                if ',' in value:
                    row_updated.append(float(value.replace(",", ".")))
                else:
                    row_updated.append(value)
            return row_updated

        def transform_time(row):
            """Kijk naar : en lengte 5 in string en zet deze om naar -"""
            try:
                row_updated = []
                for value in row:
                    value_old = value
                    if ':' in value and len(value)==5:
                        #print('if: ',value)
                        row_updated.append(value.replace(":", "-"))
                    else:
                        row_updated.append(value)
            except:
                pass
                #print('error: ', value_old, '->', value)
            return row_updated

        def mergeColumnValues(val, row):
            result = 'Error'
            try:
                result = f"{row[self.mergeColDict['col1']]}-{row[self.mergeColDict['col2']]}"
            except:
                traceback.print_exc()
            return result
             
        # Leef relevante bestandsnamen uit config file
        print('Data transformatie start', datetime.datetime.now())

        bron_bestanden = self.lees_uit_config('bronbestanden')
        new_columns = self.lees_uit_config('new-cols') 
        self.path_bron_data = self.lees_uit_config('path_bron_data')

        # lees path bestanden
        # if self.testMode:
        #     self.path_bron_data = self.lees_uit_config('path_bron_data_test')
        # else:
        #     self.path_bron_data = self.lees_uit_config('path_bron_data')
        i = 1
        for bronfilename in bron_bestanden:
            #if self.testMode:
            print(f'Start met {i} van {len(bron_bestanden)} ', bronfilename)
            i = i + 1
            df = etl.fromcsv(f"{self.path_bron_data}/{bronfilename}", delimiter=';' )
            #else:
            #    df = etl.fromcsv(f"{self.path_bron_data}/{bronfilename}", delimiter=';' )
            #table = etl.convertnumbers(df)
            header = df[0]
            table = etl.rowmap(df, transform_date_time_dash, header=header) #seraches for 2x'-
            table = etl.rowmap(table, transform_time, header=header) # searches for :

            # Lees bestanden waarin kolommen moeten worden aangemaakt.
            if new_columns:
            #new_columns = self.lees_uit_config('new-cols')
                for new_column in new_columns:
                    print('Adding new column ', new_column)

                    new_column_def = self.lees_dict_uit_config(new_column)
                    self.mergeColDict = dict(
                        col1=new_column_def['col1'],
                        col2=new_column_def['col2'])
                    if bronfilename in new_column_def['files']:
                        table = etl.addcolumn(table, new_column, [])
                        table = etl.convert(table, new_column, mergeColumnValues, pass_row=True)
                        header = etl.header(table)

            table = etl.rowmap(table, transform_decimal, header=header) # seraches for , and replace with .
            if self.testMode:
                etl.tocsv(table, f'data_bron_update_test/{bronfilename}', delimiter=',' )
            else:
                etl.tocsv(table, f'data_bron_update/{bronfilename}', delimiter=',' )

        print('Data transformatie gereed', datetime.datetime.now())

    def draaiConversie(self):
        rmlmapperjar = self.lees_uit_config('rmlmapperjar')
        rmlbestand = self.lees_uit_config('rmlbestand')
        path_rml_mapping = self.lees_uit_config('path_rml_mapping')
        rdfdata = self.lees_uit_config('rdfdata')
        print('Start conversie: ', datetime.datetime.now())
        #try:
        process = subprocess.Popen(['java', '-jar', rmlmapperjar, '-m', f"{path_rml_mapping}/{rmlbestand}", '-o', rdfdata], 
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stderr != b'':
            QMessageBox.warning(self, "RML conversie Fout", str(stderr))
        #except:
        #    QMessageBox.warning(self, "RML conversie Fout",
        #                    "Cannot read file.")
        # 08:52:45.818 [main] ERROR be.ugent.rml.cli.Main               .main(393) - E:\ZiN\kik-starter\pilots\Lelie Zorggroep\r2rdf\data_bron_update\Beaufort.csv (The system cannot find the file specified)
        # Hoe af te vangen als er een melding is en een onbetrouwbaar resultaat is ontstaan?

        print('Conversie klaar, updating view: ', datetime.datetime.now())
        # Update RDF data view
        try:
            self.rdfdata = Graph().parse(rdfdata)
        
            #sparql = self.queryEdit.toPlainText()
    #        result = list(self.rdfdata.triples((None, None, None))) #.query(sparql)
    #        column_count = 3 #len(result.vars)
    #        if len(result) > 1000:
    #            row_count = 1000
    #        else:
    #            row_count = len(result)

            # Empty existing table
    #        while self.tab_table.rowCount() > 0:
    #            self.tab_table.removeRow(0)
            # Kan verbetert worden wellicht via
            # https://stackoverflow.com/questions/28218882/how-to-insert-and-remove-row-from-model-linked-to-qtableview
    #        self.tab_table.clear() #Deze methode duurt lang en is onbetrouwbaar na sorteren

            # Fill table tab
    #        self.tab_table.destroy()
    #        self.tab_table.setRowCount(row_count)
    #        self.tab_table.setColumnCount(column_count)
    #        self.tab_table.setHorizontalHeaderLabels(['Subject', 'Property', 'Object'])

    #         for row, r in zip(result, range(row_count)):
    #         #r=0
    #         #print(len(result))
    # #            for row in result:
    #             #for row in result:
    #                 #for var, c in zip(result.vars, range(column_count)):
    #             for c in range(column_count):
    #                 item = QTableWidgetItem(row[c])
    #                 self.tab_table.setItem(r, c, item)
                
        #    for _ in range(column_count):
        #        #self.tab_table.setColumnWidth(_, 450)
        #        print('Fout query van resultaat'
        except:
            traceback.print_exc()
            QMessageBox.warning(self, 'Fout', 'Geen RDF data kunnen maken.' )

    def documentWasModified(self):
        self.setWindowModified(self.queryEdit.document().isModified())

    def createActions(self):
        self.toggleTestModeAct = QtGui.QAction("Toggle testmode", self,
                                               statusTip="Toggle testmode", triggered=self.toggletestmode)

        self.updateConfigAct = QtGui.QAction("Update configuratie", self,
                statusTip = "Lees bestandsconfiguratie", triggered=self.updateConfig)

        self.updateRmlMappingAct = QtGui.QAction("Update RML mapping", self,
                statusTip = "Lees bestand voor RML mapping", triggered=self.updateRmlMapping)

        self.draaiConversieAct = QtGui.QAction("Draai conversie", self,
                statusTip = "Draai conversie en creeer RDF data", triggered=self.draaiConversie)


        self.createTestRMLfromProdRMLAct = QtGui.QAction("Creeer RML met test paden", self,
                statusTip = "Creeer RML met test paden", triggered=self.createTestRMLfromProdRML)

        self.newAct = QtGui.QAction(QtGui.QIcon(':/images/new.png'), "&New",
                self, shortcut=QtGui.QKeySequence.New,
                statusTip="Create a new file", triggered=self.newFile)

        self.openAct = QtGui.QAction(QtGui.QIcon(':/images/open.png'),
                "&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file", triggered=self.open)

        self.saveAct = QtGui.QAction(QtGui.QIcon(':/images/save.png'),
                "&Save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to disk", triggered=self.save)

        self.saveAsAct = QtGui.QAction("Save &As...", self,
                shortcut=QtGui.QKeySequence.SaveAs,
                statusTip="Save the document under a new name",
                triggered=self.saveAs)

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application", triggered=self.close)

        self.cutAct = QtGui.QAction(QtGui.QIcon(':/images/cut.png'), "Cu&t",
                self, shortcut=QtGui.QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.queryEdit.cut)

        self.copyAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "&Copy", self, shortcut=QtGui.QKeySequence.Copy,
                statusTip="Copy the current selection's contents to the clipboard",
                triggered=self.queryEdit.copy)

        self.pasteAct = QtGui.QAction(QtGui.QIcon(':/images/paste.png'),
                "&Paste", self, shortcut=QtGui.QKeySequence.Paste,
                statusTip="Paste the clipboard's contents into the current selection",
                triggered=self.queryEdit.paste)

        self.aboutAct = QtGui.QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.bronDataTransformatieAct = QtGui.QAction("Transformatie bron data", self,
                statusTip="Lees orginele data en pas nodige transformaties toe zoals datum formaat.",
                triggered = self.bronDataTransformatie
                )

        self.draaiValideerRDFAct = QtGui.QAction("Valideer RDF data", self,
                statusTip = "Valideer aangemaakte RDF data.",
                triggered = self.draaiValideerRDF
                )

        self.draaiBasisQuerysAct = QtGui.QAction("Draai basis query's", self,
                statusTip = " Draai sparql query's voor basis data.",
                triggered = self.draaiBasisQuerys
                )

        self.draaiAnalyseQuerysAct = QtGui.QAction("Draai analyse query's", self,
                statusTip = "Draai algemene analyse sparql query's.",
                triggered = self.draaiAnalyseQuerys
                )

        # self.cutAct.setEnabled(False)
        # self.copyAct.setEnabled(False)
        # self.queryEdit.copyAvailable.connect(self.cutAct.setEnabled)
        # self.queryEdit.copyAvailable.connect(self.copyAct.setEnabled)

    def createMenus(self):
        #self.graphMenu = self.menuBar().addMenu("&Graph")
        #self.graphMenu.addAction(self.openGraphAct)

        self.fileMenu = self.menuBar().addMenu("&File")
        # self.fileMenu.addAction(self.newAct)
        # self.fileMenu.addAction(self.openAct)
        # self.fileMenu.addAction(self.saveAct)
        # self.fileMenu.addAction(self.saveAsAct)
        # self.fileMenu.addSeparator()
        # self.fileMenu.addAction(self.exitAct)
        self.fileMenu.addAction(self.createTestRMLfromProdRMLAct)


        # self.editMenu = self.menuBar().addMenu("&Edit")
        # self.editMenu.addAction(self.cutAct)
        # self.editMenu.addAction(self.copyAct)
        # self.editMenu.addAction(self.pasteAct)

        # self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def createToolBars(self):
        self.toolBar = self.addToolBar("Toggle test mode")
        self.toolBar.addAction(self.toggleTestModeAct)        
        self.toolBar = self.addToolBar("Update configuratie")
        self.toolBar.addAction(self.updateConfigAct)
        self.toolBar = self.addToolBar("Bron data transformatie")
        self.toolBar.addAction(self.bronDataTransformatieAct)
        self.toolBar = self.addToolBar("Update RML mapping")
        self.toolBar.addAction(self.updateRmlMappingAct)
        self.toolBar = self.addToolBar("Draai conversie")
        self.toolBar.addAction(self.draaiConversieAct)
        self.toolBar = self.addToolBar("Valideer RDF data")
        self.toolBar.addAction(self.draaiValideerRDFAct)
        self.toolBar = self.addToolBar("Draai basis query's")
        self.toolBar.addAction(self.draaiBasisQuerysAct)
        self.toolBar = self.addToolBar("Draai analyse query's")
        self.toolBar.addAction(self.draaiAnalyseQuerysAct)
        
    def createStatusBar(self):
        self.statusBar().showMessage("Ready")

    def readSettings(self):
        settings = QtCore.QSettings("Trolltech", "Application Example")
        pos = settings.value("pos", QtCore.QPoint(200, 200))
        size = settings.value("size", QtCore.QSize(400, 400))
        self.resize(size)
        self.move(pos)

    def writeSettings(self):
        settings = QtCore.QSettings("Trolltech", "Application Example")
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())

    def maybeSave(self):
        if self.queryEdit.document().isModified():
            ret = QMessageBox.warning(self, "Application",
                    "The document has been modified.\nDo you want to save ",
                    "your changes?",
                    QMessageBox.Save | QMessageBox.Discard |
                    QMessageBox.Cancel)
            if ret == QMessageBox.Save:
                return self.save()
            elif ret == QMessageBox.Cancel:
                return False
        return True

    def loadFile(self, fileName):
        file = QtCore.QFile(fileName)
        if not file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            reason = file.errorString()
            QMessageBox.warning(self, "Application",
                    f"Cannot read file {fileName}:\n{reason}.")
            return

        inf = QtCore.QTextStream(file)
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.queryEdit.setPlainText(inf.readAll())
        QApplication.restoreOverrideCursor()

        self.setCurrentFile(fileName)
        self.statusBar().showMessage("File loaded", 2000)

    def saveFile(self, fileName):
        error = None
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        file = QtCore.QSaveFile(fileName)
        if file.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            outf = QtCore.QTextStream(file)
            outf << self.queryEdit.toPlainText()
            if not file.commit():
                reason = file.errorString()
                error = f"Cannot write file {fileName}:\n{reason}."
        else:
            reason = file.errorString()
            error = f"Cannot open file {fileName}:\n{reason}."
        QApplication.restoreOverrideCursor()

        if error:
            QMessageBox.warning(self, "Application", error)
            return False

        self.setCurrentFile(fileName)
        self.statusBar().showMessage("File saved", 2000)
        return True

    def setCurrentFile(self, fileName):
        self.curFile = fileName
        self.queryEdit.document().setModified(False)
        self.setWindowModified(False)

        if self.curFile:
            shownName = self.strippedName(self.curFile)
        else:
            shownName = 'untitled.txt'

        self.setWindowTitle(f"{shownName}[*] - Application")

    def strippedName(self, fullFileName):
        return QtCore.QFileInfo(fullFileName).fileName()

if __name__ == '__main__':
    import sys
    #model = QtCore.QAbstractItemModel()
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec())
