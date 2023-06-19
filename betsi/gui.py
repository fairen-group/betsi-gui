# basics
import os

from PyQt5 import QtCore
from PyQt5 import QtGui
# qt gui framework
from PyQt5.QtWidgets import *
# matplotlib for plotting
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import logging
import sys

import traceback

# core lib
plt.ion()
from betsi.lib import *
from betsi.plotting import *


class BETSI_gui(QMainWindow):
    """Defines the main window of the BETSI gui and adds all the toolbars.
    The main widget is the BETSI_widget"""

    def __init__(self):
        super().__init__()

        self.title = 'BETSI'
        self.setWindowTitle(self.title)

        # define the menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        toolsMenu = menubar.addMenu('&Tools')

        # option for importing a single file.
        importfile_menu = fileMenu.addAction('&Import File')
        importfile_menu.setShortcut("Ctrl+I")
        importfile_menu.triggered.connect(self.import_file)

        # option for changing the root output directory.
        outputdir_menu = fileMenu.addAction('&Set Output Directory')
        outputdir_menu.setShortcut("Ctrl+O")
        outputdir_menu.triggered.connect(self.set_output_dir)

        # option for running on a chosen directory.
        directoryrun_menu = fileMenu.addAction('&Analyse Directory')
        directoryrun_menu.setShortcut("Ctrl+D")
        directoryrun_menu.triggered.connect(self.analyse_dir)

        # option for clearing the memory and resetting to defaults
        clear_menu = toolsMenu.addAction('&Clear')
        clear_menu.setShortcut("Ctrl+C")
        clear_menu.triggered.connect(self.clear)

        # option for replotting
        replot_menu = toolsMenu.addAction('&Replot')
        replot_menu.triggered.connect(self.replot_betsi)

        self.betsimagic_menu_action = QAction(
            'BETSI Magic', self, checkable=True)
        self.betsimagic_menu_action.setStatusTip(
            "Resets the settings to default values and performs BETSI calculation")
        self.betsimagic_menu_action.setChecked(False)
        self.betsimagic_menu_action.triggered.connect(self.trigger_betsimagic)

        betsimagic_menu = toolsMenu.addAction(self.betsimagic_menu_action)

        # define the widget
        self.betsi_widget = BETSI_widget(self)
        self.setCentralWidget(self.betsi_widget)

        # enable drag and drop
        self.setAcceptDrops(True)

    def set_output_dir(self):
        self.betsi_widget.set_output_dir()

    def analyse_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, 'Select Directory', os.getcwd())
        print(f'Imported directory: {Path(dir_path).name}')
        self.betsi_widget.analyse_directory(dir_path)
        
        
    def import_file(self):
        ## file_path = QFileDialog.getOpenFileName(
        ##     self, 'Select File', os.getcwd(), '*.csv')[0]
        file_path = QFileDialog.getOpenFileName(
            self, 'Select File', os.getcwd(), "*.csv *.aif *.txt *.XLS")[0]
        self.betsi_widget.target_filepath = file_path
        self.betsi_widget.populate_table(csv_path=file_path)
        print(f'Imported file: {Path(file_path).name}')

    def dragEnterEvent(self, e):
        data = e.mimeData()
        urls = data.urls()
        drag_type = [u.scheme() for u in urls]
        paths = [u.toLocalFile() for u in urls]
        extensions = [os.path.splitext(p)[-1] for p in paths]
        # accept files only for now.
        
        ##if all(dt == 'file' for dt in drag_type) and all(ext == '.csv' for ext in extensions):
        if all(dt == 'file' for dt in drag_type) and all(ext in ['.csv', '.aif', '.txt', '.XLS'] for ext in extensions):
            e.accept()
        elif len(drag_type) == 1 and os.path.isdir(paths[0]):
            e.ignore()
        else:
            e.ignore()

    def dropEvent(self, e):
        data = e.mimeData()
        urls = data.urls()
        paths = [u.toLocalFile() for u in urls]

        # Single path to csv file
        
        ##if len(paths) == 1 and Path(paths[0]).suffix == '.csv':
        if len(paths) == 1 and Path(paths[0]).suffix in ['.csv', '.aif', '.txt', '.XLS']:
            self.betsi_widget.target_filepath = paths[0]
            self.betsi_widget.populate_table(csv_path=paths[0])
            print(f'Imported file: {Path(paths[0]).name}')
            
            self.betsi_widget.bet_object = None
            self.betsi_widget.bet_filter_result = None
            
            self.betsi_widget.run_calculation()

    def clear(self):
        self.betsi_widget.clear()

    def replot_betsi(self):
        self.betsi_widget.display_plot = True
        self.betsi_widget.run_calculation()

    def trigger_betsimagic(self, state):
        if state:
            self.betsi_widget.set_defaults()
        self.betsi_widget.set_editable(not state)

    def closeEvent(self, evt):
        print('Closing')
        try:
            plt.close(self.bet_widget.current_fig)
            plt.close(self.bet_widget.current_fig_2)
        except:
            pass


