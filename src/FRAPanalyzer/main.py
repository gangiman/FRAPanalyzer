#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sip
sip.setapi('QString', 2)

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import sys
import os
from xml.etree import cElementTree as etree

from .lifproc import LIFContainer
from .lifproc import start_bioformats
from .lifproc import stop_bioformats
from .piv import plot_piv_flow

import re
from pprint import pprint


# from PySide import QtWidgets, QtCore

import matplotlib
matplotlib.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


about_message = """
FRAP visualisation and analysis with experimental features.
"""

MAX_TABS_WIDTH = 600  # pixels

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
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


def parseXML(parent, node):
    for element in node:
        item = QtGui.QStandardItem()
        label_item = QtGui.QStandardItem()
        # item.setCheckable(True)
        tag = element.tag
        regexp = re.compile(r"\{([^\}]+)\}")
        tag = regexp.sub('', tag)
        item.setData(tag, QtCore.Qt.DisplayRole)
        label_item.setText('')
        parseXML(item, element)
        parent.appendRow((item, label_item))


def parseStrucAnnot(parent, sub_dict):
    empty_item = QtGui.QStandardItem()
    empty_item.setText('')
    for metadata, value in sub_dict.items():
        item = QtGui.QStandardItem()
        item.setData(metadata, QtCore.Qt.DisplayRole)
        if isinstance(value, str):
            text_item = QtGui.QStandardItem()
            text_item.setText(value)
            parent.appendRow((item, text_item))
        else:
            parseStrucAnnot(item, value)
            parent.appendRow(item)
            # parent.appendRow((item, empty_item))


