__author__ = "Milo van der Linden"
__date__ = "$Jun 11, 2011 3:46:27 PM$"

"""
 Naam:         BAGFileReader.py
 Omschrijving: Inlezen van BAG-gerelateerde files of directories

 Auteur:       Milo van der Linden Just van den Broecke

 Versie:       1.0
               - basis versie
 Datum:        22 december 2011


 OpenGeoGroep.nl
"""
import os
import sys
try:
    import zipfile
except:
    logging.critical("Python zipfile is vereist")
    sys.exit()

from bagconfig import BAGConfig
from processor import Processor
from xml.dom.minidom import parse
import csv


#from lxml import etree

#Onderstaand try/catch blok is vereist voor python2/python3 portabiliteit
try:
    from io import StringIO #Python3
    from io import BytesIO #Python3
except:
    try:
        from cStringIO import StringIO #probeer cStringIO, faster
    except:
        from StringIO import StringIO #StringIO, standaard

class BAGFileReader:
    def __init__(self, file):
        self.file = file
        self.init = True
        self.processor = Processor()
        self.fileCount = 0
        self.recordCount = 0

    def process(self):
        BAGConfig.logger.info("process file=" + self.file)
        if not os.path.exists(self.file):
            logging.critical("ik kan BAG-bestand of -directory: '" + self.file + "' ech niet vinden")
            return

        # TODO: Verwerk een directory
        if os.path.isdir(self.file) == True:
            self.readDir()
        elif zipfile.is_zipfile(self.file):
            self.zip = zipfile.ZipFile(self.file, "r")
            self.readzipfile()
        else:
            zipfilename = os.path.basename(self.file).split('.')
            ext = zipfilename[1]
            if ext == 'xml':
                xml = self.parseXML(self.file)
                self.processXML(zipfilename[0],xml)
            if ext == 'csv':
                fileobject = open(self.file, "rb")
                objecten = self.processCSV(zipfilename[0], fileobject)
                # TODO: verwerken!

    def readDir(self):
        for each in os.listdir(self.file):
            _file = os.path.join(self.file, each)
            if zipfile.is_zipfile(_file):
                self.zip = zipfile.ZipFile(_file, "r")
                self.readzipfile()
            else:
                if os.path.isdir(_file) != True:
                    zipfilename = each.split('.')
                    if len(zipfilename) == 2:
                        ext = zipfilename[1]
                        if ext == 'xml':
                            BAGConfig.logger.info("==> XML File: " + each)
                            xml = self.parseXML(_file)
                            self.processXML(zipfilename[0],xml)
                        if ext == 'csv':
                            BAGConfig.logger.info("==> CSV File: " + each)
                            fileobject = open(_file, "rb")
                            objecten = self.processCSV(zipfilename[0],fileobject)
                            return objecten

    def readzipfile(self):
        tzip = self.zip
        BAGConfig.logger.info("readzipfile content=" + str(tzip.namelist()))
        for naam in tzip.namelist():
            ext = naam.split('.')
            BAGConfig.logger.info("readzipfile: " + naam)
            if len(ext) == 2:
                if ext[1] == 'xml':
                    try:
                        xml = self.parseXML(BytesIO(tzip.read(naam))) #Python3
                    except:
                        xml = self.parseXML(StringIO(tzip.read(naam)))
                    #xml = etree.parse (StringIO(tzip.read(naam)))
                    self.processXML(naam, xml)
                elif ext[1] == 'zip':
                    try:
                        self.readzipstring(BytesIO(tzip.read(naam))) #Python3
                    except:
                        self.readzipstring(StringIO(tzip.read(naam)))

                elif ext[1] == 'csv':
                    BAGConfig.logger.info(naam)
                    try:
                        fileobject = BytesIO(tzip.read(naam)) #Python3
                    except:
                        fileobject = StringIO(tzip.read(naam))

                    objecten = self.processCSV(naam, fileobject)
                    return objecten
                else:
                    BAGConfig.logger.warn("Negeer: " + naam)

    def readzipstring(self,naam):
        # logging.info("readzipstring naam=" + naam)
        tzip = zipfile.ZipFile(naam, "r")
        # logging.info("readzipstring naam=" + tzip.getinfo().filename)

        for nested in tzip.namelist():
            BAGConfig.logger.info("readzipstring: " + nested)
            ext = nested.split('.')
            if len(ext) == 2:
                if ext[1] == 'xml':
                    try:
                        xml = self.parseXML(BytesIO(tzip.read(nested)))
                    except:
                        xml = self.parseXML(StringIO(tzip.read(nested)))

                    #xml = etree.parse(StringIO(tzip.read(nested)))
                    self.processXML(nested, xml)
                elif ext[1] == 'csv':
                    #Log.log.info(nested)
                    try:
                        fileobject = BytesIO(tzip.read(nested))
                    except:
                        fileobject = StringIO(tzip.read(nested))

                    objecten = self.processCSV(nested, fileobject)
                    return objecten

                elif ext[1] == 'zip':
                    try:
                        self.readzipstring(BytesIO(tzip.read(nested)))
                    except:
                        self.readzipstring(StringIO(tzip.read(nested)))
                else:
                    BAGConfig.logger.info("Negeer: " + nested)

    def parseXML(self,naam):
        #Log.log.startTimer("parseXML")
        xml = parse(naam)
        #Log.log.endTimer("parseXML")
        return xml

    def processXML(self,naam, xml):
        BAGConfig.logger.info("processXML: " + naam)
        xmldoc = xml.documentElement
        #xmldoc = xml.getroot()
        #de orm bepaalt of het een extract of een mutatie is
        self.processor.processDOM(xmldoc)
        #Log.log.info(document)
        xml.unlink()

    def processCSV(self,naam, fileobject):
        BAGConfig.logger.info(naam)
        # TODO: zorg voor de verwerking van het geparste csv bestand
        # Maak er gemeente_woonplaats objecten van overeenkomstig de nieuwe
        # tabel woonplaats_gemeente

        # TODO: Dirty version hack. Er blijkt in python2 ook een TextIOWrapper te zitten, maar deze veroorzaakt
        #       encoding issues die ik zo snel niet kreeg opgelost. Zo dan maar:
        if sys.version_info[0] == 3:
            from io import TextIOWrapper
            myReader = csv.reader(TextIOWrapper(fileobject,'iso-8859-15'), delimiter=';', quoting=csv.QUOTE_NONE)
        elif sys.version_info[0] == 2:
            myReader = csv.reader(fileobject, delimiter=';', quoting=csv.QUOTE_NONE)

        objecten = self.processor.processCSV(myReader)
        return objecten