class BETSI_widget(QWidget):
    """Widget containing all the options for running the BETSI analysis and display of the data.

    Args:
        parent: QMainWindow the widget belongs to

    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # basic properties
        self.output_dir = os.getcwd()
        self.current_fig = None
        self.current_fig_2 = None

        self.target_filepath = None
        self.bet_object = None
        self.bet_filter_result = None

        # Create label boxes to display info
        self.current_output_label = QLabel()
        self.current_targetpath_label = QLabel()

        self.current_output_label.setText(
            f"Output Directory: {self.output_dir}")
        self.current_targetpath_label.setText(
            f"Loaded File: {self.target_filepath}")
        self.current_output_label.setFont(QtGui.QFont("Times", 10))
        self.current_targetpath_label.setFont(QtGui.QFont("Times", 10))
        
        self.current_output_label.setWordWrap(True)
        self.current_output_label.setAlignment(QtCore.Qt.AlignLeft)
        #self.current_output_label.setStyleSheet("background-color: lightgreen")
        self.current_targetpath_label.setWordWrap(True)
        self.current_targetpath_label.setAlignment(QtCore.Qt.AlignLeft)
        #self.current_targetpath_label.setStyleSheet("background-color: lightblue")

        # add a group box containing controls
        self.criteria_box = QGroupBox("BET area selection criteria")
        self.criteria_box.setMaximumWidth(700)
        self.criteria_box.setMaximumHeight(1000)
        self.criteria_box.setMinimumWidth(500)
        #self.criteria_box.setMinimumHeight(650)
        self.min_points_label = QLabel(self.criteria_box)
        self.min_points_label.setText('Minimum number of points in the linear region: [3,10]')
        self.min_points_edit = QLineEdit()
        self.min_points_edit.setMaximumWidth(75)
        self.min_points_slider = QSlider(QtCore.Qt.Horizontal)
        self.minr2_label = QLabel('Minimum R<sup>2</sup>: [0.8,0.999]')
        self.minr2_edit = QLineEdit()
        self.minr2_edit.setMaximumWidth(75)
        self.minr2_slider = QSlider(QtCore.Qt.Horizontal)
        self.rouq1_tick = QCheckBox("Rouquerol criterion 1: Monotonic")
        self.rouq2_tick = QCheckBox("Rouquerol criterion 2: Positive C")
        self.rouq3_tick = QCheckBox("Rouquerol criterion 3: Pressure in linear range")
        self.rouq4_tick = QCheckBox("Rouquerol criterion 4: Error in %, [5,75]")
        self.rouq5_tick = QCheckBox("BETSI criterion: End at the knee")
        self.rouq4_edit = QLineEdit()
        self.rouq4_edit.setMaximumWidth(75)
        self.rouq4_slider = QSlider(QtCore.Qt.Horizontal)
        
        self.adsorbate_label = QLabel('Adsorbate:')
        self.adsorbate_combo_box = QComboBox()
        self.adsorbate_combo_box.addItems(["N2", "Ar", "Kr", "Xe", "Custom"])
        self.adsorbate_cross_section_label = QLabel('Cross sectional area (nm<sup>2</sup>):')
        self.adsorbate_cross_section_edit = QLineEdit()
        self.adsorbate_cross_section_edit.setMaximumWidth(75)
        self.adsorbate_molar_volume_label = QLabel('Molar volume (mol/m<sup>3</sup>):')
        self.adsorbate_molar_volume_edit = QLineEdit()
        self.adsorbate_molar_volume_edit.setMaximumWidth(75)
        self.note_label = QLabel(
            """Hints:
   - For convenience, it is best to first set your desired criteria before importing the input file.
   - Drag and drop the input file into the BETSI window.
   - Valid input file formats: 
     # Adsorption Information File: *.aif
     # Two-column data files: *.csv, *.txt
     # Micromeritics: *.XLS
   - Valid value range for parameters are given in brackets "[ ]"
   - Make sure to read the warnings that may pop up after BET calculation.  
   - After the first run, by modifiying any of the parameters above, the calculations will rerun automatically.
   - Regarding the minimum number of points, Rouquerol suggested 10 points, but you can lower the number if the data has insufficient number of points.
   - Units: "Relative pressure" is dimensionless and "Quantity adsorbed" is in (cm\u00B3 STP/g).
   - When the calculation is done, by clicking on any points on the "Filtered BET Areas" plot, all the plots will change to the corresponding selected points range.
   - If the calculation takes longer than expected, bear with it. In case you see "Not responding", it means it is still running, otherwise the software would crash.
   """)
        self.note_label.setStyleSheet("background-color: lightblue")
        self.note_label.setMargin(10)
        #self.note_label.setIndent(10)
        self.note_label.setWordWrap(True)
        self.note_label.setAlignment(QtCore.Qt.AlignLeft)
        
        
        self.export_button = QPushButton('Export Results')
        self.export_button.pressed.connect(self.export)

        # any change in states updates the display.
        self.rouq1_tick.stateChanged.connect(self.maybe_run_calculation)
        self.rouq2_tick.stateChanged.connect(self.maybe_run_calculation)
        self.rouq3_tick.stateChanged.connect(self.maybe_run_calculation)
        self.rouq4_tick.stateChanged.connect(self.maybe_run_calculation)
        self.rouq5_tick.stateChanged.connect(self.maybe_run_calculation)

        # define widget parameters
        self.rouq4_slider.setRange(5, 75)
        self.minr2_slider.setRange(800, 999)
        self.min_points_slider.setRange(3, 10)

        # set the defaults
        self.set_defaults()
        
        # connect the actions
        self.minr2_edit.editingFinished.connect(self.minr2_edit_changed)
        ##self.minr2_edit.returnPressed.connect(self.minr2_edit_changed)
        self.rouq4_edit.editingFinished.connect(self.rouq4_edit_changed)
        ##self.rouq4_edit.returnPressed.connect(self.rouq4_edit_changed)
        self.min_points_edit.editingFinished.connect(
            self.min_points_edit_changed)
        ##self.min_points_edit.returnPressed.connect(
        ##    self.min_points_edit_changed)
        ##self.rouq4_slider.valueChanged.connect(self.rouq4_slider_changed)
        ##self.minr2_slider.valueChanged.connect(self.minr2_slider_changed)
        ##self.min_points_slider.valueChanged.connect(
        ##    self.min_points_slider_changed)

        
        self.adsorbate_combo_box.activated.connect(self.adsorbate_combo_box_changed)
        ##self.adsorbate_cross_section_edit.returnPressed.connect(self.adsorbate_related_edit_changed)
        self.adsorbate_cross_section_edit.editingFinished.connect(self.adsorbate_related_edit_changed)
        
        self.adsorbate_molar_volume_edit.editingFinished.connect(self.adsorbate_related_edit_changed)
        ##self.adsorbate_molar_volume_edit.returnPressed.connect(self.adsorbate_related_edit_changed)


        ##self.minr2_edit.editingFinished.connect(self.line_edit_changed)
        ##self.rouq4_edit.editingFinished.connect(self.line_edit_changed)
        ##self.min_points_edit.editingFinished.connect(
        ##    self.line_edit_changed)
        ##self.adsorbate_cross_section_edit.editingFinished.connect(self.line_edit_changed)
        ##self.adsorbate_molar_volume_edit.editingFinished.connect(self.line_edit_changed)


        # add the table for results
        self.results_table = QTableWidget(self)
        self.results_table.setFixedWidth(520)
        self.clean_table()

        # create layout
        criteria_layout = QGridLayout()
        criteria_layout.addWidget(
            self.min_points_label, criteria_layout.rowCount(), 1, 1, 1)
        criteria_layout.addWidget(
            self.min_points_edit, criteria_layout.rowCount() - 1, 2)
        ##criteria_layout.addWidget(
        ##    self.min_points_slider, criteria_layout.rowCount(), 1, 1, 2)
        criteria_layout.addWidget(
            self.minr2_label, criteria_layout.rowCount(), 1)
        criteria_layout.addWidget(
            self.minr2_edit, criteria_layout.rowCount() - 1, 2)
        ##criteria_layout.addWidget(
        ##    self.minr2_slider, criteria_layout.rowCount(), 1, 1, 2)
        criteria_layout.addWidget(
            self.rouq1_tick, criteria_layout.rowCount(), 1)
        criteria_layout.addWidget(
            self.rouq2_tick, criteria_layout.rowCount(), 1)
        criteria_layout.addWidget(
            self.rouq3_tick, criteria_layout.rowCount(), 1)
        criteria_layout.addWidget(
            self.rouq4_tick, criteria_layout.rowCount(), 1)
        criteria_layout.addWidget(
            self.rouq4_edit, criteria_layout.rowCount() - 1, 2)
        ##criteria_layout.addWidget(
        ##    self.rouq4_slider, criteria_layout.rowCount(), 1, 1, 2)
        criteria_layout.addWidget(
            self.rouq5_tick, criteria_layout.rowCount(), 1)
        
        criteria_layout.addWidget(
            self.adsorbate_label, criteria_layout.rowCount(), 1)
        criteria_layout.addWidget(
            self.adsorbate_combo_box, criteria_layout.rowCount() - 1, 2)
        criteria_layout.addWidget(
            self.adsorbate_cross_section_label, criteria_layout.rowCount(), 1)
        criteria_layout.addWidget(
            self.adsorbate_cross_section_edit, criteria_layout.rowCount() - 1, 2)
        criteria_layout.addWidget(
            self.adsorbate_molar_volume_label, criteria_layout.rowCount(), 1)
        criteria_layout.addWidget(
            self.adsorbate_molar_volume_edit, criteria_layout.rowCount() - 1, 2)
        
        criteria_layout.addWidget(
            self.note_label, criteria_layout.rowCount(), 1, 1, 2)
        
        criteria_layout.addWidget(
            self.export_button, criteria_layout.rowCount(), 1, 1, 2)

        # criteria_layout.addWidget(
        #     self.current_output_label, criteria_layout.rowCount(), 1, 1, 1)
        # criteria_layout.addWidget(
        #     self.current_targetpath_label, criteria_layout.rowCount(), 1, 1, 1)
        criteria_layout.addWidget(
            self.current_output_label, criteria_layout.rowCount(), 1, 1, 2)
        criteria_layout.addWidget(
            self.current_targetpath_label, criteria_layout.rowCount(), 1, 1, 2)
        
        

        criteria_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), criteria_layout.rowCount() + 1, 1)
        self.criteria_box.setLayout(criteria_layout)

        main_layout = QGridLayout()
        main_layout.addWidget(self.criteria_box, 1, 1)
        main_layout.addWidget(self.results_table, 1, 2)

        self.setLayout(main_layout)

    def set_output_dir(self):
        """Defines the output directory of the BETSI analysis"""
        dir_path = QFileDialog.getExistingDirectory(
            self, 'Select Output Directory', os.getcwd())
        print(f"Output directory set to {dir_path}")
        self.output_dir = dir_path
        self.current_output_label.setText(
            f"Output Directory: {self.output_dir}")

    def maybe_run_calculation(self):
        self.check_rouq_compatibility()
        
        self.check_adsorbate_compatibility()
        ##if self.target_filepath is not None:
        if self.target_filepath is not None:
            if self.adsorbate_combo_box.currentText() != "Custom":
                self.run_calculation()
            elif float(self.adsorbate_cross_section_edit.text()) > 0 and float(self.adsorbate_molar_volume_edit.text()) > 0:
                self.run_calculation()

    def plot_bet(self):
        # if plt.get_fignums() != [1, 2]:
        #     plt.close('all')
        plt.close('all')
        if self.current_fig is not None:
            self.current_fig.clear()
            self.current_fig_2.clear()
        try:
            # check if the figure has been closed, if it doesn't reset it to none and replot
            if self.current_fig is not None and not plt.fignum_exists(self.current_fig.number):
                self.current_fig = None
                self.current_fig_2 = None

            # Initialize plots
            with matplotlib.rc_context({'interactive': self.display_plot}):
                fig = create_matrix_plot(self.bet_filter_result, self.rouq3_tick.isChecked(), self.rouq4_tick.isChecked(),  name=Path(
                self.target_filepath).stem,  fig=self.current_fig)
                fig_2 = regression_diagnostics_plots(self.bet_filter_result, name=Path(
                self.target_filepath).stem, fig_2=self.current_fig_2)
            # connect the picker event to the figure
            if self.current_fig is None:
                fig.canvas.mpl_connect('pick_event', self.point_picker)
            self.current_fig = fig
            self.current_fig.tight_layout(pad=0.3, rect=[0, 0, 1, 0.95])
            self.current_fig_2 = fig_2
            plt.figure(num=1)
            plt.draw()
            plt.figure(num=2).canvas.manager.window.move(500,0)
            plt.draw()
        except TypeError:
            pass
        
    def run_calculation(self):
        """ Applies the currently specified filters to the currently specified target csv file. """

        ## assert self.target_filepath, "You must provide a csv file before calling run."
        if not self.target_filepath:
            warnings = "You must provide an input file (e.g. *.csv, *.txt, *.aif, *.XLS) before calling run. Press \"Clear\" and try again. Please refer to the \"Hints\" box for a quick guide."
            information = ""
            self.show_dialog(warnings, information)
            return

        use_rouq1 = self.rouq1_tick.isChecked()
        use_rouq2 = self.rouq2_tick.isChecked()
        use_rouq3 = self.rouq3_tick.isChecked()
        use_rouq4 = self.rouq4_tick.isChecked()
        use_rouq5 = self.rouq5_tick.isChecked()
        min_num_pts = int(self.min_points_edit.text())
        min_r2 = float(self.minr2_edit.text())
        max_perc_error = float(self.rouq4_edit.text())
        adsorbate = self.adsorbate_combo_box.currentText()
        cross_sectional_area = float(self.adsorbate_cross_section_edit.text())
        molar_volume = float(self.adsorbate_molar_volume_edit.text())

        
        # Retrieve the BETSI results object if non-existent
        if self.bet_object is None:
            pressure, q_adsorbed, comments_to_data = get_data(input_file=self.target_filepath)
            if len(pressure) == 0 or len(q_adsorbed) == 0:
                warnings = "You must provide a valid input file. BETSI cannot read it. Press \"Clear\" and try again with a valid one."
                information = ""
                self.show_dialog(warnings, information)
                return
            self.bet_object = BETResult(pressure, q_adsorbed)
            self.bet_object.comments_to_data = comments_to_data
            self.bet_object.original_pressure_data = pressure
            self.bet_object.original_q_adsorbed_data = q_adsorbed
            

        # Apply the currently selected filters.
        self.bet_filter_result = BETFilterAppliedResults(self.bet_object,
                                                         min_num_pts=min_num_pts,
                                                         min_r2=min_r2,
                                                         use_rouq1=use_rouq1,
                                                         use_rouq2=use_rouq2,
                                                         use_rouq3=use_rouq3,
                                                         use_rouq4=use_rouq4,
                                                         use_rouq5=use_rouq5,
                                                         max_perc_error=max_perc_error,
                                                         adsorbate=adsorbate, 
                                                         cross_sectional_area=cross_sectional_area,
                                                         molar_volume=molar_volume)
        ## Adds interpolated points to adsorption data if no valid area was found by the original data
        if not self.bet_filter_result.has_valid_areas:
            iter_num = 0
            self.bet_object.comments_to_data['interpolated_points_added'] = True
            while (not self.bet_filter_result.has_valid_areas) and (iter_num < 20):
                print('Adding extra interpolated points to the data')
                
                ##pressure = self.bet_object.pressure
                ##q_adsorbed = self.bet_object.q_adsorbed
                comments_to_data = self.bet_object.comments_to_data
                interpolated_points_added = self.bet_object.comments_to_data['interpolated_points_added']
                original_pressure_data = self.bet_object.original_pressure_data
                original_q_adsorbed_data = self.bet_object.original_q_adsorbed_data
                
                self.bet_object = None
                self.bet_filter_result = None
                pressure_added_points, q_adsorbed_added_points = isotherm_pchip_reconstruction(original_pressure_data, original_q_adsorbed_data, (iter_num+1)*round(len(original_pressure_data)/1.5))
                self.bet_object = BETResult(pressure_added_points, q_adsorbed_added_points)
                self.bet_object.comments_to_data = comments_to_data
                self.bet_object.comments_to_data['interpolated_points_added'] = interpolated_points_added
                self.bet_object.original_pressure_data = original_pressure_data
                self.bet_object.original_q_adsorbed_data = original_q_adsorbed_data
                
                # Apply the currently selected filters.
                self.bet_filter_result = BETFilterAppliedResults(self.bet_object,
                                                                 min_num_pts=min_num_pts,
                                                                 min_r2=min_r2,
                                                                 use_rouq1=use_rouq1,
                                                                 use_rouq2=use_rouq2,
                                                                 use_rouq3=use_rouq3,
                                                                 use_rouq4=use_rouq4,
                                                                 use_rouq5=use_rouq5,
                                                                 max_perc_error=max_perc_error,
                                                                 adsorbate=adsorbate, 
                                                                 cross_sectional_area=cross_sectional_area,
                                                                 molar_volume=molar_volume)
                iter_num += 1
        
        ## Warnings for pop-up message box
        warnings = ""
        information = ""
        if self.bet_object.comments_to_data['has_negative_pressure_points']:
            warnings += "- Imported adsorption data has negative pressure point(s)!\n"
            information += "- Negative pressure point(s) have been removed from the data.\n"
        if not self.bet_object.comments_to_data['monotonically_increasing_pressure']:
            warnings += "- The pressure points are not monotonically increasing!\n"
            information += "- Non-monotonically increasing pressure point(s) have been removed from the data.\n"
        if not self.bet_object.comments_to_data['rel_pressure_between_0_and_1']:
            warnings += "- The relative pressure values must lie between 0 and 1!\n"
            information += "- Relative pressure point(s) above 1.0 have been removed from the data.\n"
        if self.bet_object.comments_to_data['interpolated_points_added']:
            warnings += "- No valid areas found with the chosen minimum number of points! So, interpolated points are added to the data!\n"

        ## Create plots and print display warnings
        if self.bet_filter_result.has_valid_areas:
            self.plot_bet()
            if warnings != "":
                warnings = "Consider the following warning(s):\n" + warnings
                if information != "":
                    information = "Note(s):\n" + information
                self.show_dialog(warnings, information)
        else:
            if warnings == "":
                warnings = "No valid areas found! Try again with a new set of data and/or change your criteria"
                self.show_dialog(warnings, information)
            else:
                warnings_1 = "No valid areas found! Try again with a new set of data and/or change your criteria.\n"
                warnings_2 = "Consider the following warning(s):\n"
                warnings = warnings_1 + warnings_2 + warnings
                information = "Note(s):\n" + information
                self.show_dialog(warnings, information)
    
            
    def show_dialog(self, warnings, information):
        # Log the warnings
        if self.warning_widget is False:
            print(f'\n{warnings}{information}\n')
            # Create a local sub-directory for log if not already done.
            target_path = Path(self.target_filepath)
            output_subdir = Path(self.output_dir) / target_path.name
            output_subdir.mkdir(exist_ok=True)
            with (output_subdir / 'warnings.log').open('w') as fp:
                print(f'\n{warnings}{information}\n',file=fp)
        else :
            dialog = QMessageBox()
            dialog.setText(warnings)
            dialog.setWindowTitle('Warnings')
            if warnings.find("No valid areas found!") != -1:
                dialog.setIcon(QMessageBox().Critical)
                dialog.setStandardButtons(QMessageBox.Ok)
                dialog.addButton("Clear", QMessageBox.AcceptRole)
                if information != "":
                    information += "\n\nPress \"Clear\" if you want to clear input data, reset to default values and start over with a new set of data.\n"
                else:
                    information = "Press \"Clear\" if you want to clear input data, reset to default values and start over with a new set of data.\n"
            elif warnings.find("You must provide a") != -1:
                dialog.setIcon(QMessageBox().Critical)
                dialog.addButton("Clear", QMessageBox.AcceptRole)
            else:
                dialog.setIcon(QMessageBox().Warning)
            dialog.setInformativeText(information)
            
            dialog.buttonClicked.connect(self.dialog_clicked)
            dialog.exec_()

    def dialog_clicked(self, dialog_button):
        if dialog_button.text() == "Clear":
            self.clear()

    def point_picker(self, event):
        line = event.artist
        picked_coords = line.get_offsets()[event.ind][0]
        # redefine min_i and min_j
        self.bet_filter_result.find_nearest_idx(picked_coords)
        # replot based on the new min_i and min_j
        self.plot_bet()

    def export(self):
        """ Print out the plot, filter config and results to the output directory. """
        if self.bet_filter_result is not None:

            # Create a local sub-directory for export.
            target_path = Path(self.target_filepath)
            output_subdir = Path(self.output_dir) / target_path.name
            output_subdir.mkdir(exist_ok=True)
            self.bet_filter_result.export(output_subdir)
            self.current_fig.savefig(str(output_subdir / f'{target_path.stem}_plot.pdf'), bbox_inches='tight')
            if self.display_plot:
                plt.show()
            self.current_fig_2.savefig(str(output_subdir / f'{target_path.stem}_RD_plots.pdf'))
            if self.display_plot:
                plt.show()

    def analyse_directory(self, dir_path):
        """ Run BETSI on all csv files within dir_path. Use current filter config."""
        input_file_paths = (*Path(dir_path).glob('*.csv'),
                            *Path(dir_path).glob('*.aif'),
                            *Path(dir_path).glob('*.txt'))
        for file_path in input_file_paths:
            print(f"\nReading file {file_path}.\n")
            self.target_filepath = file_path
            self.display_plot = False
            self.warning_widget = False
            self.run_calculation()
            self.export()
            self.clear()

        print(f"\nBET analysis on {len(input_file_paths)} input files terminated.")

    def set_defaults(self):
        """Sets the widget to default state
        """
        # set default values for the tick marks
        self.rouq1_tick.setCheckState(True)
        self.rouq2_tick.setCheckState(True)
        self.rouq3_tick.setCheckState(True)
        self.rouq4_tick.setCheckState(True)
        self.rouq5_tick.setCheckState(True)

        # the ticks can only be on or off - Not sure why I need to do this every time, but doesn't matter
        self.rouq1_tick.setTristate(False)
        self.rouq2_tick.setTristate(False)
        self.rouq3_tick.setTristate(False)
        self.rouq4_tick.setTristate(False)
        self.rouq5_tick.setTristate(False)
        # set defaults for text fields
        self.minr2_edit.setText('0.995')
        self.rouq4_edit.setText('20')
        self.min_points_edit.setText('10')
        
        
        ## set defaults for adsorbate related parameters
        self.adsorbate_combo_box.setCurrentIndex(0)
        #self.adsorbate_cross_section_edit.setText('0.0')
        #self.adsorbate_molar_volume_edit.setText('0.0')
        self.adsorbate_cross_section_edit.setText(str(cross_sectional_area[self.adsorbate_combo_box.currentText()] * 1.0E18))
        self.adsorbate_molar_volume_edit.setText(str(mol_vol[self.adsorbate_combo_box.currentText()]))
        
        
        self.line_edit_values_before = {"minr2_edit": self.minr2_edit.text(), \
            "rouq4_edit": self.rouq4_edit.text(), \
            "min_points_edit": self.min_points_edit.text(), \
            "adsorbate_cross_section_edit": self.adsorbate_cross_section_edit.text(), \
            "adsorbate_molar_volume_edit": self.adsorbate_molar_volume_edit.text()}
        
        
        # trigger the corresponding sliders
        self.rouq4_edit_changed()
        self.minr2_edit_changed()
        self.min_points_edit_changed()
        # check the compatibility
        self.check_rouq_compatibility()
        
        ## check the compatibility for adsorbate
        self.check_adsorbate_compatibility()

        # By default, plots are displayed
        self.display_plot = True

        # if there is a figure, replot
        self.plot_bet()

        # Display warnings
        self.warning_widget = True

    def clear(self):
        """Closes all plots and removes all data from memory"""
        # remove the bet filter result from memory
        self.bet_filter_result = None
        self.bet_object = None
        # clear the table
        self.clean_table()
        # close the plot
        if self.current_fig is not None:
            plt.close(fig=self.current_fig)
            plt.close(fig=self.current_fig_2)
        
        
        ##reset the parameters to defaults
        self.target_filepath = None
        self.current_targetpath_label.setText(
            f"Loaded File: {self.target_filepath}")
        self.set_defaults()

    def set_editable(self, state):
        if state:
            self.rouq1_tick.setEnabled(True)
            self.rouq2_tick.setEnabled(True)
            self.rouq3_tick.setEnabled(True)
            self.rouq4_tick.setEnabled(True)
            self.rouq5_tick.setEnabled(True)
            self.minr2_edit.setEnabled(True)
            self.rouq4_edit.setEnabled(True)
            self.min_points_edit.setEnabled(True)
            self.rouq4_slider.setEnabled(True)
            self.minr2_slider.setEnabled(True)
            self.min_points_slider.setEnabled(True)
            self.adsorbate_combo_box.setEnabled(True)
            self.adsorbate_cross_section_edit.setEnabled(True)
            self.adsorbate_molar_volume_edit.setEnabled(True)
        else:
            self.rouq1_tick.setEnabled(False)
            self.rouq2_tick.setEnabled(False)
            self.rouq3_tick.setEnabled(False)
            self.rouq4_tick.setEnabled(False)
            self.rouq5_tick.setEnabled(False)
            self.minr2_edit.setEnabled(False)
            self.rouq4_edit.setEnabled(False)
            self.min_points_edit.setEnabled(False)
            self.rouq4_slider.setEnabled(False)
            self.minr2_slider.setEnabled(False)
            self.min_points_slider.setEnabled(False)
            self.adsorbate_combo_box.setEnabled(False)
            self.adsorbate_cross_section_edit.setEnabled(False)
            self.adsorbate_molar_volume_edit.setEnabled(False)

    def check_rouq_compatibility(self):
        use_rouq1 = self.rouq1_tick.isChecked()
        use_rouq2 = self.rouq2_tick.isChecked()
        use_rouq3 = self.rouq3_tick.isChecked()
        use_rouq4 = self.rouq4_tick.isChecked()
        use_rouq5 = self.rouq5_tick.isChecked()
        if not (use_rouq3 or use_rouq4):
            self.rouq2_tick.setEnabled(True)
        else:
            self.rouq2_tick.setChecked(True)
            self.rouq2_tick.setEnabled(False)

    def check_adsorbate_compatibility(self):
        if self.adsorbate_combo_box.currentText() != "Custom":
            self.adsorbate_cross_section_edit.setEnabled(False)
            self.adsorbate_molar_volume_edit.setEnabled(False)            
            self.adsorbate_cross_section_edit.setText("{0:0.3f}".format(cross_sectional_area[self.adsorbate_combo_box.currentText()] * 1.0E18))
            self.adsorbate_molar_volume_edit.setText("{0:0.3f}".format(mol_vol[self.adsorbate_combo_box.currentText()]))
            #self.adsorbate_cross_section_edit.setText("0.0")
            #self.adsorbate_molar_volume_edit.setText("0.0")
        else:
            self.adsorbate_cross_section_edit.setEnabled(True)
            self.adsorbate_molar_volume_edit.setEnabled(True)
            
    def populate_table(self, csv_path):
        self.results_table.setColumnCount(2)
        self.results_table.setRowCount(1)
        self.results_table.setHorizontalHeaderLabels(
            ['Relative pressure (p/p\u2080)', 'Quantity adsorbed (cm\u00B3/g)'])
        self.results_table.setColumnWidth(0, 250)
        self.results_table.setColumnWidth(1, 250)

        # Change the box title
        self.current_targetpath_label.setText(
            f"Loaded File: {self.target_filepath}")

        if csv_path is not None and Path(csv_path).exists():
            pressure, q_adsorbed, comments_to_data = get_data(input_file=csv_path)
            self.results_table.setRowCount(len(pressure))
            for i in range(len(pressure)):
                self.results_table.setItem(
                    i, 0, QTableWidgetItem(str(pressure[i])))
                self.results_table.setItem(
                    i, 1, QTableWidgetItem(str(q_adsorbed[i])))

    def clean_table(self):
        """Cleans the table"""
        self.results_table.setColumnCount(2)
        self.results_table.setRowCount(0)
        self.results_table.setHorizontalHeaderLabels(
            ['Relative pressure (p/p\u2080)', 'Quantity adsorbed (cm\u00B3 STP/g)'])
        self.results_table.setColumnWidth(0, 250)
        self.results_table.setColumnWidth(1, 250)


    def minr2_edit_changed(self):
        value = self.minr2_edit.text()
        mn = self.minr2_slider.minimum()
        mx = self.minr2_slider.maximum()
        try:
            value = int(round(float(value) * 1000))
            if value < mn:
                value = mn
                self.minr2_edit.setText(str(value / 1000))
            elif value > mx:
                value = mx
                self.minr2_edit.setText(str(value / 1000))
            self.minr2_slider.setValue(value)
        except (ValueError, TypeError):
            self.minr2_edit.setText('0.995')
        if self.line_edit_values_before["minr2_edit"] != self.minr2_edit.text():
            self.line_edit_values_before["minr2_edit"] = self.minr2_edit.text()
            self.maybe_run_calculation()

    def rouq4_edit_changed(self):
        value = self.rouq4_edit.text()
        mn = self.rouq4_slider.minimum()
        mx = self.rouq4_slider.maximum()
        try:
            value = int(float(value))
            if value < mn:
                value = mn
                self.rouq4_edit.setText(str(value))
            if value > mx:
                value = mx
                self.rouq4_edit.setText(str(value))
            self.rouq4_slider.setValue(value)
        except (ValueError, TypeError):
            self.rouq4_edit.setText('20')
        if self.line_edit_values_before["rouq4_edit"] != self.rouq4_edit.text():
            self.line_edit_values_before["rouq4_edit"] = self.rouq4_edit.text()
            self.maybe_run_calculation()

    def min_points_edit_changed(self):
        value = self.min_points_edit.text()
        mn = self.min_points_slider.minimum()
        mx = self.min_points_slider.maximum()
        try:
            value = int(round(float(value)))
            if value < mn:
                value = mn
                self.min_points_edit.setText(str(value))
            if value > mx:
                value = mx
                self.min_points_edit.setText(str(value))
            self.min_points_slider.setValue(value)
        except (ValueError, TypeError):
            self.min_points_edit.setText('10')
        if self.line_edit_values_before["min_points_edit"] != self.min_points_edit.text():
            self.line_edit_values_before["min_points_edit"] = self.min_points_edit.text()
            self.maybe_run_calculation()

    def rouq4_slider_changed(self):
        value = self.rouq4_slider.value()
        self.rouq4_edit.setText(str(value))
        self.maybe_run_calculation()

    def minr2_slider_changed(self):
        value = self.minr2_slider.value()
        self.minr2_edit.setText(str(value / 1000))
        self.maybe_run_calculation()

    def min_points_slider_changed(self):
        value = self.min_points_slider.value()
        self.min_points_edit.setText(str(value))
        self.maybe_run_calculation()
        
    def adsorbate_related_edit_changed(self):
        if not self.is_float(self.adsorbate_cross_section_edit.text()):
            self.adsorbate_cross_section_edit.setText("0.0")
        if not self.is_float(self.adsorbate_molar_volume_edit.text()):
            self.adsorbate_molar_volume_edit.setText("0.0")
        if self.line_edit_values_before["adsorbate_cross_section_edit"] != self.adsorbate_cross_section_edit.text() or \
        self.line_edit_values_before["adsorbate_molar_volume_edit"] != self.adsorbate_molar_volume_edit.text():
            self.line_edit_values_before["adsorbate_cross_section_edit"] = self.adsorbate_cross_section_edit.text()
            self.line_edit_values_before["adsorbate_molar_volume_edit"] = self.adsorbate_molar_volume_edit.text()
            self.maybe_run_calculation()
    
    def adsorbate_combo_box_changed(self):
        if self.adsorbate_combo_box.currentText() == "Custom":
            self.adsorbate_cross_section_edit.setText("0.0")
            self.adsorbate_molar_volume_edit.setText("0.0")
        self.maybe_run_calculation()
                
    def line_edit_changed(self):
        # modify_check = []
        # modify_check.append(self.minr2_edit.isModified())
        # modify_check.append(self.rouq4_edit.isModified())
        # modify_check.append(self.min_points_edit.isModified())
        # modify_check.append(self.adsorbate_cross_section_edit.isModified())
        # modify_check.append(self.adsorbate_molar_volume_edit.isModified())
        current_line_edit_values = self.get_line_edit_current_values()
        if self.line_edit_values_before != current_line_edit_values:
            self.maybe_run_calculation()
        self.line_edit_values_before = current_line_edit_values
    
    def get_line_edit_current_values(self):
        current_line_edit_values = []
        current_line_edit_values.append(self.minr2_edit.text())
        current_line_edit_values.append(self.rouq4_edit.text())
        current_line_edit_values.append(self.min_points_edit.text())
        current_line_edit_values.append(self.adsorbate_cross_section_edit.text())
        current_line_edit_values.append(self.adsorbate_molar_volume_edit.text())
        return current_line_edit_values
    
    def is_float(self, string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    def __del__(self):
        try:
            plt.close(self.current_fig_2)
            plt.close(self.current_fig)
        except:
            pass

class OutputCanvas(FigureCanvas):
    def __init__(self, parent, dpi=100):
        self.fig = Figure(dpi=dpi)
        self.fig.subplots_adjust(left=0.05, right=0.95)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class OutputCanvas_2(FigureCanvas):
    def __init__(self,parent,dpi=100):
        self.fig_2 = Figure(dpi=dpi)
        self.fig_2.subplots_adjust(left=.05, right=.95)
        FigureCanvas.__init__(self,self.fig_2)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

class OutLog(logging.Handler):
    def __init__(self, out_widget):
        """(edit, out=None, color=None) -> can write stdout, stderr to a
        QTextEdit.
        """
        logging.Handler.__init__(self)
        self.out_widget = out_widget

    def emit(self, message):
        self.write(message.getMessage() + '\n')

    def write(self, m):
        self.out_widget.moveCursor(QtGui.QTextCursor.End)
        self.out_widget.insertPlainText(m)


def runbetsi():
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    ex = BETSI_gui()
    ex.show()
    sys.exit(app.exec_())

runbetsi()