import pandas as pd

class DataProcessor:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file

    def process_data(self):
        try:
            df = pd.read_csv(self.input_file)
            # Perform data processing logic here
            processed_df = df.copy()
            processed_df['processed_column'] = processed_df['original_column'] * 2
            processed_df.to_csv(self.output_file, index=False)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error processing data: {e}")
