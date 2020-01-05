@echo off
pyuic5.exe Card2PDF/MainWindow.ui -o Card2PDF/Ui_MainWindow.py
pyrcc5.exe Card2PDF/resources.qrc -o Card2PDF/resources_rc.py
pyinstaller.exe --onefile --windowed --icon=Card2PDF/resources/app_icon.ico Card2PDF/main.py --name Card2PDF --hidden-import=requests
xcopy /y Card2PDF\Settings.json dist\