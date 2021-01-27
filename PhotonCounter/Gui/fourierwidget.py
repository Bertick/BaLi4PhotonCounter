# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fourierwidget.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_fouriergui(object):
    def setupUi(self, fouriergui):
        fouriergui.setObjectName("fouriergui")
        fouriergui.resize(1037, 516)
        self.horizontalLayout = QtWidgets.QHBoxLayout(fouriergui)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtWidgets.QSplitter(fouriergui)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.layoutWidget = QtWidgets.QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollplot_data = ScrollPlot(self.layoutWidget)
        self.scrollplot_data.setObjectName("scrollplot_data")
        self.verticalLayout.addWidget(self.scrollplot_data)
        self.bodeplot_fft = BodePlot(self.layoutWidget)
        self.bodeplot_fft.setObjectName("bodeplot_fft")
        self.verticalLayout.addWidget(self.bodeplot_fft)
        self.scrollplot_ifft = ScrollPlot(self.layoutWidget)
        self.scrollplot_ifft.setObjectName("scrollplot_ifft")
        self.verticalLayout.addWidget(self.scrollplot_ifft)
        self.widget = QtWidgets.QWidget(self.splitter)
        self.widget.setObjectName("widget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.dc_show_box = QtWidgets.QCheckBox(self.widget)
        self.dc_show_box.setObjectName("dc_show_box")
        self.verticalLayout_2.addWidget(self.dc_show_box)
        self.groupBox = QtWidgets.QGroupBox(self.widget)
        self.groupBox.setCheckable(False)
        self.groupBox.setChecked(False)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.filter_cFreq_prefix = QtWidgets.QComboBox(self.groupBox)
        self.filter_cFreq_prefix.setObjectName("filter_cFreq_prefix")
        self.gridLayout.addWidget(self.filter_cFreq_prefix, 1, 2, 1, 1)
        self.filter_cFreq_line = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.filter_cFreq_line.setMaximum(1000.0)
        self.filter_cFreq_line.setObjectName("filter_cFreq_line")
        self.gridLayout.addWidget(self.filter_cFreq_line, 1, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.filter_BW_line = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.filter_BW_line.setMaximum(1000.0)
        self.filter_BW_line.setObjectName("filter_BW_line")
        self.gridLayout.addWidget(self.filter_BW_line, 2, 1, 1, 1)
        self.filter_BW_prefix = QtWidgets.QComboBox(self.groupBox)
        self.filter_BW_prefix.setObjectName("filter_BW_prefix")
        self.gridLayout.addWidget(self.filter_BW_prefix, 2, 2, 1, 1)
        self.filter_selection_box = QtWidgets.QComboBox(self.groupBox)
        self.filter_selection_box.setObjectName("filter_selection_box")
        self.gridLayout.addWidget(self.filter_selection_box, 0, 1, 1, 2)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.line = QtWidgets.QFrame(self.widget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout_2.addWidget(self.line)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout.addWidget(self.splitter)

        self.retranslateUi(fouriergui)
        QtCore.QMetaObject.connectSlotsByName(fouriergui)

    def retranslateUi(self, fouriergui):
        _translate = QtCore.QCoreApplication.translate
        fouriergui.setWindowTitle(_translate("fouriergui", "Form"))
        self.dc_show_box.setText(_translate("fouriergui", "Show DC in FFT"))
        self.groupBox.setTitle(_translate("fouriergui", "Filters"))
        self.label_3.setText(_translate("fouriergui", "Bandwidth"))
        self.label.setText(_translate("fouriergui", "Filter Type"))
        self.label_2.setText(_translate("fouriergui", "Center/Cutoff"))
from .bodeplot import BodePlot
from .scrollplot import ScrollPlot
