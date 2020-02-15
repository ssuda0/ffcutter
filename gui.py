# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_main(object):
    def setupUi(self, main):
        main.setObjectName("main")
        main.resize(617, 558)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(main.sizePolicy().hasHeightForWidth())
        main.setSizePolicy(sizePolicy)
        main.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        self.verticalLayout = QtWidgets.QVBoxLayout(main)
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName("verticalLayout")        
        
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(3, 3, 3, 3)
        self.horizontalLayout_3.setSpacing(3)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")        
        
        self.video = QtWidgets.QWidget(main)
        self.video.setFocusPolicy(QtCore.Qt.NoFocus)
        self.video.setStyleSheet("background-color: rgb(117, 80, 123);")
        self.video.setObjectName("video")
        self.horizontalLayout_3.addWidget(self.video)
        
        
#################################################
#        data = [
#            {"type": "Fruit", "objects": ["Apple", "Banana"]},
#            {"type": "Vegetable", "objects": ["Carrot", "Tomato"]s},
#        ]
#        self.model = QtGui.QStandardItemModel()
#        self.model.setHorizontalHeaderLabels(['video name'])
#        
#        d = data[0]
#        item = QtGui.QStandardItem(d["type"])
#        child = QtGui.QStandardItem(d["objects"][0])  # Apple
#        item.appendRow(child)
#        child = QtGui.QStandardItem(d["objects"][1])  # Banana
#        item.appendRow(child)
#        self.model.setItem(0, 0, item)
#        
#        self.view = QtWidgets.QTreeView()
#        self.view.setFocusPolicy(QtCore.Qt.NoFocus)
#        self.view.setObjectName("video_names")
#        self.view.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
#        self.view.setModel(self.model)
#
#        self.view.setAnimated(True)
#        self.view.setFixedWidth(300)
#        self.horizontalLayout_3.addWidget(self.view)
##########################################################
        
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        
        self.widget = QtWidgets.QWidget(main)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout_2.setContentsMargins(9, 3, 9, 3)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.keep = QtWidgets.QRadioButton(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.keep.sizePolicy().hasHeightForWidth())
        self.keep.setSizePolicy(sizePolicy)
        self.keep.setFocusPolicy(QtCore.Qt.NoFocus)
        self.keep.setChecked(True)
        self.keep.setObjectName("keep")
        self.horizontalLayout_2.addWidget(self.keep)
        
        self.remove = QtWidgets.QRadioButton(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.remove.sizePolicy().hasHeightForWidth())
        self.remove.setSizePolicy(sizePolicy)
        self.remove.setFocusPolicy(QtCore.Qt.NoFocus)
        self.remove.setToolTip("")
        self.remove.setStatusTip("")
        self.remove.setObjectName("remove")
        self.horizontalLayout_2.addWidget(self.remove)
        
        self.status = QtWidgets.QLabel(self.widget)
        self.status.setText("")
        self.status.setObjectName("status")
        self.horizontalLayout_2.addWidget(self.status)
        
        spacerItem = QtWidgets.QSpacerItem(383, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        
        self.toggleArgsEdit = QtWidgets.QToolButton(self.widget)
        self.toggleArgsEdit.setMinimumSize(QtCore.QSize(0, 23))
        self.toggleArgsEdit.setFocusPolicy(QtCore.Qt.NoFocus)
        self.toggleArgsEdit.setObjectName("toggleArgsEdit")
        self.horizontalLayout_2.addWidget(self.toggleArgsEdit)
        
        self.print = QtWidgets.QToolButton(self.widget)
        self.print.setMinimumSize(QtCore.QSize(0, 23))
        self.print.setSizeIncrement(QtCore.QSize(10, 0))
        self.print.setFocusPolicy(QtCore.Qt.NoFocus)
        self.print.setObjectName("print")
        self.horizontalLayout_2.addWidget(self.print)
        
        self.run = QtWidgets.QToolButton(self.widget)
        self.run.setMinimumSize(QtCore.QSize(0, 23))
        self.run.setFocusPolicy(QtCore.Qt.NoFocus)
        self.run.setObjectName("run")
        self.horizontalLayout_2.addWidget(self.run)
        
        self.openFile = QtWidgets.QToolButton(self.widget)
        self.openFile.setMinimumSize(QtCore.QSize(0, 23))
        self.openFile.setFocusPolicy(QtCore.Qt.NoFocus)
        self.openFile.setObjectName("open file")
        self.horizontalLayout_2.addWidget(self.openFile)
        
        self.verticalLayout.addWidget(self.widget)
        self.argsEdit = QtWidgets.QPlainTextEdit(main)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.argsEdit.sizePolicy().hasHeightForWidth())
        self.argsEdit.setSizePolicy(sizePolicy)
        self.argsEdit.setMaximumSize(QtCore.QSize(16777215, 90))
        self.argsEdit.setObjectName("argsEdit")
        self.verticalLayout.addWidget(self.argsEdit)
        
        self.seekbar = QtWidgets.QWidget(main)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.seekbar.sizePolicy().hasHeightForWidth())
        self.seekbar.setSizePolicy(sizePolicy)
        self.seekbar.setMaximumSize(QtCore.QSize(16777215, 30))
        self.seekbar.setMouseTracking(True)
        self.seekbar.setFocusPolicy(QtCore.Qt.NoFocus)
        self.seekbar.setAutoFillBackground(False)
        self.seekbar.setStyleSheet("background-color: rgba(0,0,0,50);")
        self.seekbar.setObjectName("seekbar")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.seekbar)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.loading = QtWidgets.QLabel(self.seekbar)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.loading.sizePolicy().hasHeightForWidth())
        self.loading.setSizePolicy(sizePolicy)
        self.loading.setStyleSheet("background-color: none;")
        self.loading.setAlignment(QtCore.Qt.AlignCenter)
        self.loading.setObjectName("loading")
        self.horizontalLayout.addWidget(self.loading)
        self.verticalLayout.addWidget(self.seekbar)

        self.retranslateUi(main)
        QtCore.QMetaObject.connectSlotsByName(main)

    def retranslateUi(self, main):
        _translate = QtCore.QCoreApplication.translate
        main.setWindowTitle(_translate("main", "ffcutter"))
        self.keep.setText(_translate("main", "Keep"))
        self.remove.setText(_translate("main", "Remove"))
        self.toggleArgsEdit.setToolTip(_translate("main", "Show/hide ffmpeg arguments editor"))
        self.toggleArgsEdit.setText(_translate("main", "Edit Args"))
        self.toggleArgsEdit.setShortcut(_translate("main", "E"))
        self.print.setToolTip(_translate("main", "Print ffmpeg commands into terminal"))
        self.print.setText(_translate("main", "Print"))
        self.print.setShortcut(_translate("main", "P"))
        
        self.run.setToolTip(_translate("main", "Run ffmpeg commands."))
        self.run.setText(_translate("main", "Run"))
        self.run.setShortcut(_translate("main", "R"))
        
        self.openFile.setToolTip(_translate("main", "Open File ffmpeg commands."))
        self.openFile.setText(_translate("main", "Open File"))
        self.openFile.setShortcut(_translate("main", "Open File"))
        
        self.argsEdit.setPlainText(_translate("main", "out: \n"
"# FFmpeg output arguments.\n"
"out-args: \n"
"# FFmpeg Input arguments.\n"
"in-args: "))
        self.loading.setText(_translate("main", "Loading..."))

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'shift_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_shiftDialog(object):
    def setupUi(self, shiftDialog):
        shiftDialog.setObjectName("shiftDialog")
        shiftDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        shiftDialog.resize(240, 117)
        shiftDialog.setSizeGripEnabled(False)
        shiftDialog.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(shiftDialog)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.verticalLayout.setObjectName("verticalLayout")
        self.suggestion = QtWidgets.QLabel(shiftDialog)
        self.suggestion.setEnabled(True)
        self.suggestion.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.suggestion.setObjectName("suggestion")
        self.verticalLayout.addWidget(self.suggestion)
        self.widget = QtWidgets.QWidget(shiftDialog)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 9, 0, 9)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.a = QtWidgets.QSpinBox(self.widget)
        self.a.setMinimum(-999)
        self.a.setMaximum(999)
        self.a.setObjectName("a")
        self.horizontalLayout.addWidget(self.a)
        spacerItem = QtWidgets.QSpacerItem(5, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label_2 = QtWidgets.QLabel(self.widget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.b = QtWidgets.QSpinBox(self.widget)
        self.b.setMinimum(-999)
        self.b.setMaximum(999)
        self.b.setObjectName("b")
        self.horizontalLayout.addWidget(self.b)
        self.verticalLayout.addWidget(self.widget)
        self.buttonBox = QtWidgets.QDialogButtonBox(shiftDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(shiftDialog)
        self.buttonBox.accepted.connect(shiftDialog.accept)
        self.buttonBox.rejected.connect(shiftDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(shiftDialog)

    def retranslateUi(self, shiftDialog):
        _translate = QtCore.QCoreApplication.translate
        shiftDialog.setWindowTitle(_translate("shiftDialog", "Global Frame Shift"))
        self.suggestion.setText(_translate("shiftDialog", "Suggested values:"))
        self.label.setText(_translate("shiftDialog", "Start:"))
        self.label_2.setText(_translate("shiftDialog", "End:"))

