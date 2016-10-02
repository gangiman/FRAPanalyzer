#!/usr/bin/env python

from __future__ import unicode_literals
import sys
import os
from xml.etree import cElementTree as etree
import matplotlib
from lifproc import LIFContainer
from lifproc import start_bioformats
from lifproc import stop_bioformats

from piv import plot_piv_flow

import re
from pprint import pprint

matplotlib.rcParams['backend.qt4'] = 'PySide'

from PySide import QtGui, QtCore

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

about_message = """
FRAP visualisation and analysis with experimental features.
"""


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


def parseXML(parent, node):
    for element in node:
        item = QtGui.QStandardItem()
        item.setCheckable(True)
        tag = element.tag
        regexp = re.compile(r"\{([^\}]+)\}")
        tag = regexp.sub('', tag)
        item.setData(tag, QtCore.Qt.DisplayRole)
        parseXML(item, element)
        parent.appendRow(item)


class XmlTreeView(QtGui.QTreeView):

    def __init__(self, *args, **kwargs):
        super(XmlTreeView, self).__init__(*args, **kwargs)

    def load_xml(self, xml_string):
        xml = etree.fromstring(xml_string)
        root = xml
        self.mdl = QtGui.QStandardItemModel()
        self.setModel(self.mdl)
        parseXML(self.mdl, root)


class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.init_window()

        self.create_menu()

        self.lif = None
        self.lif_img_data = None
        self.lif_series_order = None

        self.main_widget = QtGui.QWidget(self)

        top_layout = QtGui.QHBoxLayout(self.main_widget)

        # Left half elements
        self.tabs = QtGui.QTabWidget()
        self.xw1 = XmlTreeView(self.main_widget)
        self.xw2 = XmlTreeView(self.main_widget)
        self.tabs.addTab(self.xw1, "Full view")
        self.tabs.addTab(self.xw2, "Limited view")
        top_layout.addWidget(self.tabs)

        # Right half elements
        self.right_half = QtGui.QWidget(self.main_widget)
        top_layout.addWidget(self.right_half)

        #   Right half vertical layout
        right_half_vertical_layout = QtGui.QVBoxLayout(self.right_half)
        self.right_half.setLayout(right_half_vertical_layout)

        #   Right half top (drop-down list and checkbox)
        self.right_top_widget = QtGui.QWidget(self.right_half)
        right_top_horizontal_layout = QtGui.QHBoxLayout(self.right_top_widget)
        self.right_top_widget.setLayout(right_top_horizontal_layout)

        #       Drop-Down list
        self.combo = QtGui.QComboBox(self.right_half)
        self.combo.currentIndexChanged[str].connect(self.combo_callback)
        right_top_horizontal_layout.addWidget(self.combo)

        #       Flow checkbox
        self.flow_checkbox = QtGui.QCheckBox('Show flow', self.right_top_widget)
        self.flow_checkbox.stateChanged.connect(self.showFlow)
        right_top_horizontal_layout.addWidget(self.flow_checkbox)

        right_half_vertical_layout.addWidget(self.right_top_widget)

        #   Time Slider
        self.time_slider = QtGui.QSlider(QtCore.Qt.Horizontal, self.right_half)
        # self.time_slider.valueChanged[int].connect(self.slider_move)
        self.time_slider.sliderReleased.connect(self.slider_move)
        self.time_slider.setTickPosition(QtGui.QSlider.TicksBelow)
        right_half_vertical_layout.addWidget(self.time_slider)
        #   Canvas for visualisation
        self.image_canvas = MyMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        right_half_vertical_layout.addWidget(self.image_canvas)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        # self.statusBar().showMessage("All hail matplotlib!", 2000)

    def init_window(self):
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Frap analyzer")
        start_bioformats()

    def create_menu(self):
        self.file_menu = QtGui.QMenu('&File', self)
        self.export_menu = QtGui.QMenu('&Export', self)
        self.file_menu.addAction('&Select LIF File', self.callOpenFileDialog, QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.file_menu.addAction('&Quit', self.fileQuit, QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)
        self.help_menu = QtGui.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)

    def callOpenFileDialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File', '.', ".lif(*.lif)")
        self.openFile(filename[0])

    def openFile(self, filename):
        self.lif = LIFContainer(filename)
        self.lif_img_data = self.lif.get_image_data()
        pprint(self.lif_img_data)
        # self.lif_series_order = sorted(self.lif_img_data.keys())
        self.lif_series_order = self.lif_img_data.keys()
        self.combo.clear()
        self.combo.addItems(self.lif_series_order)
        start_img = self.lif.get_image(series_id=0)
        self.redraw_canvas(start_img)
        self.xw1.load_xml(self.lif.metadata_in_xml)

    def showFlow(self, state):
        if state == QtCore.Qt.Checked:
            value = self.time_slider.value()
            series_str = str(self.combo.currentText())
            max_id = (self.lif_img_data[series_str]['T'] - 1)
            if value == max_id:
                value -= 1
            plot_piv_flow(
                self.lif.get_image(t=value, series_id=self.current_series_id),
                self.lif.get_image(t=value + 1, series_id=self.current_series_id),
                axes=self.image_canvas.axes
            )
            self.image_canvas.draw()
        else:
            print("Not Show flow")

    def slider_move(self):
        value = self.time_slider.value()
        print("new slider position {0}".format(value))
        if hasattr(self, "lif"):
            img = self.lif.get_image(t=value, series_id=self.current_series_id)
            self.redraw_canvas(img)
        else:
            print("No lif-file opened.")

    def redraw_canvas(self, data):
        self.image_canvas.axes.imshow(data)
        self.image_canvas.draw()

    def combo_callback(self, series_str):
        if not series_str:
            return
        self.time_slider.setRange(0, self.lif_img_data[series_str]['T'] - 1)
        self.time_slider.setValue(0)
        self.time_slider.setTickInterval(round((self.lif_img_data[series_str]['T']-1)/10.0))

        self.current_series_id = self.lif_series_order.index(series_str)
        img = self.lif.get_image(series_id=self.current_series_id)
        self.redraw_canvas(img)

    def close(self):
        stop_bioformats()
        super(ApplicationWindow, self).close()

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtGui.QMessageBox.about(self, "About", about_message)

if __name__ == '__main__':
    qApp = QtGui.QApplication(sys.argv)
    aw = ApplicationWindow()
    if len(sys.argv) > 1:
        if os.path.exists(sys.argv[1]):
            aw.openFile(sys.argv[1])
        else:
            print("{0} file doesn't exist!".format(sys.argv[1]))
    # aw.setWindowTitle("%s" % progname)
    aw.show()
    sys.exit(qApp.exec_())
