
import math
import queue
import sys
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from pyqtgraph.GraphicsScene.mouseEvents import MouseClickEvent
import scipy.io.wavfile
import sounddevice as sd
import beepy
from scipy import signal as sig
import simpleaudio as sa
import vlc
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSlider
from scipy.io import wavfile
import logging

logging.basicConfig(level=logging.INFO, filename='log.txt',
                    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

matplotlib.use('Qt5Agg')

sample_rate= 44100 #Hz
octave = ['C', 'c', 'D', 'd', 'E', 'F', 'f', 'G', 'g', 'A', 'a', 'B']

class MplCanvas_spec_empty(FigureCanvas):

    def __init__(self, parent=None, width=4, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.set(xlabel='time (sec)', ylabel='frequency (Hz)', title = "Spectrogram" )
        super(MplCanvas_spec_empty, self).__init__(fig)

class Canvas_spec(FigureCanvas):
    def __init__(self, amplitude, fs):

        fig, self.ax = plt.subplots(figsize=(5, 4))
        super().__init__(fig)

        """
        Matplotlib Script
        """
        if math.log2(len(amplitude)) >= 256:
            nfft = math.floor(math.log2(len(amplitude)))
        else:
            nfft = 256

        noverlap = int(nfft*0.88)
        self.ax.specgram(amplitude, NFFT=nfft, Fs=fs,noverlap=noverlap, cmap="plasma")

        self.ax.set(xlabel='time (sec)', ylabel='frequency (Hz)', title = "Spectrogram")
        self.ax.grid()


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        fig.tight_layout()


class Worker(QtCore.QRunnable):

    def __init__(self, function, *args, **kwargs):
        super(Worker, self).__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):

        self.function(*self.args, **self.kwargs)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1090, 689)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget(self.tabWidget)
        self.tab.setObjectName("tab")
        self.gridLayout_tab1 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_tab1.setObjectName("gridLayout")
        self.label_volume = QtWidgets.QLabel(self.tab)
        self.label_volume.setObjectName("label")
        self.gridLayout_tab1.addWidget(self.label_volume,0,0)


        self.verticalSlider_volume = QtWidgets.QSlider(self.tab)
        self.verticalSlider_volume.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider_volume.setObjectName("verticalSlider_volume")
        self.gridLayout_tab1.addWidget(self.verticalSlider_volume,1,0,3,1)
        self.verticalSlider_volume.setMinimum(0)
        self.verticalSlider_volume.setMaximum(200)
        self.verticalSlider_volume.setValue(100)
        self.verticalSlider_volume.setTickInterval(20)
        self.verticalSlider_volume.setSingleStep(20)
        self.verticalSlider_volume.setTickPosition(QSlider.TicksBelow)
        self.verticalSlider_volume.valueChanged.connect(lambda: self.adjust_volume())

        self.pushButton_play = QtWidgets.QPushButton(self.tab)
        self.pushButton_play.setObjectName("pushButton_play")

        self.pushButton_play.clicked.connect(lambda: self.play_pause())
        self.gridLayout_tab1.addWidget(self.pushButton_play,4,0,1,1)

        self.pushButton_equalize = QtWidgets.QPushButton(self.tab)
        self.pushButton_equalize.setObjectName("pushButton")

        self.pushButton_equalize.clicked.connect(lambda: self.equalize())
        self.gridLayout_tab1.addWidget(self.pushButton_equalize,5,0,1,1)

        self.splitter_graphs = QtWidgets.QSplitter(self.tab)
        self.splitter_graphs.setGeometry(QtCore.QRect(110, 70, 951, 331))
        self.splitter_graphs.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_graphs.setObjectName("splitter_graphs")
        self.gridLayout_tab1.addWidget(self.splitter_graphs,0,1,6,4)
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.splitter_graphs.addWidget(self.canvas)
        self.empty_spec = MplCanvas_spec_empty(self, width=5, height=4, dpi=100)
        self.splitter_graphs.addWidget(self.empty_spec)

        self.horizontalSlider_piano = QtWidgets.QSlider(self.tab)
        self.gridLayout_tab1.addWidget(self.horizontalSlider_piano,1,6,1,1)

        self.horizontalSlider_altoSaxophone = QtWidgets.QSlider(self.tab)
        self.gridLayout_tab1.addWidget(self.horizontalSlider_altoSaxophone,2,6,1,1)

        self.horizontalSlider_guitar = QtWidgets.QSlider(self.tab)
        self.gridLayout_tab1.addWidget(self.horizontalSlider_guitar,3,6,1,1)

        self.horizontalSlider_bass = QtWidgets.QSlider(self.tab)
        self.gridLayout_tab1.addWidget(self.horizontalSlider_bass,0,6,1,1)

        self.horizontalSlider_bell = QtWidgets.QSlider(self.tab)
        self.gridLayout_tab1.addWidget(self.horizontalSlider_bell,5,6,1,1)

        self.horizontalSlider_flute = QtWidgets.QSlider(self.tab)
        self.gridLayout_tab1.addWidget(self.horizontalSlider_flute,4,6,1,1)

        self.sliders = [self.horizontalSlider_piano,self.horizontalSlider_altoSaxophone,
        self.horizontalSlider_guitar,self.horizontalSlider_bass,self.horizontalSlider_bell,self.horizontalSlider_flute]
        
        self.sliders_names = ["horizontalSlider_piano","horizontalSlider_altoSaxophone","horizontalSlider_guitar",
        "horizontalSlider_bass","horizontalSlider_bell","horizontalSlider_flute"]

        for i in range(len(self.sliders)):
            self.sliders[i].setOrientation(QtCore.Qt.Horizontal)
            self.sliders[i].setMinimum(0)
            self.sliders[i].setMaximum(10)
            self.sliders[i].setValue(1)
            self.sliders[i].setTickInterval(1)
            self.sliders[i].setSingleStep(1)
            self.sliders[i].setTickPosition(QSlider.TicksBelow)
            self.sliders[i].setObjectName(self.sliders_names[i])

        bass_image = QtGui.QPixmap('Bass')
        self.label_bass = QtWidgets.QLabel(self.tab)
        self.label_bass.setPixmap(bass_image)
        self.label_bass.setObjectName("label_bass")
        self.gridLayout_tab1.addWidget(self.label_bass,0,5,1,1)

        piano_image = QtGui.QPixmap('Piano')
        self.label_piano = QtWidgets.QLabel(self.tab)
        self.label_piano.setPixmap(piano_image)
        self.label_piano.setObjectName("label_piano")
        self.gridLayout_tab1.addWidget(self.label_piano,1,5,1,1)

        saxophone_image = QtGui.QPixmap('Saxophone')
        self.label_saxophone = QtWidgets.QLabel(self.tab)
        self.label_saxophone.setPixmap(saxophone_image)
        self.label_saxophone.setObjectName("label_saxophone")
        self.gridLayout_tab1.addWidget(self.label_saxophone,2,5,1,1)

        guitar_image = QtGui.QPixmap('guitar')
        self.label_guitar = QtWidgets.QLabel(self.tab)
        self.label_guitar.setPixmap(guitar_image)
        self.label_guitar.setObjectName("label_guitar")
        self.gridLayout_tab1.addWidget(self.label_guitar,3,5,1,1)

        flute_image = QtGui.QPixmap('flute')
        self.label_flute = QtWidgets.QLabel(self.tab)
        self.label_flute.setPixmap(flute_image)
        self.label_flute.setObjectName("label_flute")
        self.gridLayout_tab1.addWidget(self.label_flute,4,5,1,1)

        bell_image = QtGui.QPixmap('bell')
        self.label_bell = QtWidgets.QLabel(self.tab)
        self.label_bell.setPixmap(bell_image)
        self.label_bell.setObjectName("label_bell")
        self.gridLayout_tab1.addWidget(self.label_bell,5,5,1,1)

        self.tabWidget.addTab(self.tab, "")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.gridLayout.addWidget(self.tabWidget, 15, 15)
        self.gridLayout_tab2 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_tab2.setObjectName("gridLayout")

        self.piano_image = QPixmap('piano_img.png')
        self.label_piano = QtWidgets.QLabel(self.tab_2)
        self.label_piano.setPixmap(self.piano_image)
        self.label_piano.setObjectName("Piano_label")
        self.label_piano.setGeometry(9, 205, 420, 194)
        # self.gridLayout_tab2.addWidget(self.label_piano,0,0,1,1)

        self.settings_combobox_label=QtWidgets.QLabel(self.tab_2)
        self.settings_combobox_label.setObjectName("combobox_label")
        self.settings_combobox_label.setGeometry(30,430,200,20)


        piano_modes_names = ["Octave","Major sixth","Minor sixth","Perfect fifth","Perfect fourth","Major third","Minor third"]
        self.piano_settings_combobox = QtWidgets.QComboBox(self.tab_2)
        self.piano_settings_combobox.setObjectName("piano_settings_combobox")
        self.piano_settings_combobox.setGeometry(30,460,150,20)

        for name in piano_modes_names:
             self.piano_settings_combobox.addItem(name)

        self.piano_mode=2
        self.piano_modes={0:2,1:(5/2),2:(8/5),3:1.5,4:(4/3),5:(5/4),6:(6/5)}
        self.piano_settings_combobox.currentIndexChanged.connect(lambda: self.piano_mode_picker())

        self.piano_far_left_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_far_left_btn.setObjectName("click for paino note")
        self.piano_far_left_btn.setGeometry(9, 205, 58, 194)
        self.piano_far_left_btn.setStyleSheet("background-color:rgb(226,226,226);background-color: white;")
        self.piano_far_left_btn.clicked.connect(lambda: self.played_instrument_key(0, 261.63, 12))

        self.piano_second_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_second_btn.setObjectName("click for paino note")
        self.piano_second_btn.setGeometry(66, 205, 58, 194)
        self.piano_second_btn.setStyleSheet("background-color:rgb(226,226,226);background-color: white;")
        self.piano_second_btn.clicked.connect(lambda: self.played_instrument_key(2, 261.63, 12))

        self.piano_far_left_black_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_far_left_black_btn.setObjectName("click for paino note")
        self.piano_far_left_black_btn.setGeometry(39, 205, 35, 130)
        self.piano_far_left_black_btn.setStyleSheet("background-color:rgb(50,50,50);background-color: black;")
        self.piano_far_left_black_btn.clicked.connect(lambda: self.played_instrument_key(1, 261.63, 12))

        self.piano_third_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_third_btn.setObjectName("click for paino note")
        self.piano_third_btn.setGeometry(123, 205, 58, 194)
        self.piano_third_btn.setStyleSheet("background-color:rgb(226,226,226);background-color: white;")
        self.piano_third_btn.clicked.connect(lambda: self.played_instrument_key(4, 261.63, 12))

        self.piano_forth_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_forth_btn.setObjectName("click for paino note")
        self.piano_forth_btn.setGeometry(180, 205, 58, 194)
        self.piano_forth_btn.setStyleSheet("background-color:rgb(226,226,226);background-color: white;")
        self.piano_forth_btn.clicked.connect(lambda: self.played_instrument_key(5, 261.63, 12))

        self.piano_second_black_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_second_black_btn.setObjectName("click for paino note")
        self.piano_second_black_btn.setGeometry(100, 205, 35, 130)
        self.piano_second_black_btn.setStyleSheet("background-color:rgb(50,50,50);background-color: black;")
        self.piano_second_black_btn.clicked.connect(lambda: self.played_instrument_key(3, 261.63, 12))

        self.piano_fifth_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_fifth_btn.setObjectName("click for paino note")
        self.piano_fifth_btn.setGeometry(237, 205, 58, 194)
        self.piano_fifth_btn.setStyleSheet("background-color:rgb(226,226,226);background-color: white;")
        self.piano_fifth_btn.clicked.connect(lambda: self.played_instrument_key(7, 261.63, 12))

        self.piano_third_black_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_third_black_btn.setObjectName("click for paino note")
        self.piano_third_black_btn.setGeometry(220, 205, 35, 130)
        self.piano_third_black_btn.setStyleSheet("background-color:rgb(50,50,50);background-color: black;")
        self.piano_third_black_btn.clicked.connect(lambda: self.played_instrument_key(6, 261.63, 12))

        self.piano_sixth_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_sixth_btn.setObjectName("click for paino note")
        self.piano_sixth_btn.setGeometry(294, 205, 58, 194)
        self.piano_sixth_btn.setStyleSheet("background-color:rgb(226,226,226);background-color: white;")
        self.piano_sixth_btn.clicked.connect(lambda: self.played_instrument_key(9, 261.63, 12))

        self.piano_seventh_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_seventh_btn.setObjectName("click for paino note")
        self.piano_seventh_btn.setGeometry(351, 205, 58, 194)
        self.piano_seventh_btn.setStyleSheet(
            "background-color:rgb(226,226,226);background-color: white;text-align:bottom;")
        self.piano_seventh_btn.clicked.connect(lambda: self.played_instrument_key(11, 261.63, 12))

        self.piano_forth_black_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_forth_black_btn.setObjectName("click for paino note")
        self.piano_forth_black_btn.setGeometry(280, 205, 35, 130)
        self.piano_forth_black_btn.setStyleSheet("background-color:rgb(50,50,50);background-color: black;")
        self.piano_forth_black_btn.clicked.connect(lambda: self.played_instrument_key(8, 261.63, 12))

        self.piano_fifth_black_btn = QtWidgets.QPushButton(self.tab_2)
        self.piano_fifth_black_btn.setObjectName("click for paino note")
        self.piano_fifth_black_btn.setGeometry(345, 205, 35, 130)
        self.piano_fifth_black_btn.setStyleSheet("background-color:rgb(50,50,50);background-color: black;")
        self.piano_fifth_black_btn.clicked.connect(lambda: self.played_instrument_key(10, 261.63, 12))

        self.flute_image = QPixmap('pan_flute.png')
        self.label_flute = QtWidgets.QLabel(self.tab_2)
        self.label_flute.setPixmap(self.flute_image)
        self.label_flute.setObjectName("flute_label")
        self.label_flute.setGeometry(415, 199, 240, 200)
        # self.gridLayout_tab2.addWidget(self.label_flute,0,2,1,1)

        self.flute_far_left = QtWidgets.QPushButton(self.tab_2)
        self.flute_far_left.setObjectName("click for flute note")
        self.flute_far_left.setGeometry(482, 200, 16, 16)
        self.flute_far_left.setStyleSheet("QPushButton {background: transparent;border-radius: 8px; padding: 6px;\n"
                                          "}\n"
                                          "QPushButton:hover { background-color: #a27741;}"
                                          "QPushButton:pressed {background-color: #9c733f;}")
        self.flute_far_left.clicked.connect(lambda: self.played_instrument_key(6, 523.25, 6))

        self.second_tube = QtWidgets.QPushButton(self.tab_2)
        self.second_tube.setObjectName("click for flute note")
        self.second_tube.setGeometry(503, 205, 16, 16)
        self.second_tube.setStyleSheet("QPushButton {background: transparent;border-radius: 8px; padding: 6px;\n"
                                       "}\n"
                                       "QPushButton:hover { background-color: #a27741;}"
                                       "QPushButton:pressed {background-color: #9c733f;}")
        self.second_tube.clicked.connect(lambda: self.played_instrument_key(5, 523.25, 6))

        self.third_tube = QtWidgets.QPushButton(self.tab_2)
        self.third_tube.setObjectName("click for flute note")
        self.third_tube.setGeometry(524, 211, 16, 16)
        self.third_tube.setStyleSheet("QPushButton {background: transparent;border-radius: 8px; padding: 6px;\n"
                                      "}\n"
                                      "QPushButton:hover { background-color: #a27741;}"
                                      "QPushButton:pressed {background-color: #9c733f;}")
        self.third_tube.clicked.connect(lambda: self.played_instrument_key(4, 523.25, 6))

        self.forth_tube = QtWidgets.QPushButton(self.tab_2)
        self.forth_tube.setObjectName("click for flute note")
        self.forth_tube.setGeometry(546, 215, 18, 18)
        self.forth_tube.setStyleSheet("QPushButton {background: transparent;border-radius: 9px; padding: 6px;\n"
                                      "}\n"
                                      "QPushButton:hover { background-color: #a27741;}"
                                      "QPushButton:pressed {background-color: #9c733f;}")
        self.forth_tube.clicked.connect(lambda: self.played_instrument_key(3, 523.25, 6))

        self.fifth_tube = QtWidgets.QPushButton(self.tab_2)
        self.fifth_tube.setObjectName("click for flute note")
        self.fifth_tube.setGeometry(564, 220, 20, 20)
        self.fifth_tube.setStyleSheet("QPushButton {background: transparent;border-radius: 10px; padding: 6px;\n"
                                      "}\n"
                                      "QPushButton:hover { background-color: #a27741;}"
                                      "QPushButton:pressed {background-color: #9c733f;}")
        self.fifth_tube.clicked.connect(lambda: self.played_instrument_key(2, 523.25, 6))

        self.sixth_tube = QtWidgets.QPushButton(self.tab_2)
        self.sixth_tube.setObjectName("click for flute note")
        self.sixth_tube.setGeometry(591, 227, 22, 22)
        self.sixth_tube.setStyleSheet("QPushButton {background: transparent;border-radius: 11px; padding: 6px;\n"
                                      "}\n"
                                      "QPushButton:hover { background-color: #a27741;}"
                                      "QPushButton:pressed {background-color: #9c733f;}")
        self.sixth_tube.clicked.connect(lambda: self.played_instrument_key(1, 523.25, 6))

        self.far_right_tube = QtWidgets.QPushButton(self.tab_2)
        self.far_right_tube.setObjectName("click for flute note")
        self.far_right_tube.setGeometry(617, 235, 24, 24)
        self.far_right_tube.setStyleSheet("QPushButton {background: transparent;border-radius: 12px; padding: 6px;\n"
                                          "}\n"
                                          "QPushButton:hover { background-color: #a27741;}"
                                          "QPushButton:pressed {background-color: #9c733f;}")
        self.far_right_tube.clicked.connect(lambda: self.played_instrument_key(0, 523.25, 6))

        self.bells_image = QPixmap('belll_img.png')
        self.label_bells = QtWidgets.QLabel(self.tab_2)
        self.label_bells.setPixmap(self.bells_image)
        self.label_bells.setObjectName("bells_label")
        self.label_bells.setGeometry(690, 150, 500, 300)
        # self.gridLayout_tab2.addWidget(self.label_bells,0,3,1,1)

        self.bell_btn = QtWidgets.QPushButton(self.tab_2)
        self.bell_btn.setObjectName("click for flute note")
        self.bell_btn.setGeometry(783, 374, 30, 30)
        self.bell_btn.setStyleSheet("QPushButton {background: transparent ;border-radius: 15px; padding: 6px;\n"
                                    "}\n"
                                    "QPushButton:hover { background-color: rgb(212, 175, 55); }"
                                    "QPushButton:pressed {background-color: rgb(200, 170, 50);}")
        self.bell_btn.clicked.connect(lambda: self.bell())

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1090, 21))
        self.menubar.setObjectName("menubar")
        self.menufile = QtWidgets.QMenu(self.menubar)
        self.menufile.setObjectName("menufile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionopen = QtWidgets.QAction(MainWindow)
        self.actionopen.setObjectName("actionopen")
        self.menufile.addAction(self.actionopen)
        self.menubar.addAction(self.menufile.menuAction())

        self.actionopen.triggered.connect(lambda: self.open_audio_file())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.spec_displayed = 0
        self.stop = False
        self.toggle_PlayPause = 1


        self.threadpool = QtCore.QThreadPool()

        self.reference_plot = None
        self.q = queue.Queue(maxsize=20)

        self.device = 0
        self.window_length = 200
        self.downsample = 10
        self.channels = [1]
        self.interval = 30

        #device_info = sd.query_devices(self.device, 'input')
        device_info = sd.query_devices(self.device)
        self.samplerate = device_info['default_samplerate']
        length = int(self.window_length*self.samplerate/(1000*self.downsample))
        sd.default.samplerate = self.samplerate

        self.plotdata = np.zeros((length, len(self.channels)))

        self.update_plot()
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.interval)  # msec
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label_volume.setText(_translate("MainWindow", "Adjust Volume"))
        self.pushButton_play.setText(_translate("MainWindow", "Play"))
        self.pushButton_equalize.setText(_translate("MainWindow", "Equalize"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(
            self.tab), _translate("MainWindow", "Tab 1"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(
            self.tab_2), _translate("MainWindow", "Tab 2"))  
        
        self.settings_combobox_label.setText(_translate("MainWindow", "Instrument settings"))

        piano_shortcuts = {
            self.piano_far_left_btn: "z",
            self.piano_second_btn: "x",
            self.piano_third_btn: "c",
            self.piano_forth_btn: "v",
            self.piano_fifth_btn: "b",
            self.piano_sixth_btn: "n",
            self.piano_seventh_btn: "m",
            self.piano_far_left_black_btn: "s",
            self.piano_second_black_btn: "d",
            self.piano_third_black_btn: "g",
            self.piano_forth_black_btn: "h",
            self.piano_fifth_black_btn: "j",
        }

        for btn, chr in piano_shortcuts.items():
            btn.setShortcut(_translate("MainWindow", chr))

        self.menufile.setTitle(_translate("MainWindow", "file"))
        self.actionopen.setText(_translate("MainWindow", "open"))

    def equalize(self):

        # [bass , piano--- , altoSaxophone--- , guitar--- , flute, bell]
        freq_min = [0, 1000, 250, 2000, 262, 73]
        freq_max = [800, 2000, 900, 15000, 2092, 1172]


        Gains = []
        Gains.append(self.horizontalSlider_bass.value())
        Gains.append(self.horizontalSlider_piano.value())
        Gains.append(self.horizontalSlider_altoSaxophone.value())
        Gains.append(self.horizontalSlider_guitar.value())
        Gains.append(self.horizontalSlider_flute.value())
        Gains.append(self.horizontalSlider_bell.value())

        self.fs, self.data = wavfile.read(self.full_file_path)
        self.data = self.data / 2.0 ** 15
        N = len(self.data)

        rfft_coeff = np.fft.rfft(self.data)
        frequencies = np.fft.rfftfreq(N, 1. / self.fs)

        for i in range(6):
            for j in range(len(frequencies)):
                if frequencies[j] >= freq_min[i] and frequencies[j] <= freq_max[i]:
                    rfft_coeff[j] = rfft_coeff[j] * Gains[i]

        Equalized_signal = np.fft.irfft(rfft_coeff)
        scipy.io.wavfile.write('new.wav', self.fs, Equalized_signal)
        self.media.stop()
        self.playAudioFile('new.wav')

    def open_audio_file(self):
        self.full_file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, 'Open Song', QtCore.QDir.rootPath(), 'wav(*.wav)')
        self.playAudioFile(self.full_file_path)

    def playAudioFile(self, full_file_path):
        self.pushButton_play.setText("Pause")
        self.media = vlc.MediaPlayer(full_file_path)
        self.media.play()

        self.fs, self.data = wavfile.read(full_file_path)

        if self.spec_displayed == 0:
            self.empty_spec.hide()
            self.spec_Fig = Canvas_spec(self.data, self.fs)
            self.splitter_graphs.addWidget(self.spec_Fig)
            self.spec_displayed = 1
        else:
            self.spec_Fig.hide()
            self.spec_Fig = Canvas_spec(self.data, self.fs)
            self.splitter_graphs.addWidget(self.spec_Fig)

        worker = Worker(self.start_stream,)
        self.threadpool.start(worker)

    def start_stream(self):
        try:
            def audio_callback(indata, frames, time, status):
                self.q.put(indata[::self.downsample, [0]])
            stream = sd.InputStream(device=self.device, channels=max(
                self.channels), samplerate=self.samplerate, callback=audio_callback)
            with stream:
                input()
        except Exception as e:
            print("ERROR: ", e)

    def update_plot(self):
        try:
            data = [0]

            while True:
                try:
                    data = self.q.get_nowait()
                except queue.Empty:
                    break
                shift = len(data)
                self.plotdata = np.roll(self.plotdata, -shift, axis=0)
                self.plotdata[-shift:, :] = data
                self.ydata = self.plotdata[:]
                self.canvas.axes.set_facecolor((0, 0, 0))

                if self.reference_plot is None:
                    plot_refs = self.canvas.axes.plot(
                        self.ydata, color=(0, 1, 0.29))
                    self.reference_plot = plot_refs[0]
                else:
                    self.reference_plot.set_ydata(self.ydata)

            self.canvas.axes.yaxis.grid(True, linestyle='--')
            start, end = self.canvas.axes.get_ylim()
            self.canvas.axes.yaxis.set_ticks(np.arange(start, end, 0.1))
            self.canvas.axes.yaxis.set_major_formatter(
                ticker.FormatStrFormatter('%0.1f'))
            self.canvas.axes.set_ylim(ymin=-0.5, ymax=0.5)
            if self.stop == False:
                self.canvas.draw()
        except:
            pass

    def adjust_volume(self):
        value = int(self.verticalSlider_volume.value())
        self.media.audio_set_volume(value)

    def play_pause(self):
        if self.pushButton_play.text() != "Play":
            self.media.pause()
            self.pushButton_play.setText("Play")
        else :
            self.pushButton_play.setText("Pause")
            self.media.play()     

    '''self.toggle_PlayPause = self.toggle_PlayPause ^ 1
        self.stop = self.stop ^ 1

        if self.toggle_PlayPause == 1:
            self.media.play()
        else:
            self.media.pause()'''

    def get_wave(self, freq, duration=0.5):
        amplitude = 4096
        self.sample_rate = 44100  # Hz
        time = np.linspace(0, duration, int(sample_rate * duration))
        wave = amplitude * np.sin(2 * np.pi * freq * time)
        return wave

    def get_instrument_notes(self, base_freq, denominator):
        note_freq = {octave[note_index]: base_freq * pow(self.piano_mode, (note_index / denominator)) for note_index in
                     range(len(octave))}
        note_freq[''] = 0.0  # silent freq
        return note_freq

    def played_instrument_key(self, key_index, base_freq, den):
        notesFreqs = self.get_instrument_notes(base_freq, den)
        sound = octave[key_index]
        song = [self.get_wave(notesFreqs[note]) for note in sound.split('-')]
        song = np.concatenate(song)
        data = song.astype(np.int16)
        data=self.amplifying_wave(data)
        sa.play_buffer(data, 1, 2, sample_rate)

    def get_flute_notes(self, length):
        base_freq = 294  # the note of C4
        note_freq = {octave[note_index]: 340 / (4 * length) for note_index in range(len(octave))}
        note_freq[''] = 0.0  # silent freq
        return note_freq

    def amplifying_wave(self,data):
        data = data * (16300/np.max(data))  # amplifying the wave
        data = data.astype(np.int16)
        return data

    def piano_mode_picker(self):
        self.piano_mode=self.piano_modes.get(self.piano_settings_combobox.currentIndex())

    def bell(self):
        beepy.beep(sound="ping")



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
