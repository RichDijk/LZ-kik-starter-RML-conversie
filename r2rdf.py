# Create sparql query UI
# aantal triples na query

# TODO: Wijzig paden voor testbestanden nadat de RML is aangemaakt

# Render ontologie als treeview ; 

import sys
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import * #QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtGui import QPainter, QPen

from rdflib import Graph, RDFS, SH, OWL, XSD
import yaml
from yaml.loader import SafeLoader

import petl as etl
#from petl import dateparser
import io, csv, os, sys, subprocess, datetime
import dateparser #https://dateparser.readthedocs.io/en/latest/introduction.html
import traceback
#import application_rc

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.testMode = False
        self.statusBar().showMessage(f"Test mode: False")

        self.curFile = ''
        self.queryEdit = QTextEdit()
        self.graph = None
        self.rdfdata = None
        self.graph_type = dict(model=None, constrained=None, data=None)
        self.configTxt = QTextBrowser()
        self.rmlmappingTxt = QTextBrowser()
        self.execButton = QPushButton('Run conversion.')
        self.execButton.setCheckable(True)
        self.execButton.clicked.connect(self.draaiConversie)

        self.resultPane = QTextBrowser()

        self.tabs	= QTabWidget()
        self.tab_table = QTableWidget()
        self.tab_table.setSortingEnabled(True)
        self.tab_basisquery = QTextBrowser()
        self.tab_validatie = QTextBrowser()

        self.config_panel_label = QLabel('Config')
        self.rml_panel_label = QLabel('RML mapping')

        page_layout = QGridLayout()

        self.tabs.addTab(self.tab_table,"RDF data")
        self.tabs.addTab(self.tab_validatie,"Validation result")
        self.tabs.addTab(self.tab_basisquery,"Basic query result")

        page_layout.addWidget(self.config_panel_label, 0, 0)
        page_layout.addWidget(self.rml_panel_label, 0, 1)
        page_layout.addWidget(self.configTxt, 1, 0)
        page_layout.addWidget(self.rmlmappingTxt, 1, 1)
        #page_layout.addWidget(self.queryEdit, 0, 1)
        page_layout.addWidget(self.execButton, 2, 0, 1, 2)
        page_layout.addWidget(self.tabs, 3, 0, 1, 2)
        
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

        #self.setCurrentFile('')
        self.setUnifiedTitleAndToolBarOnMac(True)

        # Lees config
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

    def toggleTestMode(self):
        # And update config file
        if self.testMode: 
            self.unsetTestMode()
        else:
            self.setTestMode()
        
    def setTestMode(self):
        # And update config file
        self.testMode = True
        self.updateConfig()
        self.statusBar().showMessage(f"Test mode: True, config updated")
        #currentfont = self.toggleTestModeAct.font()
        self.toggleTestModeAct.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.toggleTestModeAct.setFont
        
    def unsetTestMode(self):
        # And update config file
        # self.label.setFont(QtGui.QFont("Times",weight=QtGui.QFont.Bold))
        # self.label.setStyleSheet("font-weight: bold")
        self.testMode = False
        self.updateConfig()
        self.statusBar().showMessage(f"Test mode: False, config updated")
        self.toggleTestModeAct.setFont(QFont("Segoe UI", 9, QFont.Normal))
        

    def execute_conversie(self):
        # 
        #print(self.graph.all_nodes())
        if self.graph:
            sparql = self.queryEdit.toPlainText()
            result = self.graph.query(sparql)
            column_count = len(result.vars)
            row_count = len(list(result))

            # Fill table tab
            self.tab_table.setRowCount(row_count)
            self.tab_table.setColumnCount(column_count)
            self.tab_table.setHorizontalHeaderLabels(result.vars)

            for row, r in zip(result, range(row_count)):
                for var, c in zip(result.vars, range(column_count)):
                    item = QTableWidgetItem(row[var])
                    self.tab_table.setItem(r, c, item)
            
            for _ in range(column_count):
                self.tab_table.setColumnWidth(_,int(1500/column_count))

        else:
            QMessageBox.about(self, "Info",
                "Please first load a RDF graph.")
                
    def loadGraph(self, event):
        fileName, filtr = QFileDialog.getOpenFileName(self)
        if fileName:
            self.loadFile(fileName)

    def createProdRMLfromTestRML(self):
        """Vervang de testpaden door productiepaden."""
        # Lees rml_mapping test and produd folder
        # setTestMode en lees parameters
        # unsetTestMode en lees parameters
        # Lees path_update_data, used in RML mapping as logical source
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
        path_bron_data = remove_dotslash(self.lees_uit_config('path_update_data'))
        path_inrichting = remove_dotslash(self.lees_uit_config('path_inrichting'))

        path_rml_mapping = self.lees_uit_config('path_rml_mapping')
        rmlbestand = self.lees_uit_config('rmlbestand')
        #self.rmlMapping = Graph().parse(f"{path_rml_mapping}/{rmlbestand}")
        
        self.setTestMode()
        #print(self.testMode,self.config)
        path_update_data_test = remove_dotslash(self.lees_uit_config('path_bron_data'))
        path_inrichting_test = remove_dotslash(self.lees_uit_config('path_inrichting'))

        path_rml_mapping_test = self.lees_uit_config('path_rml_mapping')
        rmlbestand_test = self.lees_uit_config('rmlbestand')

        print(f"{path_rml_mapping_test}/{rmlbestand_test}")
        testrml = open(f"{path_rml_mapping}/{rmlbestand}", 'r')
        prodrml = open(f"{path_rml_mapping_test}/{rmlbestand_test}", 'w')
        for line in testrml:
            print(path_update_data_test, line)
            if path_update_data_test in line or path_inrichting_test in line:
                print('found!')
                if path_update_data_test in line:
                    prodrml.write(line.replace(path_update_data_test, path_update_data))
                if path_inrichting_test in line:
                    prodrml.write(line.replace(path_inrichting_test, path_inrichting))
            else:
                prodrml.write(line)
        testrml.close()
        prodrml.close()


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

    def openGraph(self):
        fileName, filtr = QFileDialog.getOpenFileName(self)
        if fileName:
            self.loadGraph(fileName)

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
        QMessageBox.about(self, "About R2RDF app",
                "This <b>R2RDF app</b> gives functions for working creating RML mappings based of test data."
                )

    def display_config(self):
        pass

    def updateConfig(self):
        try:
            if self.testMode:
                with open('config_test.yaml') as f:
                    self.config = yaml.load(f, Loader=SafeLoader)        
            else:
                with open('config.yaml') as f:
                    self.config = yaml.load(f, Loader=SafeLoader)        

            self.configTxt.setText(yaml.dump(self.config))
        except:
            QMessageBox.about(self, "Fout",
                "config.yaml en/of config_test.yaml staat(n) niet bij de exe")

    def updateRmlMapping(self):
        try:
            path_rml_mapping = self.lees_uit_config('path_rml_mapping')
            #if self.testMode:
            rmlbestand = self.lees_uit_config('rmlbestand')
            self.rmlMapping = Graph().parse(f"{path_rml_mapping}/{rmlbestand}")
            #else:
            #    self.rmlMapping = Graph().parse('mapping.rml.ttl')
            self.rmlmappingTxt.setText(self.rmlMapping.serialize())
        except:
            QMessageBox.about(self, "Fout",
                "RML mapping bestand staat niet bij de exe")

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
            shape_graph = Graph().parse('personeleSamenstellingShapes.ttl')

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
        except:
            QMessageBox.warning(self, 'Info', 'Geen RDF data beschikbaar.' )


    def draaiBasisQuerys(self):
        """Draai enkele tel en sommatie basis query's om 
        gevoel voor de data te krijgen.
        """
        if self.rdfdata:
            sparql = self.queryEdit.toPlainText()
            result = self.rdfdata.query("""SELECT ?txt (count(*) AS ?aantal) 
            WHERE {
                BIND ("Aantal triples: " AS ?txt)
                ?s ?p ?o
            }
            """)
            self.tab_basisquery.setText(f"{str(list(result)[0][0])}  {str(list(result)[0][1])}")
        else:
            QMessageBox.warning(self, 'Info', 'Geen RDF data beschikbaar.' )


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
                if value.count('-') == 2 or value.count('/') == 2:
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

        # def fill_pnr_cvnr_kolom(row):
        #     try:
        #         if 'PersoneelsNummer' in row.keys() and 'DienstverbandVolgnummer' in row.keys():
        #             row['pnrCvnr'] = f"{row['PersoneelsNummer']}-{row['DienstverbandVolgnummer']}"
        #     except:
        #         pass
        #     return row

        # def mergePnrDvnr(val, row):
        #     return f"{row[self.mergeColDict['col1']]}-{row[self.mergeColDict['col2']]}"

        def mergeColumnValues(val, row):
            result = 'Error'
            try:
                result = f"{row[self.mergeColDict['col1']]}-{row[self.mergeColDict['col2']]}"
            except:
                traceback.print_exc()
            return result
             

        # Leef relevante bestandsnamen uit config file
        bron_bestanden = self.lees_uit_config('bronbestanden')
        new_columns = self.lees_uit_config('new-cols') 
        self.path_bron_data = self.lees_uit_config('path_bron_data')

        # lees path bestanden
        # if self.testMode:
        #     self.path_bron_data = self.lees_uit_config('path_bron_data_test')
        # else:
        #     self.path_bron_data = self.lees_uit_config('path_bron_data')
            
        for bronfilename in bron_bestanden:
            #if self.testMode:
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
                    new_column_def = self.lees_dict_uit_config(new_column)
                    self.mergeColDict = dict(
                        col1=new_column_def['col1'],
                        col2=new_column_def['col2'])
                    print('files: ', new_column_def['files'])
                    if bronfilename in new_column_def['files']:
                        print('if: ', bronfilename , new_column)
                        table = etl.addcolumn(table, new_column, [])
                        table = etl.convert(table, new_column, mergeColumnValues, pass_row=True)
                        print('na\n', table)
                        header = etl.header(table)
                        print('header', header)

            table = etl.rowmap(table, transform_decimal, header=header) # seraches for , and replace with .
            if self.testMode:
                etl.tocsv(table, f'data_bron_update_test/{bronfilename}', delimiter=',' )
            else:
                etl.tocsv(table, f'data_bron_update/{bronfilename}', delimiter=',' )

    def draaiConversie(self):
        rmlmapperjar = self.lees_uit_config('rmlmapperjar')
        rmlbestand = self.lees_uit_config('rmlbestand')
        path_rml_mapping = self.lees_uit_config('path_rml_mapping')
        rdfdata = self.lees_uit_config('rdfdata')
        print('voor: ', datetime.datetime.now())
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

        print('na: ', datetime.datetime.now())
        # Update RDF data view
        try:
            self.rdfdata = Graph().parse(rdfdata)
            #sparql = self.queryEdit.toPlainText()
            result = list(self.rdfdata.triples((None, None, None))) #.query(sparql)
            column_count = 3 #len(result.vars)
            row_count = len(result)

            # Fill table tab
            self.tab_table.setRowCount(row_count)
            self.tab_table.setColumnCount(column_count)
            self.tab_table.setHorizontalHeaderLabels(['s', 'p', 'o'])

            for row, r in zip(result, range(row_count)):
            #r=0
            #print(len(result))
    #            for row in result:
                #for row in result:
                    #for var, c in zip(result.vars, range(column_count)):
                for c in range(column_count):
                    item = QTableWidgetItem(row[c])
                    self.tab_table.setItem(r, c, item)
                
            for _ in range(column_count):
                self.tab_table.setColumnWidth(_, 450)
        except:
            traceback.print_exc()
            QMessageBox.warning(self, 'Fout', 'Geen RDF data kunnen maken.' )

        

    def documentWasModified(self):
        self.setWindowModified(self.queryEdit.document().isModified())

    def createActions(self):
        self.toggleTestModeAct = QtGui.QAction("Toggle testmode", self,
                statusTip = "Toggle testmode", triggered=self.toggleTestMode)

        self.updateConfigAct = QtGui.QAction("Update configuratie", self,
                statusTip = "Read new config.yaml", triggered=self.updateConfig)

        self.updateRmlMappingAct = QtGui.QAction("Update RML mapping", self,
                statusTip = "Read mapping for RML mapping", triggered=self.updateRmlMapping)

        self.draaiConversieAct = QtGui.QAction("Run conversion", self,
                statusTip = "Run conversion using RML and create RDF data", triggered=self.draaiConversie)

        self.createProdRMLfromTestRMLAct = QtGui.QAction("Create RML from test folder paths.", self,
                statusTip = "Create RML from test mapping using testfolder paths.", triggered=self.createProdRMLfromTestRML)

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

        self.openGraphAct = QtGui.QAction("Open graph file", self,
                statusTip = "Open RDF graph", 
                triggered=self.openGraph
                )

        self.graphAnalysisAct = QtGui.QAction("Graph analysis", self,
                statusTip="Graaf analyse",
                triggered = self.graphAnalysis
                )

        self.bronDataTransformatieAct = QtGui.QAction("Transform source data", self,
                statusTip="Lees orginele data en pas nodige transformaties toe zoals datum formaat.",
                triggered = self.bronDataTransformatie
                )

        self.draaiValideerRDFAct = QtGui.QAction("Validate RDF data", self,
                statusTip = "Validate created RDF data.",
                triggered = self.draaiValideerRDF
                )

        self.draaiBasisQuerysAct = QtGui.QAction("Run basic query's", self,
                statusTip = "Draai sparql query's voor basis data.",
                triggered = self.draaiBasisQuerys
                )

        self.cutAct.setEnabled(False)
        self.copyAct.setEnabled(False)
        self.queryEdit.copyAvailable.connect(self.cutAct.setEnabled)
        self.queryEdit.copyAvailable.connect(self.copyAct.setEnabled)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.createProdRMLfromTestRMLAct)

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)

    def createToolBars(self):
        self.toolBar = self.addToolBar("Toggle test mode")
        self.toolBar.addAction(self.toggleTestModeAct)        
        self.toolBar = self.addToolBar("Update configuration")
        self.toolBar.addAction(self.updateConfigAct)
        self.toolBar = self.addToolBar("Source data transformation")
        self.toolBar.addAction(self.bronDataTransformatieAct)
        self.toolBar = self.addToolBar("Update RML mapping")
        self.toolBar.addAction(self.updateRmlMappingAct)
        self.toolBar = self.addToolBar("Run conversion")
        self.toolBar.addAction(self.draaiConversieAct)
        self.toolBar = self.addToolBar("Validate RDF data")
        self.toolBar.addAction(self.draaiValideerRDFAct)
        self.toolBar = self.addToolBar("Run basic query's")
        self.toolBar.addAction(self.draaiBasisQuerysAct)
        
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

    def loadGraph(self, fileName):
        self.graph = Graph().parse(fileName)
        self.queryEdit.setText(
"""select ?s ?p ?o 
where { 
    ?s ?p ?o 
    }
""")
        self.statusBar().showMessage(f"{fileName} loaded")

    def graphAnalysis(self):
        """Based on this analysis standard query's are offered and ran for profiling.
        This is rather difficult to assess."""
        # If sh property exists than it is a shapes graph
        # If a owl:Class exists than it is a model graph
        # If a <non-owl/rdfs prefix>:<Class> exists it is a data graph
        if self.graph:
            shape_count = len(list(self.graph.triples((None, SH.NodeShape, None))))
            #predicate_objects = self.graph.triples.predicate_objects(subject=None)
            # check objects of type Literal
            #print(shape_count)
            if self.graph.triples((None, None, OWL.Class)):
                # for t in self.graph.triples((None, None, OWL.Class)):
                #     print(t)
                self.graph_type['model'] = True
            if shape_count:
                self.graph_type['constrained'] = True
            if self.graph_type['constrained'] == False and self.graph_type['constrained'] == False: 
                self.graph_type['data'] = True
        else:
            self.statusBar().showMessage("No graph loaded")

        shape_count = len(list(self.graph.triples((None, SH.NodeShape, None))))
        class_count = len(list(self.graph.triples((None, None, OWL.Class))))

        self.configTxt.setText(f"""
Config:
{self.config}
        """
        )




    # def preprocess(self):
    #     """Pre process csv files
    #     Configureer middels yaml file
    #     - alle csv's in data_bron
    #     - bestanden waar een kolom in moet worden bijgemaakt via kolomnaam en twee veldnamen met dash ertussen
    #     - 
    #     """
    #     from rdflib import Graph
    #     import petl as etl
    #     #from petl import dateparser
    #     import io, csv, os, sys, subprocess, datetime
    #     import dateparser #https://dateparser.readthedocs.io/en/latest/introduction.html

    #     # Varianten
    #     # 1-15-2021 12:00:00 AM
    #     # 1-15-2021 12:00:00
    #     # 1-4-2021 00:00
    #     # 1-15-2021


    #     def transform_date_time_dash(row):
    #         """Kijk naar datum velden in het formaat d-m-J hh:mmm:(ss) (AM) en zet dez om in J-m-d"""
    #         row_updated = []
    #         for value in row:
    #             if value.count('-') == 2:
    #                 date = dateparser.parse(value).strftime("%Y-%m-%d") # Parse and write
    #                 if value != date:
    #                     row_updated.append(date)
    #                 else:
    #                     row_updated.append(value)
    #             else:
    #                 row_updated.append(value)
    #         return row_updated 


    #     def transform_decimal(row):
    #         """Kijk naar , in string en zet deze om naar ."""
    #         # TODO: kan dit niet met pandas import?
    #         row_updated = []
    #         for value in row:
    #             if ',' in value:
    #                 row_updated.append(float(value.replace(",", ".")))
    #             else:
    #                 row_updated.append(value)
    #         return row_updated

    #     def transform_time(row):
    #         """Kijk naar : en lengte 5 in string en zet deze om naar -"""
    #         try:
    #             row_updated = []
    #             for value in row:
    #                 value_old = value
    #                 if ':' in value and len(value)==5:
    #                     #print('if: ',value)
    #                     row_updated.append(value.replace(":", "-"))
    #                 else:
    #                     row_updated.append(value)
    #         except:
    #             pass
    #             #print('error: ', value_old, '->', value)
    #         return row_updated

    #     def mergePnrDvnr(val, row):
    #         return f"{row['PersoneelsNummer']}-{row['DienstverbandVolgnummer']}"

    #     for filename in [
    #         'AFAS', 
    #         'Aysist',
    #         'Beaufort',
    #         'ONSNedap',
    #         'Verzuim',
    #         ]:
    #         df = etl.fromcsv(f'data/{filename}.csv', delimiter=';' )
    #         #table = etl.convertnumbers(df)
    #         header = df[0]
    #         table = etl.rowmap(df, transform_date_time_dash, header=header) #seraches for 2x'-
    #         table = etl.rowmap(table, transform_time, header=header) # searches for :

    #         if filename in ['Aysist', 'Beaufort','Verzuim']:
    #             table = etl.addcolumn(table, 'pnr-dvvnr', [])
    #             table = etl.convert(table, 'pnr-dvvnr', mergePnrDvnr, pass_row=True)
    #             header = etl.header(table)

    #         table = etl.rowmap(table, transform_decimal, header=header) # seraches for , and replace with .

    #         etl.tocsv(table, f'data_update/{filename}.csv', delimiter=',' )



if __name__ == '__main__':
    import sys
    #model = QtCore.QAbstractItemModel()
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec())
