#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import os
from qtpy import QtWidgets
from FRAPanalyzer.main import ApplicationWindow

progname = os.path.basename(sys.argv[0])
progversion = "0.1"


if __name__ == '__main__':
    qApp = QtWidgets.QApplication(sys.argv)
    aw = ApplicationWindow(qApp=qApp)
    if len(sys.argv) > 1:
        if os.path.exists(sys.argv[1]):
            aw.openFile(sys.argv[1])
        else:
            print("{0} file doesn't exist!".format(sys.argv[1]))
    # aw.setWindowTitle("%s" % progname)
    aw.show()
    sys.exit(qApp.exec_())
