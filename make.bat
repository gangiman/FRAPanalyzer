pyinstaller --onefile --name frapanalyzer --runtime-hook=.\env\rthook_pyqt4.py ".\src\main.py"