class XmlTreeView(QtWidgets.QTreeView):

    def __init__(self, *args, **kwargs):
        super(XmlTreeView, self).__init__(*args, **kwargs)
        self.model = QtGui.QStandardItemModel()
        self.setModel(self.model)
        self.model.setColumnCount(2)
        self.model.setHeaderData(0, QtCore.Qt.Horizontal, "Metadata")
        self.model.setHeaderData(1, QtCore.Qt.Horizontal, "Value")
        self.strucan = None

    def load_xml(self, xml_string):
        xml = etree.fromstring(xml_string)
        root = xml
        parseXML(self.model, root)

    def load_structured_annotation(self, strucan):
        self.strucan = strucan

    def show_str_ann(self, series):
        self.model.removeRows(0, self.model.rowCount())
        if self.strucan is not None:
            parseStrucAnnot(self.model, self.strucan[series])


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, qApp=None):
        QtWidgets.QMainWindow.__init__(self)
        self.init_window()

        self.create_menu()

        self.qApp = qApp

        self.lif = None
        self.lif_img_data = None
        self.lif_series_order = None
        self.max_frame_count = None
        self.current_series_id = None

        self.main_widget = QtWidgets.QWidget(self)

        top_layout = QtWidgets.QHBoxLayout(self.main_widget)

        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Horizontal)
        # Left half elements
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setMaximumWidth(MAX_TABS_WIDTH)
        self.xw1 = XmlTreeView(self.main_widget)
        self.xw2 = XmlTreeView(self.main_widget)
        self.tabs.addTab(self.xw1, "Structured Annotations")
        self.tabs.addTab(self.xw2, "Limited view")
        splitter.addWidget(self.tabs)

        # Right half elements
        self.right_half = QtWidgets.QWidget(self.main_widget)
        splitter.addWidget(self.right_half)
        top_layout.addWidget(splitter)

        #   Right half vertical layout
        right_half_vertical_layout = QtWidgets.QVBoxLayout(self.right_half)
        self.right_half.setLayout(right_half_vertical_layout)

        #   Right half top (drop-down list and checkbox)
        self.right_top_widget = QtWidgets.QWidget(self.right_half)
        right_top_horizontal_layout = QtWidgets.QHBoxLayout(self.right_top_widget)
        self.right_top_widget.setLayout(right_top_horizontal_layout)

        # play button
        self.play_button = QtWidgets.QPushButton('Play', self)
        self.play_button.clicked.connect(self.handlePlayButton)
        right_top_horizontal_layout.addWidget(self.play_button)

        #       Drop-Down list
        self.combo = QtWidgets.QComboBox(self.right_half)
        self.combo.currentIndexChanged[str].connect(self.combo_callback)
        right_top_horizontal_layout.addWidget(self.combo)

        #       Flow checkbox
        self.flow_checkbox = QtWidgets.QCheckBox('Show flow', self.right_top_widget)
        self.flow_checkbox.stateChanged.connect(self.showFlow)
        right_top_horizontal_layout.addWidget(self.flow_checkbox)

        right_half_vertical_layout.addWidget(self.right_top_widget)

        #   Time Slider
        self.time_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.right_half)
        # self.time_slider.valueChanged[int].connect(self.slider_move)
        self.time_slider.sliderReleased.connect(self.slider_move)
        self.time_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        right_half_vertical_layout.addWidget(self.time_slider)
        #   Canvas for visualisation
        self.image_canvas = MyMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        right_half_vertical_layout.addWidget(self.image_canvas)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        # timer for callbacks, taken from:
        # http://ralsina.me/weblog/posts/BB974.html
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frames)

    def handlePlayButton(self):
        if self.play_button.text() == 'Play':
            value = self.time_slider.value()
            series_str = str(self.combo.currentText())
            if not series_str:
                QtWidgets.QMessageBox.about(self, "Error message",
                                            "Choose one of the series!")
            series_duration = self.lif_img_data[series_str]['T'] - 1
            if not series_duration:
                QtWidgets.QMessageBox.about(self, "Error message",
                                            "Only one image in a series!")
            if value == series_duration:
                self.time_slider.setValue(0)
            self.timer.start(1000 / series_duration)
            self.play_button.setText("Stop")
        elif self.play_button.text() == 'Stop':
            self.timer.stop()
            self.play_button.setText("Play")

    def update_frames(self):
        value = self.time_slider.value()
        if value == self.max_frame_count:
            self.timer.stop()
            self.play_button.setText("Play")
            return
        img = self.lif.get_image(t=value + 1, series_id=self.current_series_id)
        self.redraw_canvas(img)
        self.time_slider.setValue(value + 1)

    def init_window(self):
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Frap analyzer")
        start_bioformats()

    def create_menu(self):
        self.file_menu = QtWidgets.QMenu('&File', self)
        self.export_menu = QtWidgets.QMenu('&Export', self)
        self.file_menu.addAction('&Select LIF File', self.callOpenFileDialog, QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.file_menu.addAction('&Quit', self.fileQuit, QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)
        self.help_menu = QtWidgets.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)

    def callOpenFileDialog(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '.', ".lif(*.lif)")
        self.openFile(filename)

    def openFile(self, filename):
        print("Opening file: {0}".format(filename))
        self.lif = LIFContainer(filename)
        self.lif_img_data = self.lif.get_image_data()
        pprint(self.lif_img_data)
        # self.lif_series_order = sorted(self.lif_img_data.keys())
        self.lif_series_order = self.lif_img_data.keys()
        self.combo.clear()
        self.combo.addItems(self.lif_series_order)
        start_img = self.lif.get_image(series_id=0)
        self.redraw_canvas(start_img)
        self.xw1.load_structured_annotation(
            self.lif.get_structured_annotations())
        self.xw1.show_str_ann(self.lif_series_order[0])

    def showFlow(self, state):
        if state == QtCore.Qt.Checked:
            value = self.time_slider.value()
            series_str = str(self.combo.currentText())
            max_id = (self.lif_img_data[series_str]['T'] - 1)
            if value == max_id:
                value -= 1
            plot_piv_flow(
                self.lif.get_image(t=value, series_id=self.current_series_id),
                self.lif.get_image(t=value + 3, series_id=self.current_series_id),
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
        self.max_frame_count = self.lif_img_data[series_str]['T'] - 1
        self.time_slider.setRange(0, self.max_frame_count)
        self.time_slider.setValue(0)
        self.time_slider.setTickInterval(self.max_frame_count / 10)

        self.current_series_id = self.lif_series_order.index(series_str)
        img = self.lif.get_image(series_id=self.current_series_id)
        self.redraw_canvas(img)
        self.xw1.show_str_ann(series_str)

    def close(self):
        stop_bioformats()
        super(ApplicationWindow, self).close()
        sys.exit(self.qApp.exec_())

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "About", about_message)
