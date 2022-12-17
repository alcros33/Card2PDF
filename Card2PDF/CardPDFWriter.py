from PyQt5.QtCore import QFile, QIODevice, QSizeF, QMarginsF, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPdfWriter, QPen

from enum import Enum

def assert_file_open(func):
    def wrapper(obj, *args, **kwargs):
        if not obj.isOpen():
            raise ValueError("PDF file is closed")
        return func(obj, *args, **kwargs)
    return wrapper

class CardPDFWriter:
    RESOLUTION = 300 # 300dpi

    @staticmethod
    def mm2pix(args):
        return [x*(CardPDFWriter.RESOLUTION/25.4) for x in args]
    
    def __init__(self, file_name, card_format, paper_format, separation=[0.8, 0.8]):
        self.cardFormat = self.mm2pix(card_format)
        self.paperFormat = self.mm2pix(paper_format)
        self.separation = self.mm2pix(separation)
        self.paperFormatMM = paper_format
        self.file = QFile(str(file_name))
        self.file.open(QIODevice.WriteOnly)

        self.writer = QPdfWriter(self.file)
        self.writer.setResolution(self.RESOLUTION)
        self.writer.setPageSizeMM(QSizeF(*self.paperFormatMM))
        self.writer.setPageMargins(QMarginsF(0, 0, 0, 0))

        self.painter = QPainter(self.writer)
        self.pen = QPen()
        self.pen.setWidth(int(self.mm2pix([1])[0]))
        self.painter.setPen(self.pen)
        
        self.bleeding = [0,0]
        self.bleeding[0] = (self.paperFormat[0] % int(self.cardFormat[0] + self.separation[0]))/2
        self.bleeding[1] = (self.paperFormat[1] % int(self.cardFormat[1] + self.separation[1]))/2
        self.cursor = self.bleeding[:]

        self._setupPage()
    
    def _setupPage(self):
        # self.writer.setPageSizeMM(QSizeF(*self.paperFormatMM))
        # self.writer.setPageMargins(QMarginsF(0, 0, 0, 0))
        # Horizontal lines
        pos = self.bleeding[0] - self.separation[0]/2
        while (pos < self.paperFormat[0]):
            self.painter.drawLine(QPointF(pos, 0) , QPointF(pos, self.paperFormat[1]))
            pos += self.cardFormat[0] + self.separation[0]
        
        # Vertical lines
        pos = self.bleeding[1] - self.separation[1]/2
        while (pos < self.paperFormat[1]):
            self.painter.drawLine(QPointF(0, pos), QPointF(self.paperFormat[0], pos))
            pos += self.cardFormat[1] + self.separation[1]

    @assert_file_open
    def addPage(self):
        self.writer.newPage()
        self._setupPage()

    @assert_file_open
    def addCard(self, card, num_copies):
        for _ in range(num_copies):
            if self.cursor[1] > (self.paperFormat[1] - self.bleeding[1] - self.cardFormat[1]):
                self.cursor = self.bleeding[:]
                self.addPage()
        
            self.painter.drawPixmap(QRectF(*self.cursor, *self.cardFormat), card, QRectF(0,0, card.width(), card.height()))
            # self.painter.drawPixmap(*self.cursor, *self.cardFormat, card)
            self.cursor[0] += self.cardFormat[0] + self.separation[0]

            if self.cursor[0] > (self.paperFormat[0] - self.bleeding[0] - self.cardFormat[0]):
                self.cursor[0] = self.bleeding[0]
                self.cursor[1] += self.cardFormat[1] + self.separation[1]
                
    
    @assert_file_open
    def close(self):
        self.painter.end()
        self.file.flush()
        self.file.close()
    
    def isOpen(self): return self.file.isOpen()
