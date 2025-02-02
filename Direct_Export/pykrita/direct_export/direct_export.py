from krita import *
from PyQt5.Qt import *
import re

DOCKER_TITLE = 'Direct Export'
DE_VERSION   = '1.01'

class DEEDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(DOCKER_TITLE)
        self.msg       = None
        self.timer     = None

        self.txtNotExported   = "  -- Image not exported yet --"
        self.txtInvalidFormat = "  -- Not a Krita file --" 

        # Settings default
        self.deeSettings = {
            'DirectExport_Version': DE_VERSION,
            'deeExportPath': None,
            'exportSettings': {}
        }
            
        self.mainWidget = QWidget()
        self.layout = QVBoxLayout()
        
        # Controls layout
        self.controlsLayout = QHBoxLayout()
        
        self.labelExport = QLabel()
        self.labelExport.setText("File Path:")
        self.pathDisplay = QLineEdit("")

        self.selectExportPath = QPushButton()
        icon = self.style().standardIcon(QStyle.SP_DirIcon)
        self.selectExportPath.setIcon(icon)
        
        self.selectExport = QPushButton()
        icon2 = self.style().standardIcon(QStyle.SP_ArrowForward)
        self.selectExport.setIcon(icon2)

        self.statusLabelWrongVersion = QLabel("Please update the plugin, old version used to export this image")
        self.statusLabelWrongVersion.setStyleSheet("color: red;")
        self.statusLabelWrongVersion.setAlignment(Qt.AlignLeft)
        
        self.selectExportPath.clicked.connect(self.updateExportingPath)
        self.selectExport.clicked.connect(self.export)
        
        self.controlsLayout.addWidget(self.labelExport)
        self.controlsLayout.addWidget(self.pathDisplay)
        self.controlsLayout.addWidget(self.selectExportPath)
        self.controlsLayout.addWidget(self.selectExport)
        
        self.layout.addLayout(self.controlsLayout)
        self.layout.addWidget(self.statusLabelWrongVersion)
        self.mainWidget.setLayout(self.layout)
        
        self.setWidget(self.mainWidget)

        self.mainWidget.setFixedHeight(63)
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.mainWidget.setSizePolicy(size_policy)
        self.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.setMinimumHeight(63)
        self.setMaximumHeight(63)
        self.statusLabelWrongVersion.setVisible(False)


    # Update settings when canvas changes
    def canvasChanged(self, canvas):
        self.loadSettingsFromFile()

    # Export button.
    def export(self):
        # Not exported yet so in this case we force updateExportingPath
        if self.deeSettings['deeExportPath'] == self.txtNotExported:
            self.updateExportingPath()

        # Invalid format
        elif self.deeSettings['deeExportPath'] == self.txtInvalidFormat:
            print("Not a valid exporting format, needs to be a .kra")

        else:
            success = self.directExport()
            if success:
                self.showExportMessage()


    def loadSettingsFromFile(self):
        app = Krita.instance()
        activeDoc = app.activeDocument()

        if activeDoc:
            file_extension = activeDoc.fileName().split('.')[-1] if '.' in activeDoc.fileName() else 'NoSavedFile'
            doc_info = activeDoc.documentInfo()

            match = re.search(r'<abstract[^>]*>\s*<!\[CDATA\[(.*?)\]\]>\s*</abstract>', doc_info, re.DOTALL)

            if file_extension == "kra" or file_extension == "NoSavedFile":
                if match:
                    xml_content = match.group(1)
                    print (xml_content)
                    if not xml_content.startswith('<DirectExport>'):
                        print("File does not contain Direct Export configuration")
                        self.setPathDisplay(None)
                        return False
                        
                    from xml.etree import ElementTree as ET
                    root = ET.fromstring(xml_content)
                    
                    # Load Settings
                    loaded_settings = {
                        'DirectExport_Version': root.find('DirectExport_Version').text,
                        'deeExportPath': root.find('deeExportPath').text,
                        'exportSettings': {}
                    }

                    # Check Version 
                    if loaded_settings['DirectExport_Version'] != DE_VERSION:
                        self.mainWidget.setFixedHeight(63)
                        self.setMinimumHeight(70)
                        self.setMaximumHeight(70)
                        self.statusLabelWrongVersion.setVisible(True)
                        print(f"Warning: Config version mismatch. File: {loaded_settings['DirectExport_Version']}, Current: {DE_VERSION}")
                        print("Please download the latest DirectExport version to ensure proper file export\n")
                    else:
                        self.mainWidget.setFixedHeight(60)
                        self.setMinimumHeight(60)
                        self.setMaximumHeight(60)
                        self.statusLabelWrongVersion.setVisible(False)


                    # Parse export settings
                    export_settings = root.find('exportSettings')
                    if export_settings is not None:
                        for setting in export_settings:
                            if setting.tag == 'transparencyFillcolor':
                                value = setting.text
                                unescaped_value = value.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
                                loaded_settings['exportSettings'][setting.tag] = unescaped_value
                            else:
                                loaded_settings['exportSettings'][setting.tag] = setting.text

                    # Update settings on main object 
                    self.deeSettings['exportSettings'] = {}
                    self.deeSettings = loaded_settings

                    # Update text displayed at path
                    self.setPathDisplay(self.deeSettings['deeExportPath'])

                    print("\nLoaded settings from file:")
                    print(" Settings Version:" + self.deeSettings['DirectExport_Version'])
                    print(" "+ self.deeSettings['deeExportPath'] + "\n")
                    return True

            else:
                self.setPathDisplay("Wrong")
                print("\nNot a .kra file")             
        
        return False


    def showExportMessage(self):
        self.exportedText = "  IMAGE EXPORTED   "
        self.msg = QMessageBox()
        self.msg.setWindowTitle("")
        self.msg.setText(self.exportedText + "\n\n" + self.deeSettings['deeExportPath'])
        self.msg.setStandardButtons(QMessageBox.NoButton)
        self.msg.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Export window Text Style
        self.msg.setStyleSheet("""
            QMessageBox {
                background-color: #474747;
                color: red;
                min-height: 24px;
                max-height: 24px;
            }
            QLabel {
                color: orange;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
                qproperty-alignment: AlignCenter;
                margin-top: 8px;
            }
        """)

        window = Krita.instance().activeWindow().qwindow()
        if window:
            self.msg.move(
                window.frameGeometry().center() - self.msg.rect().center()
            )
        
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.closeMessage)
        
        self.msg.show()
        self.timer.start(1000) #time showing msg

        # Update the status bar
        app = Krita.instance()
        window = app.activeWindow()
        statusBar = window.qwindow().statusBar()
        statusBar.showMessage(self.exportedText)
 
    
    def closeMessage(self):
        if self.msg:
            self.msg.close()
            self.msg = None
            self.timer.stop()

    def directExport(self):
        app = Krita.instance()
        activeDoc = app.activeDocument()

        activeDoc.setBatchmode(True) # Disabling quiet exporting

        info_object = InfoObject()

        # Adding export setting to info_object
        format_settings = self.deeSettings['exportSettings']
        for key, value in format_settings.items():
            info_object.setProperty(key, value)
        imageExportPath = self. deeSettings['deeExportPath']
        success = activeDoc.exportImage(imageExportPath, info_object)
        
        activeDoc.setBatchmode(False) # Disabling quiet exporting
        if success:
            print("\nExport successful")
            print(" Path: " + imageExportPath)
            print ("\n" + str(format_settings))
            return True
        else:
            print("Export failed")
            return False


    def export_advanced(self, document):
        app = Krita.instance()
        
        # Check if the document is not None
        if document is None:
            document = app.activeDocument()
            if document is None:
                raise Exception("No active document")

        # Creatng file dialog
        fileDialog = QFileDialog()
        fileDialog.setWindowTitle("Export Image As")
        fileDialog.setFileMode(QFileDialog.AnyFile)
        fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        
        nameFilters = [
            "All Files (*.*)", 
            "PNG image (*.png)",
            "TGA image (*.tga *.icb *.tpic *.vda *.vst)",
            "Windows BMP image (*.bmp *.dib)",
            "JPEG image (*.jpg *.jpeg *.jpe)",
            "OpenRaster Image (*.ora)",
            "OpenEXR (Extended) (*.exr)",
            "AVIF Image (*.avif)",
            "CSV Document (*.csv)",
            "EXR image (*.exr)",
            "GIF image (*.gif)",
            "Gimp Brush (*.gbr *.vbr)",
            "Gimp Image Hose Brush (*.gih)",
            "HEIC/HEIF Image (*.heic *.heif)",
            "JPEG-XL Image (*.jxl)",
            "Krita Archival Image Format (*.krz)",
            "Krita Brush Preset (*.kpp)",
            "PBM image (*.pbm)",
            "PGM image (*.pgm)",
            "PPM image (*.ppm)",
            "Photoshop image (*.psd)",
            "Qt Markup Language file (*.qml *.qmltypes *.qmlproject)",
            "R16 Heightmap (*.r16)",
            "R32 Heightmap (*.r32)",
            "R8 Heightmap (*.r8)",
            "RAW Spriter SCML (*.scml)",
            "TIFF image (*.tif *.tiff)",
            "WebP image (*.webp)",
            "Windows icon (*.ico)",
            "XBM image (*.xbm)"
        ]
        
        fileDialog.setNameFilters(nameFilters)

        # Set default directory and file
        if self.deeSettings['deeExportPath'] and self.deeSettings['deeExportPath'] not in [self.txtNotExported, self.txtInvalidFormat]:
            lastPath = self.deeSettings['deeExportPath']
            lastDir = '/'.join(lastPath.split('/')[:-1])
            
            fileDialog.setDirectory(lastDir)
            fileDialog.selectFile(lastPath)
            
            last_extension = lastPath.split('.')[-1].lower()
            for filter_str in nameFilters:
                if f"*.{last_extension}" in filter_str.lower():
                    fileDialog.selectNameFilter(filter_str)
                    break
        else:
            if document.fileName():
                defaultPath = document.fileName()
                fileDialog.selectFile(defaultPath)
            else:
                defaultPath = document.name()
                fileDialog.selectFile(defaultPath)

        if fileDialog.exec_() == QFileDialog.Accepted:
            output_path = fileDialog.selectedFiles()[0]
            selected_filter = fileDialog.selectedNameFilter()
            
            if '.' not in output_path.split('/')[-1]:
                import re
                match = re.search(r'\*\.(\w+)[\s\)]', selected_filter)
                if match:
                    extension = match.group(1)
                    output_path = f"{output_path}.{extension}"
            
            info_object = InfoObject()
            format_settings = self.deeSettings['exportSettings']
            for key, value in format_settings.items():
                info_object.setProperty(key, value)

            success = document.exportImage(output_path, info_object)

            if success:
                self.deeSettings['deeExportPath'] = output_path
                self.setPathDisplay(output_path)
                expProperties = info_object.properties()
                self.deeSettings['exportSettings'] = expProperties
                print("\nExported file: ")
                print(self.deeSettings['deeExportPath'])
                print(self.deeSettings['exportSettings'])
                return True

        return False

    def updateExportingPath(self):
        app = Krita.instance()
        activeDoc = app.activeDocument()

        success = self.export_advanced(activeDoc)

        if success:
            self.deeSettings['DirectExport_Version'] = DE_VERSION  #Added correct exported version to the file
            self.statusLabelWrongVersion.setVisible(False)         #Hides wrong version label telling you about the old plugin
            xml_content = f"""<DirectExport>
        <DirectExport_Version>{self.deeSettings['DirectExport_Version']}</DirectExport_Version>
        <deeExportPath>{self.deeSettings['deeExportPath']}</deeExportPath>
        <exportSettings>"""
            
            for key, value in self.deeSettings['exportSettings'].items():
                if key == 'transparencyFillcolor':
                    escaped_value = value.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
                    xml_content += f"\n        <{key}>{escaped_value}</{key}>"
                else:
                    xml_content += f"\n        <{key}>{value}</{key}>"
                
            xml_content += "\n    </exportSettings>\n</DirectExport>"
            
            # Add settings into the description section of the .kra file
            doc_info = activeDoc.documentInfo()
            new_info = re.sub(
                r'<abstract><!\[CDATA\[([^]]*)\]\]></abstract>',
                f'<abstract><![CDATA[{xml_content}]]></abstract>',
                doc_info
            )
            activeDoc.setDocumentInfo(new_info)

            if activeDoc.fileName():
                activeDoc.save()
                print("Document saved")
                print(xml_content)
            else:
                print("Document needs to be saved")


    def setPathDisplay(self,path=None):
        if path == "Wrong": #This is a wrong format document
            self.pathDisplay.setReadOnly(True)  #Not editable text
            self.pathDisplay.setStyleSheet(
            """
                QLineEdit {
                    color: #954a4a;                
                }
            """)
            self.pathDisplay.setText(self.txtInvalidFormat)
            self.deeSettings['deeExportPath'] = self.txtInvalidFormat #update path variable

            #Show UI buttons
            self.selectExportPath.setVisible(False)
            self.selectExport.setVisible(False)

        elif path is None:   #Still not exported
            self.pathDisplay.setReadOnly(True)  #Not editable text
            self.pathDisplay.setStyleSheet(
            """
                QLineEdit {
                    color: gray;
                }
            """)
            self.pathDisplay.setText(self.txtNotExported)
            self.deeSettings['deeExportPath'] = self.txtNotExported #update path variable
            
            #Show UI buttons
            self.selectExportPath.setVisible(True)
            self.selectExport.setVisible(False)

        else:
            self.pathDisplay.setStyleSheet(
            """
                QLineEdit {
                    color: white;                 
                }
            """)
            self.pathDisplay.setText(path)
            
            #Show buttons again
            self.selectExportPath.setVisible(True)
            self.selectExport.setVisible(True)


class DEEDockerFactory(DockWidgetFactoryBase):
    def __init__(self):
        super().__init__("direct_export", DockWidgetFactory.DockRight)
    
    def createDockWidget(self):
        return DEEDocker()


class DEExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass
    
    def createActions(self, window):
        exportAction = window.createAction(
            "direct_export",
            "Direct Export"
        )
        
        exportAction.triggered.connect(self.triggerExport)

    def triggerExport(self):
        mainWindow = Krita.instance().activeWindow()
        for docker in mainWindow.dockers():
            if docker.objectName() == "direct_export":
                docker.export()
                break


def registerDocker():
    docker_factory = DEEDockerFactory()
    Krita.instance().addDockWidgetFactory(docker_factory)

Krita.instance().addExtension(DEExtension(Krita.instance()))
registerDocker()