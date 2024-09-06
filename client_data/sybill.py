import time
import pandas as pd

from fi.client import Client
from fi.utils.types import Environments, ModelTypes


prompt = """ 
You are given the conversation details of the meeting and a background context.


Conversation: {}
Context: {}
Sample Email: {}

You have to generate a follow up reply email using the conversation details , context and a sample email template given to you.
"""
def convert_excel_to_desired_format(input_file, output_file):
    # Read the Excel file
    df = pd.read_csv(input_file)

    # Initialize an empty DataFrame to hold the processed data
    processed_data = []
    
    print("Available columns:", df.columns.tolist())
    
    # Define the columns you want in the output
    output_columns = ['conversation', 'context', 'user_email', 'ai_email']

    # Iterate through each row in the original DataFrame
    for _, row in df.iterrows():
        # Iterate over all prompt-opener pairs        
        processed_row = {
            'conversation': row['conversation'],
            'context': row['context'],
            'user_email': row['user_email'],
            'ai_email': row['ai_email'],
        }
        # Append to the list
        processed_data.append(processed_row)

    print(processed_data,"processed_data")
    # Convert the list to a DataFrame
    processed_df = pd.DataFrame(processed_data, columns=output_columns)

    # Save the processed DataFrame to a new Excel file
    processed_df.to_csv(output_file, index=False)

# Example usage
input_file = '/Users/apple/Downloads/test_upload.csv'  # Replace with your actual file path
output_file = 'output_file.csv'  # Replace with your desired output file path
convert_excel_to_desired_format(input_file, output_file)
#getayana
# fi_client = Client(
#     uri="https://api.futureagi.com",
#     api_key="14bce73eb2684110b4fa9dfdfc7df5b1",
#     secret_key="6d52d11ce1914384a5b1dbea3bd94451",
# ) 

# fi_client = Client(
#     api_key="5ffab106598343a79720824d380632ce",
#     secret_key="faf78735c36c459f8f6be81823950f9d",
# )

fi_client = Client(
    uri="https://api.futureagi.com",
    api_key="4cd0367544a6489ca4f1f3644b7c7acb",
    secret_key="6aba50f4f186420588edce689c61c559",
)
df = pd.read_csv('output_file.csv')
print("Available columns:", df.columns.tolist())
for _, row in df.iterrows():
    
    response = fi_client.log(
        "AIBrilliance",
        ModelTypes.GENERATIVE_LLM,
        Environments.PRODUCTION,
        "v2",
        int(time.time()),
        {
            "chat_history": [
                {"role": "user", "content":  prompt.format(row['conversation'],row['context'],row['user_email'])},
                {"role": "assistant",
                "content": row['ai_email']}
            ],
        }
    ).result()
    print(response)