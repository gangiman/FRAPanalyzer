import argparse
from PySide import QtGui, QtCore

def parseOpt():
    parser = argparse.ArgumentParser(description="Check if the files in this folder are valid EXRs")
    parser.add_argument("-file", dest="filepath", help="The file path to be checked.")
    return parser.parse_args()
ARGS = parseOpt()

class CheckableDirModel(QtGui.QDirModel):
    # a class to put checkbox on the folders
    def __init__(self, parent=None):
        QtGui.QDirModel.__init__(self, None)
        self.checks = {}

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.CheckStateRole:
            return QtGui.QDirModel.data(self, index, role)
        else:
            if index.column() == 0:
                return self.checkState(index)

    def flags(self, index):
        return QtGui.QDirModel.flags(self, index) | QtCore.Qt.ItemIsUserCheckable

    def checkState(self, index):
        if index in self.checks:
            return self.checks[index]
        else:
            return QtCore.Qt.Unchecked

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            self.checks[index] = value
            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
            return True 

        return QtGui.QDirModel.setData(self, index, value, role)

    #def filtering(self, index):
    #   self.checks.setFilter(QtCore.QDir.Dirs|QtCore.QDir.NoDotAndDotDot)




class Ui_Dialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self,parent)
        self.setObjectName("Dialog")
        self.resize(600, 500)

        self.llayout = QtGui.QVBoxLayout(parent)

        self.model = CheckableDirModel()
        self.model.setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)

        #self.tree = QtGui.QTreeWidget()
        self.tree = QtGui.QTreeView()
        self.tree.setModel(self.model)
        self.tree.setSortingEnabled(True)
        self.tree.setRootIndex(self.model.index(ARGS.filepath))

        #self.tree.hideColumn(1)
        #self.tree.hideColumn(2)
        #self.tree.hideColumn(3)

        self.tree.setWindowTitle("Dir View")
        self.tree.resize(400, 480)
        self.tree.setColumnWidth(0, 200)

        self.but = QtGui.QPushButton(str("Run"))

        self.llayout.addWidget(self.tree)
        self.llayout.addWidget(self.but)

        self.setLayout(self.llayout)

        self.but.clicked.connect(self.print_path)

    def print_path(self):
        print "hello"
        root = self.tree.childCount()
        print root
        for i in range(root):
            print i.text()

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = Ui_Dialog()
    ui.show()
    sys.exit(app.exec_())
