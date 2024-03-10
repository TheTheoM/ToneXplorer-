from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QSpinBox, QHBoxLayout, QLabel, QRadioButton
import pyqtgraph     as pg
import numpy         as np
import sounddevice   as sd
from scipy.fft       import fft
from scipy.signal    import medfilt, chirp
import asyncio, sys, time

class noneScientificAxis(pg.AxisItem):
    def logTickStrings(self, values, scale, spacing):
        formatted_values = []
        for v in values:
            formatted_values.append(f'{10 ** v:g}'.replace(' ', ''))
        return formatted_values

class SpectrogramApp(QWidget):
    def __init__(self):
        super().__init__()
        self.start_freq, self.end_freq = 20, 20000
        self.duration = 5
        self.sample_freq = 44100
        self.smoothen_Window_Size = 15
        self.frequencies = np.zeros(0)
        self.rfft_result = np.zeros(0)
        self.eq_band_value = 15
        self.init_ui()
        self.target_curve = np.array([0, 0, 0, 0, 0])

    def init_ui(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Spectrogram App')
        dark_mode_stylesheet = """
            QWidget {
                background-color: #2E2E2E;
                color: #FFFFFF;
            }
            QSpinBox, QPushButton {
                background-color: #404040;
                color: #FFFFFF;
                border: 1px solid #707070;
            }
            QHBoxLayout{
                background-color: #404040;
            }

        """
        self.setStyleSheet(dark_mode_stylesheet)
        layout = QVBoxLayout(self)
        axis = {}
        for ori in ['top', 'bottom', 'left', 'right']: 
            axis[ori] = noneScientificAxis(orientation=ori)
        self.plot_widget = pg.PlotWidget(axisItems=axis)
        self.plot_widget.setTitle('Frequency Range')
        self.plot_widget.setLabel('bottom', 'Frequency (Hz)')
        self.plot_widget.setLabel('left', 'Amplitude (dB)')
        self.plot_widget.setBackground('#2E2E2E')
        layout.addWidget(self.plot_widget)
        spinbox_layout = QHBoxLayout()

        # Start Frequency Layout
        start_freq_layout = QVBoxLayout()
        start_freq_label = QLabel("Start Freq:")
        start_freq_layout.addWidget(start_freq_label)
        self.lower_freq_spinbox = QSpinBox()
        self.lower_freq_spinbox.setRange(1, 100000)
        self.lower_freq_spinbox.setValue(self.start_freq)
        start_freq_layout.addWidget(self.lower_freq_spinbox)

        # End Frequency Layout
        end_freq_layout = QVBoxLayout()
        end_freq_label = QLabel("End Freq:")
        end_freq_layout.addWidget(end_freq_label)
        self.upper_freq_spinbox = QSpinBox()
        self.upper_freq_spinbox.setRange(2, 100000)
        self.upper_freq_spinbox.setValue(self.end_freq)
        end_freq_layout.addWidget(self.upper_freq_spinbox)


        # Smoothing Window Size
        smooth_graph_layout = QVBoxLayout()
        smooth_graph_value = QLabel("Smoothing Value")
        smooth_graph_layout.addWidget(smooth_graph_value)
        self.smoothen_Window_Size_Spinbox = QSpinBox(self)
        self.smoothen_Window_Size_Spinbox.setRange(0, 10000)
        self.smoothen_Window_Size_Spinbox.setValue(self.smoothen_Window_Size)
        self.smoothen_Window_Size_Spinbox.valueChanged.connect(self.display_spectrum)
        smooth_graph_layout.addWidget(self.smoothen_Window_Size_Spinbox)


        # Add Start and End Frequency Layouts to the main layout
        spinbox_layout.addLayout(start_freq_layout)
        spinbox_layout.addLayout(end_freq_layout)
        spinbox_layout.addLayout(smooth_graph_layout)

        self.radio_5 = QRadioButton("5 Bands")
        self.radio_7 = QRadioButton("7 Bands")
        self.radio_15 = QRadioButton("15 Bands")
        self.radio_15.setChecked(True)
        self.radio_31 = QRadioButton("31 Bands")

        self.radio_5.clicked.connect(self.radio_button_clicked)
        self.radio_7.clicked.connect(self.radio_button_clicked)
        self.radio_15.clicked.connect(self.radio_button_clicked)
        self.radio_31.clicked.connect(self.radio_button_clicked)

        eq_bands_V_Box = QVBoxLayout()
        Eq_Bands_label = QLabel("Outputted Corrected Eq Bands")
        eq_bands_V_Box.addWidget(Eq_Bands_label)

        # Create a widget to hold the radio buttons layout
        eq_band_widget = QWidget()
        eq_band_layout = QHBoxLayout(eq_band_widget)
        eq_band_layout.addWidget(self.radio_5)
        eq_band_layout.addWidget(self.radio_7)
        eq_band_layout.addWidget(self.radio_15)
        eq_band_layout.addWidget(self.radio_31)
        eq_band_layout.setContentsMargins(0, 0, 0, 0)

        # Add the widget containing radio buttons layout to the main layout
        eq_bands_V_Box.addWidget(eq_band_widget)

        spinbox_layout.addLayout(eq_bands_V_Box)
        layout.addLayout(spinbox_layout)

        self.button = QPushButton('Play and Plot Spectrum', self)
        self.button.clicked.connect(self.play_and_plot)
        layout.addWidget(self.button)

        self.setLayout(layout)
        
    def radio_button_clicked(self):
        sender = self.sender()
        if sender.isChecked():
            self.eq_band_value = int(sender.text().replace(" Bands", "")) #"7 Bands" => 7
            print("Checked Value:", self.eq_band_value)

    def frequency_sweep(self, start_freq, stop_freq, sweep_time, sample_rate):
        t = np.linspace(0, sweep_time, int(sample_rate * sweep_time))
        sweep = chirp(t, f0=start_freq, f1=stop_freq, t1=sweep_time, method='logarithmic')
        return sweep
        

    def smooth_it(self, data, window_size):
        """Smooths magnitude_db"""
        if window_size % 2 == 0:
            raise ValueError("Window size should be an odd number.")
            
        data_padded = np.pad(data, (window_size // 2, window_size // 2), mode='edge')
        return  np.convolve(data_padded, np.ones(window_size)/window_size, mode='valid')

    def calculate_frequency_response(self, signal, sample_rate, start_freq, end_freq):
        fft_result = np.fft.fft(signal)
        frequencies = np.fft.fftfreq(len(fft_result), d=1/sample_rate)
        magnitude_db = 20 * np.log10(np.abs(fft_result))

        # Plot the magnitude spectrum in dB within the specified frequency range
        mask = (frequencies >= start_freq) & (frequencies <= end_freq)
        return frequencies[mask], magnitude_db[mask]
        
    def play_and_plot(self):
        self.start_freq = self.lower_freq_spinbox.value()
        self.end_freq   = self.upper_freq_spinbox.value()
        linear_sweep_wave = self.frequency_sweep(self.start_freq, self.end_freq, self.duration, self.sample_freq)
        # linear_sweep_wave = np.zeros(int(self.duration * self.sample_freq))
        recorded_signal = sd.playrec(linear_sweep_wave, samplerate=self.sample_freq, channels=1, blocking=True).flatten()

        self.start_freq, self.end_freq = self.lower_freq_spinbox.value(), self.upper_freq_spinbox.value() 

        self.frequencies, self.rfft_result = self.calculate_frequency_response(recorded_signal,  self.sample_freq, self.start_freq, self.end_freq)
        self.display_spectrum()
        
    def display_spectrum(self):
        if len(self.rfft_result) == 0 or len(self.frequencies) == 0:
            return False
        
        self.start_freq = self.lower_freq_spinbox.value()
        self.end_freq   = self.upper_freq_spinbox.value()
        window_size     = 2 * self.smoothen_Window_Size_Spinbox.value() + 1 #Ensure its always an odd number. Otherwise it'll crash. 'ValueError: Each element of kernel_size should be odd.'

        if window_size > 0: 
            plot_Data = self.smooth_it(self.rfft_result, window_size)
        else:
            plot_Data = self.rfft_result

        self.plot_widget.clear()
        plot_item = self.plot_widget.getPlotItem()
        plot_item.setLogMode(x=True) 

        plot_item.plot(self.frequencies, plot_Data, pen=(0, 200, 50), stepMode='right')  # Plot using original frequencies
        plot_item.setTitle('Frequency Range')
        plot_item.setLabel('bottom', 'Frequency (Hz)')
        plot_item.setLabel('left', 'Amplitude (dB)')
        targetLevel = round(np.mean(plot_Data[0:4000]), 2)  # Lower and Mid Freqs
        interpolated_target_curve = np.interp(plot_Data, np.arange(len(self.target_curve)), self.target_curve)
        centered_interpolated_target_curve = interpolated_target_curve - np.mean(interpolated_target_curve) + targetLevel         # Centering the interpolated_target_curve around the targetLevel
        plot_item.plot(self.frequencies, interpolated_target_curve, pen=(0, 10, 50), stepMode='right')  # Plot using original frequencies
        avgDbBans, eqString = self.generate_eq_settings(self.start_freq, self.end_freq, self.frequencies, plot_Data, targetLevel)
        
        print(eqString)


    def get_eq_bands(self, numBands):
        match int(numBands):
            case 5:
                return {60: 0, 230: 0, 910: 0, 3600: 0, 14000: 0}
            case 7:
                return {64: 0, 160: 0, 400: 0, 1000: 0, 2500: 0, 6300: 0, 16000: 0}
            case 15:
                return {25: 0, 40: 0, 63: 0, 100: 0, 160: 0, 250: 0, 400: 0, 630: 0,
                    1000: 0, 1600: 0, 2500: 0, 4000: 0, 6300: 0, 10000: 0, 16000: 0}
            case 31:
                return {20: 0, 25: 0, 32: 0, 40: 0, 50: 0, 63: 0, 80: 0, 100: 0,
                    125: 0, 160: 0, 200: 0, 250: 0, 315: 0, 400: 0, 500: 0, 630: 0,
                    800: 0, 1000: 0, 1250: 0, 1600: 0, 2000: 0, 2500: 0, 3150: 0,
                    4000: 0, 5000: 0, 6300: 0, 8000: 0, 10000: 0, 12500: 0, 16000: 0, 20000: 0}
        

 


    def generate_eq_settings(self, start_freq, end_freq, measured_frequencies, measured_magnitude_db, targetLevel):
        eqBands = self.get_eq_bands(self.eq_band_value)
        interpolated_target_curve = np.interp(measured_frequencies, np.arange(len(self.target_curve)), self.target_curve)
        gain_adjustments = interpolated_target_curve - measured_magnitude_db
        fromFreq = 0
        threshold = 4        
        avgDbBans = []
        eqString = ""
        maxGain = 8
        print(f"Calculated Target level at {targetLevel}")
        for toFreq in eqBands.keys():
            if 0 <= fromFreq < len(measured_magnitude_db) and 0 <= toFreq < len(measured_magnitude_db):
                avg_Db = np.mean(measured_magnitude_db[fromFreq:toFreq])
                gain = round(targetLevel - avg_Db, 2)
                if gain > maxGain: gain = maxGain
                avgDbBans.append({toFreq: {gain}})
                eqString += (f"{toFreq} {gain}; ")
            else:
                eqString += f"{toFreq} {0}; "
            
            fromFreq = toFreq
        return avgDbBans, '# GraphicEQ: ' + eqString.strip()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SpectrogramApp()
    ex.show()
    sys.exit(app.exec())
