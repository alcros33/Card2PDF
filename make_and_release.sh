#! /usr/bin/bash
pyuic5 Card2PDF/MainWindow.ui -o Card2PDF/Ui_MainWindow.py
pyrcc5 Card2PDF/resources.qrc -o Card2PDF/resources_rc.py
pyinstaller --onefile --windowed --icon=Card2PDF/resources/app_icon.ico Card2PDF/main.py --name Card2PDF --hidden-import=requests