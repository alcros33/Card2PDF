import json, os, sys
from pathlib import Path

from PyQt5.QtCore import Qt, QDir, QRect
from PyQt5.QtWidgets import QApplication, QFileDialog, QDialog,QMainWindow, QTableWidget,QTableWidgetItem, QHeaderView, QPushButton, QLabel
from PyQt5.QtGui import QIcon, QPixmap

from Ui_MainWindow import Ui_MainWindow
from CardPDFWriter import CardPDFWriter
from ygo_parser import YGOProParser

BASE_DIR = Path(__file__).resolve().parent

class DialogMesage(QDialog):
    def __init__(self,parent, title, msg):
        super().__init__(parent)
        self.resize(485, 140)
        self.setWindowTitle(title)
        
        self.Mesage = QLabel(self)
        self.Mesage.setGeometry(QRect(50, 20, 370, 30))
        self.Mesage.setAlignment(Qt.AlignCenter)
        self.Mesage.setObjectName("Mesage")
        self.Mesage.setText(msg)
        
        self.okButton = QPushButton(self)
        self.okButton.setGeometry(QRect(190, 80, 100, 40))
        self.okButton.setObjectName("okButton")
        self.okButton.clicked.connect(self.close)
        self.okButton.setText("Ok")

class ImgItemWidget(QLabel):
    def __init__(self, img:QPixmap, parent=None):
        super().__init__(parent)
        self.img = img.scaled(50, 70)
        self.setPixmap(self.img)

def check_formats_ok(formats):
    try:
        if isinstance(formats, (tuple, list)):
            assert len(formats) == 2
            for x in formats:
                assert isinstance(x, (int, float))
            return True
        elif isinstance(formats, dict):
            for val in formats.values():
                assert check_formats_ok(val)
        else:
            return False
    except AssertionError:
        return False
    return True

class Card2PDFGUI(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        # Config File
        try:
            with (BASE_DIR/"Settings.json").open('r') as f:
                _config = json.load(f)
        except:
            _config = {}
        # Defaults
        self.settings = {}
        self.settings["Paper Formats"] = {"Ledger 432x279 mm": [432, 279]}
        self.settings["Card Formats"] = dict(Pokemon=[63, 88], Yugioh=[59, 85.5])
        self.settings["Separation"] = [0.8, 0.8]
        self.settings["YGOPro Deck Folder"] = str(BASE_DIR.parent)
        # Read and check config
        if "Paper Formats" in _config and check_formats_ok(_config["Paper Formats"]):
            self.settings["Paper Formats"] = _config["Paper Formats"]
        if "Card Formats" in _config and check_formats_ok(_config["Card Formats"]):
            self.settings["Card Formats"] = _config["Card Formats"]
        if "Separation" in _config and check_formats_ok(_config["Separation"]):
            self.settings["Separation"] = _config["Separation"]
        if "YGOPro Deck Folder" in _config and Path(str(_config["YGOPro Deck Folder"])).resolve().exists():
            self.settings["YGOPro Deck Folder"] = _config["YGOPro Deck Folder"]
        
        self.imageNames = []
        self.images = []
        self.setWindowTitle("Card2PDF") 
        
        for key in self.settings['Card Formats']:
            self.cardComboBox.addItem(key)
        
        for key in self.settings['Paper Formats']:
            self.paperComboBox.addItem(key)
            
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.tableWidget.verticalHeader().setDefaultSectionSize(70)
        
        self.addCardsButton.clicked.connect(self.selectImages)
        self.exportButton.clicked.connect(self.makePDF)
        self.clearButton.clicked.connect(self.clearList)
        self.removeCardsButton.clicked.connect(self.removeSelected)
        self.ygopro = YGOProParser(self)
    
    def selectImages(self):
        new_images, ok = QFileDialog.getOpenFileNames(self, "Choose one or more Card Images",
            str(BASE_DIR),"Images (*.png *.xpm *.jpg);;All Files (*)")
        if not ok or not new_images:
            return
        new_images = list(filter(lambda img: img not in self.imageNames, new_images))
        self.addImgsToTable(new_images)

    def addImgsToTable(self, new_images):
        old_len = len(self.imageNames)
        for img in new_images:
            pixmap = QPixmap(img)
            if pixmap.isNull():
                continue
            self.imageNames.append(img)
            self.images.append(pixmap)
        new_len = len(self.imageNames)

        for it in range(old_len, new_len):
            self.tableWidget.insertRow(it)
            base_file_name = Path(self.imageNames[it]).name
            self.tableWidget.setItem(it, 0, QTableWidgetItem(base_file_name))
            self.tableWidget.item(it, 0).setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
            self.tableWidget.setItem(it, 1, QTableWidgetItem('1'))
            self.tableWidget.setCellWidget(it, 2, ImgItemWidget(self.images[it], self.tableWidget))
        if (new_len-old_len) != len(new_images):
            DialogMesage(self, "ERROR", "Some images could not be loaded").show()
    
    def clearList(self):
        self.images.clear()
        self.imageNames.clear()
        self.tableWidget.setRowCount(0)
    
    def makePDF(self):
        if not self.images:
            DialogMesage(self, "ERROR", "The Card list is empty").show()
            return
        file_name, ok = QFileDialog.getSaveFileName(self, "Save PDF Document", str(BASE_DIR/"out.pdf"),
                        "PDF (*.pdf);;All Files (*)")
        if not ok:
            return
        paper_format = self.settings['Paper Formats'][self.paperComboBox.currentText()]
        card_format = self.settings['Card Formats'][self.cardComboBox.currentText()]
        copies = self.parseNumCopies()
        if not copies:
            DialogMesage(self, "ERROR", "Incorrect value in number of copies").show()
            return
        PDFWriter = CardPDFWriter(file_name, card_format, paper_format, self.settings['Separation'])
        for img, num_copies in zip(self.images, copies):
            PDFWriter.addCard(img, num_copies)
        PDFWriter.close()
        DialogMesage(self, "Success!!", "PDF Exported Correctly").show()
    
    def parseNumCopies(self):
        result = []
        for it in range(self.tableWidget.rowCount()):
            try:
                num_copies = int(self.tableWidget.item(it, 1).text())
                assert num_copies >= 0
            except:
                return []
            result.append(num_copies)
        return result
    
    def removeSelected(self):
        items = sorted(map(self.tableWidget.row, self.tableWidget.selectedItems()), reverse=True)
        for it in items:
            self.tableWidget.removeRow(it)
            self.imageNames.pop(it)
            self.images.pop(it)
    
    def flushSettings(self):
        with (BASE_DIR/"Settings.json").open('w') as f:
            json.dump(self.settings, f, indent=2)
            f.flush()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    GUI = Card2PDFGUI()
    GUI.show()

    sys.exit(app.exec_())
