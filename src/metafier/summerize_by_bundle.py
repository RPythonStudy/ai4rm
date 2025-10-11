# pip install langchain-google-genai langchain python-dotenv pandas
# python .\summerize_by_bundle.py prompt_lung_patho.txt


import os
import pandas as pd
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableSequence
import re
import argparse

SEPERATOR = '|'
# Load environment variables
load_dotenv()
google_api_key = os.getenv('GEMINI_API_KEY')

def read_prompt_from_file(filepath: str) -> str:
    """
    Reads the content of a file line by line and returns it as a single string.

    Args:
        filepath (str): The path to the file containing the prompt instructions.

    Returns:
        str: The content of the file as a single string.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If there's an issue reading the file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Error: Prompt file '{filepath}' not found.")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except IOError as e:
        raise IOError(f"Error reading prompt file '{filepath}': {e}")


def process_llm_parsing_reports(input_folder: str, size_of_a_bundle: int, prompt_instruction: str = "",
                                bundled_files_dir: str = "Bundled_Files", results_files_dir: str = "Result_Files"):
    """
    Processes pathology reports from a folder, bundles them, extracts key information,
    and outputs to CSV and console, including the original filename.

    Args:
        input_folder (str): The path to the folder containing pathology reports.
        size_of_a_bundle (int): The number of reports to bundle together for processing.
        prompt_instruction (str): The instruction for the LLM to extract information.
        bundled_files_dir (str): Directory to save bundled text files.
        results_files_dir (str): Directory to save result CSV files.
    """
    if not os.path.isdir(input_folder):
        print(f"Error: Folder '{input_folder}' not found.")
        return

    report_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
    if not report_files:
        print(f"No .txt report files found in '{input_folder}'.")
        return

    # 파일 이름을 자연어 숫자 순으로 정렬하는 함수 (예: report_1.txt, report_2.txt, ..., report_10.txt)
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

    report_files.sort(key=natural_sort_key) # 파일 목록을 정렬합니다.

    # Create the Bundled_Files directory if it doesn't exist
    os.makedirs(bundled_files_dir, exist_ok=True)
    print(f"Bundled files will be saved in: {os.path.abspath(bundled_files_dir)}")

    # Create the Result_Files directory if it doesn't exist
    os.makedirs(results_files_dir, exist_ok=True)
    print(f"Result CSV files will be saved in: {os.path.abspath(results_files_dir)}")

    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=google_api_key, temperature=0.0)

    prompt = PromptTemplate(
        input_variables=["file_content"],
        template="{file_content}\n\n" + prompt_instruction
    )
    # Use RunnableSequence to chain the prompt and llm together
    llmchain = prompt | llm

    bundle_count = 0
    for i in range(0, len(report_files), size_of_a_bundle):
        bundle_count += 1
        current_bundle_files = report_files[i:i + size_of_a_bundle]
        bundle_content = ""
        filename_list = ", ".join(current_bundle_files)
        for filename in current_bundle_files:
            filepath = os.path.join(input_folder, filename) # Use input_folder here
            with open(filepath, "r", encoding="utf-8") as f:
                # Add filename to the beginning of the report content
                bundle_content += f"Filename: {filename}\n" + f.read() + "\n\n---\n\n"

        print(f"\n--- Processing Bundle {bundle_count} ---")
        print(f"Files in this bundle: {filename_list}")

        # Save bundle file to the specified directory
        bundle_output_filepath = os.path.join(bundled_files_dir, f"bundle_{bundle_count}.txt")
        with open(bundle_output_filepath, "w", encoding="utf-8") as bundle_file:
            bundle_file.write(bundle_content)
        print(f"Bundle content saved to {bundle_output_filepath}")

        # Invoke the LLM chain and get the result
        result = llmchain.invoke({"file_content": bundle_content})

        llm_output_text = result.content # Access the 'content' attribute from the result object

        print("\n--- Raw LLM Result ---")
        print(llm_output_text)

        # Attempt to parse the LLM's table output into a DataFrame
        try:
            # Split the output into lines and clean them
            lines = llm_output_text.strip().split('\n')
            # Filter out empty lines and potential markdown code block fences (like '```')
            cleaned_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('```')]

            if len(cleaned_lines) < 2:
                print("LLM did not return enough lines to form a table.")
                continue

            # Find the header and separator lines more robustly
            header_line = ""
            separator_line = ""
            data_start_index = -1

            for idx, line in enumerate(cleaned_lines):
                if '|' in line and '---' not in line:  # This is likely the header line
                    header_line = line
                    if idx + 1 < len(cleaned_lines) and '---' in cleaned_lines[idx+1]: # The next line should be the separator
                        separator_line = cleaned_lines[idx+1] # This line is often '---|---|---'
                        data_start_index = idx + 2 # Data starts after header and separator
                        break

            if not header_line or not separator_line or data_start_index == -1:
                print("Could not identify table header or data start in LLM output.")
                continue

            # Extract column names from the header line
            # Remove leading/trailing '|' and split by '|', then strip spaces
            columns = [col.strip() for col in header_line.strip('|').split('|')]

            data = []
            for j in range(data_start_index, len(cleaned_lines)):
                current_line = cleaned_lines[j]
                if current_line.strip(): # Ensure the line is not empty
                    # Remove leading/trailing '|' and split by '|', then strip spaces
                    row_values = [val.strip() for val in current_line.strip('|').split('|')]

                    if len(row_values) == len(columns):
                        data.append(row_values)
                    else:
                        print(f"Skipping malformed row (column count mismatch): {current_line}")
                        print(f"Expected {len(columns)} columns, got {len(row_values)}")

            df = pd.DataFrame(data, columns=columns)

            # Save to CSV in the specified results directory
            output_csv_filename = os.path.join(results_files_dir, f"result_{bundle_count}.csv")
            df.to_csv(output_csv_filename, index=False, encoding='utf-8-sig', sep=SEPERATOR)
            print(f"\nResults saved to {output_csv_filename}")
            print("\n--- Extracted Data (DataFrame) ---")
            print(df.to_string(index=False))
        except Exception as e:
            print(f"Error parsing LLM output for bundle {bundle_count}: {e}")
            print("LLM output:\n", llm_output_text) # Print the raw LLM output for debugging
        # input("Press Enter to continue to the next bundle...")

# --- Main execution block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process several reports and extract information using an LLM.")
    parser.add_argument("prompt_file", nargs='?', help="Path to the file containing prompt instructions.")
    parser.add_argument("-i", "--input_folder", default="Input_Files", # Changed from -d to -i, and default from Haewon_Reports to Input_Files
                        help="Path to the directory containing pathology reports (default: Input_Files).")
    parser.add_argument("-s", "--bundle_size", type=int, default=10,
                        help="Number of reports to bundle together for processing (default: 10).")
    parser.add_argument("-b", "--bundled_folder", default="Bundled_Files",
                        help="Directory to save bundled text files (default: Bundled_Files).")
    parser.add_argument("-r", "--result_folder", default="Result_Files",
                        help="Directory to save result CSV files (default: Result_Files).")

    args = parser.parse_args()

    if not args.prompt_file:
        parser.print_help()
        print("\nError: Please provide a prompt file as the first argument.")
    else:
        try:
            # Read prompt instruction from the specified file
            dynamic_prompt_instruction = read_prompt_from_file(args.prompt_file)

            # Run the processing with the dynamic prompt and specified folders
            process_llm_parsing_reports(args.input_folder, args.bundle_size, # Passed args.input_folder
                                        dynamic_prompt_instruction, args.bundled_folder, args.result_folder)
        except (FileNotFoundError, IOError) as e:
            print(e)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")