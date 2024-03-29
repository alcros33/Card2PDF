import sys
from pathlib import Path
from collections import defaultdict, Counter
import zlib, base64
from PyQt5 import QtCore, QtGui, QtWidgets
import requests

BASE_DIR = Path(sys.argv[0]).resolve().parent
PIC_DIR = BASE_DIR/"pics"
PIC_DIR.mkdir(exist_ok=True)
BASE_URL = "https://images.ygoprodeck.com/images/cards/"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def download_file(url, path):
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print(f"Error downloading {url}")
        return False
    with path.open('wb') as f:
        f.write(r.content)
    return True

def download_pic_by_id(card_id):
    path = (PIC_DIR/card_id).with_suffix(".jpg")
    if path.exists():
        return path
    if download_file(BASE_URL+card_id+".jpg", path):
        return path
    return None

def parse_ygo_deck():
    cb_contents = QtGui.QGuiApplication.clipboard().text()
    print(cb_contents)
    byte_data = zlib.decompress(base64.b64decode(cb_contents), -8)
    ids = [int.from_bytes(byte_data[i:i+4], 'little') for i in range(2, len(byte_data[2:]), 4)]
    return Counter(ids[:byte_data[0]+byte_data[1]])

class DialogPBar(QtWidgets.QDialog):
    def __init__(self,parent, title, msg):
        super().__init__(parent)
        self.resize(485, 180)
        self.setWindowTitle(title)
        
        self.message = QtWidgets.QLabel(self)
        self.message.setGeometry(QtCore.QRect(50, 20, 370, 30))
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.message.setObjectName("message")
        self.message.setText(msg)
        
        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setGeometry(QtCore.QRect(100, 80, 300, 30))
        self.progress.setObjectName("progress")
        self.progress.setMaximum(100)

        self.status = QtWidgets.QLabel(self)
        self.status.setGeometry(QtCore.QRect(50, 130, 370, 30))
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.status.setObjectName("status")
    
    @QtCore.pyqtSlot(str)
    def updateStatus(self, msg):
        self.status.setText(msg)

class Worker(QtCore.QThread):
    def __init__(self, parent, iterable, work):
        super().__init__(parent)
        self.iterable = iterable
        self.work = work
    countChanged = QtCore.pyqtSignal(int)
    valChanged = QtCore.pyqtSignal(str)
    def run(self):
        n = len(self.iterable)
        for it, val in enumerate(self.iterable):
            self.valChanged.emit(f"{val} -- {it+1}/{n}")
            self.work(val)
            self.countChanged.emit(100*(it+1)//n)

class YGOProParser:
    def __init__(self, parent):
        self.parent = parent
        parent.menuYGOPro = QtWidgets.QMenu(parent.menubar)
        parent.menuYGOPro.setObjectName("menuImport")
        parent.menuYGOPro.setTitle("Import")

        parent.actionYGOProDeck = QtWidgets.QAction(parent)
        parent.actionYGOProDeck.setObjectName("actionParseOmegaDeck")
        parent.menuYGOPro.addAction(parent.actionYGOProDeck)
        parent.actionYGOProDeck.setText("Import Omega Code from clipboard")
        parent.menubar.addAction(parent.menuYGOPro.menuAction())
        parent.actionYGOProDeck.triggered.connect(self.parseYGOProDeck)
    
    def parseYGOProDeck(self):
        try:
            card2num = parse_ygo_deck()
        except RuntimeError:
            print("Error in file")
        path2num = dict()
        not_found = []
        # Progressbar dialog
        dia = DialogPBar(self.parent, "Downloading...", "Downloading Pics From YGOPro...")
        dia.progress.setValue(0)
        # Define work callable
        def work(card_id):
            path = download_pic_by_id(str(card_id))
            if path is None:
                not_found.append(card_id)
            else:
                path2num[str(path)] = card2num[card_id]
        # Define worker
        w = Worker(dia, card2num.keys(), work)
        w.countChanged.connect(dia.progress.setValue)
        w.valChanged.connect(dia.updateStatus)
        # Start download
        dia.show()
        w.start()
        while w.isRunning():
            QtCore.QCoreApplication.processEvents()
        dia.close()
        ## Update table
        # Change num_copies of duplicates
        for it, name in enumerate(self.parent.imageNames):
            if name not in path2num:
                continue
            try:
                num_copies = int(self.parent.tableWidget.item(it, 1).text())
                assert num_copies >= 0
            except:
                num_copies = 0
            num_copies += path2num.pop(name)
            self.parent.tableWidget.setItem(it, 1, QtWidgets.QTableWidgetItem(str(num_copies)))
        # Add new cards
        old_len = len(self.parent.imageNames)
        self.parent.addImgsToTable(path2num.keys())
        for it, key in enumerate(path2num.keys()):
            copies = str(path2num[key])
            self.parent.tableWidget.setItem(it+old_len, 1, QtWidgets.QTableWidgetItem(copies))
        self.parent.cardComboBox.setCurrentIndex(self.parent.cardComboBox.findText("Yugioh"))