import os
import sys
import pandas as pd
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableSequence
import re
import argparse
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QFileDialog, QLabel, QSizePolicy, QSpinBox, QMessageBox, QComboBox
)
from PySide6.QtCore import QThread, Signal, Qt

# --- Backend Logic (Copied from your previous script, ideally in a separate file) ---
# This part should ideally be in a separate module (e.g., backend_processor.py)
# and imported. For demonstration, it's included here.

SEPERATOR = '|'
# Load environment variables
load_dotenv()
google_api_key = os.getenv('GEMINI_API_KEY')

# Redefined here to make it part of the worker for clean execution
class BackendWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(str) # Signal to update the log/status window

    def __init__(self, prompt_instruction, input_folder, bundle_size, bundled_folder, result_folder, merge_results):
        super().__init__()
        self.prompt_instruction = prompt_instruction
        self.input_folder = input_folder
        self.bundle_size = bundle_size
        self.bundled_folder = bundled_folder
        self.result_folder = result_folder
        self.merge_results = merge_results # New parameter for merging

    def run(self):
        try:
            self._process_llm_parsing_reports()
            self.finished.emit("Processing complete!")
        except Exception as e:
            self.error.emit(f"An error occurred: {e}")

    def _read_prompt_from_file(self, filepath: str) -> str:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Error: Prompt file '{filepath}' not found.")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except IOError as e:
            raise IOError(f"Error reading prompt file '{filepath}': {e}")

    def _process_llm_parsing_reports(self):
        reports_folder = self.input_folder
        size_of_a_bundle = self.bundle_size
        prompt_instruction = self.prompt_instruction
        bundled_files_dir = self.bundled_folder
        results_files_dir = self.result_folder

        if not os.path.isdir(reports_folder):
            self.error.emit(f"Error: Input folder '{reports_folder}' not found.")
            return

        report_files = [f for f in os.listdir(reports_folder) if f.endswith('.txt')]
        if not report_files:
            self.error.emit(f"No .txt report files found in '{reports_folder}'.")
            return

        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

        report_files.sort(key=natural_sort_key)

        os.makedirs(bundled_files_dir, exist_ok=True)
        self.progress.emit(f"Bundled files will be saved in: {os.path.abspath(bundled_files_dir)}")

        os.makedirs(results_files_dir, exist_ok=True)
        self.progress.emit(f"Result CSV files will be saved in: {os.path.abspath(results_files_dir)}")

        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=google_api_key, temperature=0.0)

        prompt = PromptTemplate(
            input_variables=["file_content"],
            template="{file_content}\n\n" + prompt_instruction
        )
        llmchain = prompt | llm

        bundle_count = 0
        individual_csv_files = [] # To store paths of generated CSVs for merging

        for i in range(0, len(report_files), size_of_a_bundle):
            bundle_count += 1
            current_bundle_files = report_files[i:i + size_of_a_bundle]
            bundle_content = ""
            filename_list = ", ".join(current_bundle_files)

            self.progress.emit(f"\n--- Processing Bundle {bundle_count} ---")
            self.progress.emit(f"Files in this bundle: {filename_list}")

            for filename in current_bundle_files:
                filepath = os.path.join(reports_folder, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    bundle_content += f"Filename: {filename}\n" + f.read() + "\n\n---\n\n"

            bundle_output_filepath = os.path.join(bundled_files_dir, f"bundle_{bundle_count}.txt")
            with open(bundle_output_filepath, "w", encoding="utf-8") as bundle_file:
                bundle_file.write(bundle_content)
            self.progress.emit(f"Bundle content saved to {bundle_output_filepath}")

            result = llmchain.invoke({"file_content": bundle_content})
            llm_output_text = result.content

            try:
                lines = llm_output_text.strip().split('\n')
                cleaned_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('```')]

                if len(cleaned_lines) < 2:
                    self.progress.emit(f"LLM did not return enough lines to form a table for bundle {bundle_count}.")
                    continue

                header_line = ""
                separator_line = ""
                data_start_index = -1

                for idx, line in enumerate(cleaned_lines):
                    if '|' in line and '---' not in line:
                        header_line = line
                        if idx + 1 < len(cleaned_lines) and '---' in cleaned_lines[idx+1]:
                            separator_line = cleaned_lines[idx+1]
                            data_start_index = idx + 2
                            break

                if not header_line or not separator_line or data_start_index == -1:
                    self.progress.emit(f"Could not identify table header or data start in LLM output for bundle {bundle_count}.")
                    continue

                columns = [col.strip() for col in header_line.strip('|').split('|')]
                data = []
                for j in range(data_start_index, len(cleaned_lines)):
                    current_line = cleaned_lines[j]
                    if current_line.strip():
                        row_values = [val.strip() for val in current_line.strip('|').split('|')]
                        if len(row_values) == len(columns):
                            data.append(row_values)
                        else:
                            self.progress.emit(f"Skipping malformed row (column count mismatch) for bundle {bundle_count}: {current_line}")

                df = pd.DataFrame(data, columns=columns)
                output_csv_filename = os.path.join(results_files_dir, f"result_{bundle_count}.csv")
                df.to_csv(output_csv_filename, index=False, encoding='utf-8-sig', sep=SEPERATOR)
                self.progress.emit(f"Results saved to {output_csv_filename}")
                individual_csv_files.append(output_csv_filename) # Add to list for merging

            except Exception as e:
                self.progress.emit(f"Error parsing LLM output for bundle {bundle_count}: {e}")

        # --- Result Merging Logic ---
        if self.merge_results and individual_csv_files:
            self.progress.emit("\n--- Merging individual result CSVs ---")
            merged_df = pd.DataFrame()
            for csv_file in individual_csv_files:
                try:
                    df_temp = pd.read_csv(csv_file, sep=SEPERATOR, encoding='utf-8-sig')
                    merged_df = pd.concat([merged_df, df_temp], ignore_index=True)
                except Exception as e:
                    self.progress.emit(f"Warning: Could not read {csv_file} for merging: {e}")

            if not merged_df.empty:
                merged_output_filepath = os.path.join(os.getcwd(), "merged_results.csv")
                merged_df.to_csv(merged_output_filepath, index=False, encoding='utf-8-sig', sep=SEPERATOR)
                self.progress.emit(f"All results merged into: {os.path.abspath(merged_output_filepath)}")

                # Optionally, clean up individual CSVs after merging
                # for csv_file in individual_csv_files:
                #     try:
                #         os.remove(csv_file)
                #         self.progress.emit(f"Removed individual file: {os.path.basename(csv_file)}")
                #     except Exception as e:
                #         self.progress.emit(f"Warning: Could not remove {csv_file}: {e}")
            else:
                self.progress.emit("No data to merge.")


class ReportProcessorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM Pathology Report Processor")
        self.setGeometry(100, 100, 800, 700) # Increased initial window height

        self.worker_thread = None # Initialize worker_thread

        self.init_ui()
        self.set_default_values()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 1. Prompt Input
        # New layout for Prompt Label and Load Prompt Button
        prompt_header_layout = QHBoxLayout()
        prompt_label = QLabel("Prompt Instruction:")
        prompt_header_layout.addWidget(prompt_label)
        prompt_header_layout.addStretch(1) # Pushes the button to the right

        self.load_prompt_btn = QPushButton("Load Prompt from File")
        self.load_prompt_btn.clicked.connect(self.load_prompt_file)
        prompt_header_layout.addWidget(self.load_prompt_btn)
        main_layout.addLayout(prompt_header_layout)

        # Prompt text edit remains below the header
        self.prompt_text_edit = QTextEdit()
        self.prompt_text_edit.setPlaceholderText("Enter your LLM prompt instructions here, or load from file...")
        self.prompt_text_edit.setMinimumHeight(80)
        main_layout.addWidget(self.prompt_text_edit)

        # 2. Bundle Size and Result Merging
        bundle_config_layout = QHBoxLayout() # New layout for this row
        
        bundle_size_label = QLabel("Bundle Size:")
        self.bundle_size_spinbox = QSpinBox()
        self.bundle_size_spinbox.setRange(1, 1000)
        self.bundle_size_spinbox.setValue(10)

        # Result Merging
        result_merging_label = QLabel("Result Merging:")
        self.merge_results_combobox = QComboBox()
        self.merge_results_combobox.addItems(["Yes", "No"])
        self.merge_results_combobox.setCurrentText("Yes") # Default to Yes

        bundle_config_layout.addWidget(bundle_size_label)
        bundle_config_layout.addWidget(self.bundle_size_spinbox)
        bundle_config_layout.addStretch(1) # Adds flexible space
        bundle_config_layout.addWidget(result_merging_label)
        bundle_config_layout.addWidget(self.merge_results_combobox)
        bundle_config_layout.addStretch(1) # Adds flexible space

        main_layout.addLayout(bundle_config_layout)

        # 3. Input Folder (Display then Button)
        input_folder_layout = QHBoxLayout()
        input_label = QLabel("Input Folder:")
        self.input_folder_display = QLineEdit()
        self.input_folder_display.setReadOnly(True)
        self.input_folder_display.setPlaceholderText("Path to your input reports")
        input_folder_btn = QPushButton("Select Input Folder")
        input_folder_btn.clicked.connect(self.select_input_folder)

        input_folder_layout.addWidget(input_label)
        input_folder_layout.addWidget(self.input_folder_display)
        input_folder_layout.addWidget(input_folder_btn)
        main_layout.addLayout(input_folder_layout)

        # 4. Result Folder (Display then Button)
        result_folder_layout = QHBoxLayout()
        result_label = QLabel("Result Folder:")
        self.result_folder_display = QLineEdit()
        self.result_folder_display.setReadOnly(True)
        self.result_folder_display.setPlaceholderText("Path to save result CSVs")
        result_folder_btn = QPushButton("Select Result Folder")
        result_folder_btn.clicked.connect(self.select_result_folder)

        result_folder_layout.addWidget(result_label)
        result_folder_layout.addWidget(self.result_folder_display)
        result_folder_layout.addWidget(result_folder_btn)
        main_layout.addLayout(result_folder_layout)

        # 5. Bundled Folder (Display then Button)
        bundled_folder_layout = QHBoxLayout()
        bundled_label = QLabel("Bundled Folder:")
        self.bundled_folder_display = QLineEdit()
        self.bundled_folder_display.setReadOnly(True)
        self.bundled_folder_display.setPlaceholderText("Path to save bundled text files")
        bundled_folder_btn = QPushButton("Select Bundled Folder")
        bundled_folder_btn.clicked.connect(self.select_bundled_folder)

        bundled_folder_layout.addWidget(bundled_label)
        bundled_folder_layout.addWidget(self.bundled_folder_display)
        bundled_folder_layout.addWidget(bundled_folder_btn)
        main_layout.addLayout(bundled_folder_layout)

        # Scrollable Status/Log Display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setPlaceholderText("Processing log will appear here...")
        self.log_display.setMinimumHeight(150)
        main_layout.addWidget(QLabel("Processing Log:"))
        main_layout.addWidget(self.log_display)

        # 6. Run Button
        run_button_layout = QHBoxLayout()
        self.run_button = QPushButton("실행")
        self.run_button.setFixedSize(200, 60)
        self.run_button.setStyleSheet("font-size: 24px; font-weight: bold;")

        run_button_layout.addStretch()
        run_button_layout.addWidget(self.run_button)
        run_button_layout.addStretch()
        main_layout.addLayout(run_button_layout)

        self.run_button.clicked.connect(self.run_processing)

    def set_default_values(self):
        self.input_folder_display.setText("Input_Files")
        self.result_folder_display.setText("Result_Files")
        self.bundled_folder_display.setText("Bundled_Files")

    def load_prompt_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Text files (*.txt)")
        file_dialog.setWindowTitle("Select Prompt File")

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                filepath = selected_files[0]
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.prompt_text_edit.setText(f.read())
                    self.update_log(f"Loaded prompt from: {filepath}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not read file: {e}")
                    self.update_log(f"ERROR: Could not read prompt file: {e}")

    def select_input_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Input Folder", self.input_folder_display.text())
        if directory:
            self.input_folder_display.setText(directory)
            self.update_log(f"Input folder set to: {directory}")

    def select_result_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Result Folder", self.result_folder_display.text())
        if directory:
            self.result_folder_display.setText(directory)
            self.update_log(f"Result folder set to: {directory}")

    def select_bundled_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Bundled Folder", self.bundled_folder_display.text())
        if directory:
            self.bundled_folder_display.setText(directory)
            self.update_log(f"Bundled folder set to: {directory}")

    def update_log(self, message):
        self.log_display.append(message)
        self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())
        QApplication.processEvents()

    def handle_finished(self, message):
        self.update_log(message)
        self.run_button.setEnabled(True)
        QMessageBox.information(self, "Processing Complete", message)

    def handle_error(self, message):
        self.update_log(f"ERROR: {message}")
        self.run_button.setEnabled(True)
        QMessageBox.critical(self, "Error", message)

    def run_processing(self):
        prompt_instruction = self.prompt_text_edit.toPlainText().strip()
        input_folder = self.input_folder_display.text().strip()
        bundle_size = self.bundle_size_spinbox.value()
        bundled_folder = self.bundled_folder_display.text().strip()
        result_folder = self.result_folder_display.text().strip()
        merge_results = (self.merge_results_combobox.currentText() == "Yes") # Get merging preference

        self.log_display.clear()

        if not prompt_instruction:
            QMessageBox.warning(self, "Input Missing", "Please enter or load prompt instructions.")
            self.update_log("Processing cancelled: Prompt instruction is missing.")
            return
        if not input_folder:
            QMessageBox.warning(self, "Input Missing", "Please select an input folder.")
            self.update_log("Processing cancelled: Input folder is not selected.")
            return
        if not os.path.exists(input_folder):
            QMessageBox.warning(self, "Invalid Path", f"Input folder does not exist: {input_folder}")
            self.update_log(f"Processing cancelled: Input folder does not exist: {input_folder}")
            return

        self.run_button.setEnabled(False)
        self.update_log("Processing started... Please wait.")

        # Create and start the worker thread with the new merge_results parameter
        self.worker_thread = BackendWorker(
            prompt_instruction, input_folder, bundle_size, bundled_folder, result_folder, merge_results
        )
        self.worker_thread.finished.connect(self.handle_finished)
        self.worker_thread.error.connect(self.handle_error)
        self.worker_thread.progress.connect(self.update_log)
        self.worker_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = ReportProcessorGUI()
    gui.show()
    sys.exit(app.exec())