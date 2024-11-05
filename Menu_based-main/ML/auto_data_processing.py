import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
import os

class AutomatedDataProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
    
    # Step 1: Load Data
    def load_data(self):
        _, file_extension = os.path.splitext(self.file_path)
        if file_extension == '.csv':
            self.data = pd.read_csv(self.file_path)
        elif file_extension in ['.xls', '.xlsx']:
            self.data = pd.read_excel(self.file_path)
        else:
            raise ValueError("Unsupported file format")
        print("Data loaded successfully!")

    # Step 2: Clean Data
    def clean_data(self):
        # Remove duplicates
        self.data.drop_duplicates(inplace=True)
        
        # Handle missing values
        self.data.fillna(self.data.mean(), inplace=True)
        print("Data cleaned successfully!")

    # Step 3: Transform Data
    def transform_data(self):
        # Example: Standardize numeric columns
        numeric_cols = self.data.select_dtypes(include=['float64', 'int64']).columns
        scaler = StandardScaler()
        self.data[numeric_cols] = scaler.fit_transform(self.data[numeric_cols])
        
        # Example: Encode categorical columns
        categorical_cols = self.data.select_dtypes(include=['object']).columns
        encoder = LabelEncoder()
        for col in categorical_cols:
            self.data[col] = encoder.fit_transform(self.data[col])
        
        print("Data transformed successfully!")

    # Step 4: Analyze Data
    def analyze_data(self):
        # Example: Show basic statistics
        print("Dataset Statistics:\n", self.data.describe())

        # Example: Show data types and null counts
        print("\nData Information:")
        print(self.data.info())

    # Step 5: Save processed data
    def save_processed_data(self, output_file_path):
        self.data.to_csv(output_file_path, index=False)
        print(f"Processed data saved to {output_file_path}")

# Example usage
if __name__ == "__main__":
    # Path to the dataset file
    input_file = "marks.csv"  # Change this to your actual file path
    
    # Initialize the processor with the dataset
    processor = AutomatedDataProcessor(input_file)
    
    # Automating the processing steps
    processor.load_data()
    processor.clean_data()
    processor.transform_data()
    processor.analyze_data()
    
    # Save processed data
    output_file = "processed_dataset.csv"
    processor.save_processed_data(output_file)
