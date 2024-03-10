# ToneXplorer-
 Pure Python application that measurs and visualizes speaker frequency response, generating equalization bands to align with a specified target curve.

## Installation

You can install the required dependencies using the following command:

```bash
pip install PyQt6 pyqtgraph numpy sounddevice scipy
```


# Usage:
```bash
python ToneXplorer.py
```

Select the Start and End frequency you wish to test your device through and press "Play and Plot Spectrum"
![image](https://github.com/TheTheoM/ToneXplorer-/assets/103237702/12671b71-165c-4b33-ad13-6ee7350faa57)

You can smoothed the graph through the Smoothing Value Input. This also impacts the curve that is eq'd against a flat curve.

![image](https://github.com/TheTheoM/ToneXplorer-/assets/103237702/17207ffa-f986-48d1-ad28-71592ef4efb6)

The Outputed EQ Bands are printed to the console, to change the eq-bands, select one of the 5 bands on the right, and click play and plot Spectrum.

![image](https://github.com/TheTheoM/ToneXplorer-/assets/103237702/9ff691e0-597b-4f7f-a3e9-cb3033825c37)

Example EQ-Bands Output. This is in the format accepted via Equaliser APO.
```
# GraphicEQ: 25 5.0; 40 -7.41; 63 -11.07; 100 -9.66; 160 -8.02; 250 -10.0; 400 -6.76; 630 -5.9; 1000 -8.75; 1600 -2.73; 2500 2.61; 4000 4.58; 6300 8; 10000 8; 16000 8;
```

## Future To-Do List:
   - Display the correction EQ-bands on the GUI with a copy-to-clipboard option.
   - Display the target curve and add options to change it.
   - Output Parametric EQ curves.
   - Improve the eq-correction logic to using an optimization and target function instead of using the magnitude difference between the measured and target curve as the gain for the eq curves.
   - Add Automatic Testing with Feedback, which measures the curve, applies a correction, than measures the correction and optimizes untill within a flatness target threshold.
   - Add better labeling to the x-axis of the graph, such that minor-ticks are labelled and endpoints.  
