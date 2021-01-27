import numpy as np

from PyQt5.QtCore import QSettings, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget

from .Gui.fourierwidget import Ui_fouriergui

from .fourierfilter import filter_type_map


prefix_map = {
    'Hz': 1.0,
    'kHz': 1e3,
    'MHz': 1e6,
    'GHz': 1e9
}


# todo: add support for multiple Fourier Filters
# todo: real high-order filters require more than 2 parameters, this interface does not support it.
class FourierGui(QWidget, Ui_fouriergui):
    """
    Implements GUI and logic for Fourier analysis window
    """
    def __init__(self):
        super(FourierGui, self).__init__()

        # setup the UI code
        self.setupUi(self)
        self.read_settings()

        # populate the filter types combo list
        for tp in filter_type_map.keys():
            self.filter_selection_box.addItem(tp)

        # populate the unit SI prefix combo list
        for prefix in prefix_map:
            self.filter_cFreq_prefix.addItem(prefix)
            self.filter_BW_prefix.addItem(prefix)

        # the filter is initialized by self._filter_changed function
        self._fourier_filter = None

        # signals from FourierFilter widgets
        self.filter_selection_box.activated.connect(self._filter_changed)
        self.filter_cFreq_line.editingFinished.connect(self._filter_changed)
        self.filter_cFreq_prefix.activated.connect(self._filter_changed)
        self.filter_BW_line.editingFinished.connect(self._filter_changed)
        self.filter_BW_prefix.activated.connect(self._filter_changed)

    ####################
    # CLIENT INTERFACE #
    ####################
    def process(self, xdata, ydata):
        """
        Plots data over 3 plots: 1st the raw data only, 2nd the FFT, 3rd the filtered anti-transform.
        """
        # plot data (no modifications) on 1st scroll plot
        self.scrollplot_data.plot(xdata, ydata)
        # compute fft and plot on Bodeplot
        yfft = np.fft.rfft(ydata)

        observation_time = abs(xdata[0] - xdata[-1])
        xfft = np.mgrid[0:yfft.shape[0]] / observation_time

        # remove DC value if needed
        if not self.dc_show_box.isChecked():
            yfft = yfft[1:]
            xfft = xfft[1:]

        # normalize
        yfft /= yfft.max()
        # plot
        self.bodeplot_fft.plot_fft(xfft, yfft)

        # filter the fft and anti-transform
        if self._fourier_filter:
            filtered_fft = self._fourier_filter.filter(xfft, yfft)
            filtered_signal = np.fft.irfft(filtered_fft)
            minlen = min(xdata.shape[0], filtered_signal.shape[0])
            self.scrollplot_ifft.plot(xdata[:minlen], filtered_signal[:minlen])

    def set_display_time(self, value):
        self.scrollplot_data.display_time = value
        self.scrollplot_ifft.display_time = value

    #############
    # INTERNALS #
    #############
    @pyqtSlot()
    def _filter_changed(self):
        """
        Creates a new FourierFilter object based on user selection.
        This is run every time the user makes a change in the parameters.
        """
        # select type
        type = filter_type_map[self.filter_selection_box.currentText()]
        # center frequency
        cFreq = float(self.filter_cFreq_line.value())
        cFreq *= prefix_map[self.filter_cFreq_prefix.currentText()]
        # bandwidth
        BW = float(self.filter_BW_line.value())
        BW *= prefix_map[self.filter_BW_prefix.currentText()]
        # call object constructor
        self._fourier_filter = type(cFreq, BW)

        # update the plot so as to show the filter Bode response
        if self.bodeplot_fft.fft_curve:
            xx = self.bodeplot_fft.fft_curve.xData
            yy = np.ones_like(xx)
            self.bodeplot_fft.plot(xx, self._fourier_filter.filter(xx, yy))



    ########################
    # SETTINGS AND CLOSING #
    ########################
    def save_settings(self):
        settings = QSettings('BaLi', 'PhotonCounter')
        settings.setValue('FFTgeometry', self.saveGeometry())
        settings.setValue('FFTsplitter/geometry', self.splitter.saveGeometry())
        settings.setValue('FFTsplitter/state', self.splitter.saveState())

    def read_settings(self):
        settings = QSettings('BaLi', 'PhotonCounter')
        try:
            self.restoreGeometry(settings.value("FFTgeometry"))
            self.splitter.restoreGeometry(settings.value("FFTsplitter/geometry"))
            self.splitter.restoreState(settings.value("FFTsplitter/state"))
        except TypeError:
            pass

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)