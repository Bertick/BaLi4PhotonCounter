# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwin.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(933, 453)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.graphicsView = PlotWidget(self.splitter)
        self.graphicsView.setObjectName("graphicsView")
        self.widget = QtWidgets.QWidget(self.splitter)
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.y_range_form = QtWidgets.QLineEdit(self.widget)
        self.y_range_form.setEnabled(False)
        self.y_range_form.setClearButtonEnabled(False)
        self.y_range_form.setObjectName("y_range_form")
        self.horizontalLayout.addWidget(self.y_range_form)
        self.y_range_auto = QtWidgets.QCheckBox(self.widget)
        self.y_range_auto.setChecked(True)
        self.y_range_auto.setObjectName("y_range_auto")
        self.horizontalLayout.addWidget(self.y_range_auto)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.line = QtWidgets.QFrame(self.widget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setHorizontalSpacing(7)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gate_time_select = QtWidgets.QComboBox(self.widget)
        self.gate_time_select.setObjectName("gate_time_select")
        self.gridLayout_2.addWidget(self.gate_time_select, 0, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.widget)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 1, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.widget)
        self.label_3.setObjectName("label_3")
        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 1)
        self.buffer_size_form = QtWidgets.QLineEdit(self.widget)
        self.buffer_size_form.setObjectName("buffer_size_form")
        self.gridLayout_2.addWidget(self.buffer_size_form, 1, 1, 1, 1)
        self.display_secs_form = QtWidgets.QLineEdit(self.widget)
        self.display_secs_form.setText("")
        self.display_secs_form.setObjectName("display_secs_form")
        self.gridLayout_2.addWidget(self.display_secs_form, 2, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.widget)
        self.label_5.setObjectName("label_5")
        self.gridLayout_2.addWidget(self.label_5, 2, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_2)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2.addWidget(self.splitter)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "Y Axis Max"))
        self.y_range_form.setText(_translate("MainWindow", "0.0"))
        self.y_range_auto.setText(_translate("MainWindow", "Auto"))
        self.label_4.setText(_translate("MainWindow", "Buffered Points"))
        self.label_3.setText(_translate("MainWindow", "Gate Time [msec]"))
        self.label_5.setText(_translate("MainWindow", "Display Time [sec]"))
from pyqtgraph import PlotWidget
