import time
import pandas as pd

from fi.client import Client
from fi.utils.types import Environments, ModelTypes

def convert_excel_to_desired_format(input_file, output_file):
    # Read the Excel file
    df = pd.read_csv(input_file)

    # Initialize an empty DataFrame to hold the processed data
    processed_data = []
    
    print("Available columns:", df.columns.tolist())
    
    # Define the columns you want in the output
    output_columns = ['name', 'value_proposition', 'combined_posts', 'prompt', 'opener']

    # Iterate through each row in the original DataFrame
    for _, row in df.head(1).iterrows():
        # Iterate over all prompt-opener pairs
        print(row['name'])
        for i in range(1, 18):  # Assuming there are 17 prompts and openers
            prompt_col = f'prompt_{i}'
            opener_col = f'opener_{i}'

            if prompt_col in df.columns and opener_col in df.columns:
                # Create a new row with the desired columns
                processed_row = {
                    'name': row['name'],
                    'value_proposition': row['value_proposition'],
                    'combined_posts': row['combined_posts'],
                    'prompt': row[prompt_col].split('Posts')[0],
                    'opener': row[opener_col]
                }
                # Append to the list
                processed_data.append(processed_row)

    print(processed_data,"processed_data")
    # Convert the list to a DataFrame
    processed_df = pd.DataFrame(processed_data, columns=output_columns)

    # Save the processed DataFrame to a new Excel file
    processed_df.to_csv(output_file, index=False)

# Example usage
input_file = '/Users/apple/Desktop/rows.csv'  # Replace with your actual file path
output_file = 'output_file.csv'  # Replace with your desired output file path
convert_excel_to_desired_format(input_file, output_file)
fi_client = Client(
    api_key="5ffab106598343a79720824d380632ce",
    secret_key="faf78735c36c459f8f6be81823950f9d",
)

df = pd.read_csv('output_file.csv')
print("Available columns:", df.columns.tolist())
for _, row in df.iloc[8:9].iterrows():
    variables = {col: row[col] for col in df.columns if col not in ['combined_posts', 'opener','prompt']}
    
    response = fi_client.log(
        "ptemp-test-2",
        ModelTypes.GENERATIVE_LLM,
        Environments.PRODUCTION,
        "v2",
        int(time.time()),
        {
            "chat_history": [
                {"role": "user", "content": row['combined_posts'],"variables" : variables , "prompt_template" : row['prompt']},
                {"role": "assistant",
                "content": row['opener']}
            ],
        }
    ).result()