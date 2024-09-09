import time
import pandas as pd

from fi.client import Client
from fi.utils import generate_random_date
from fi.utils.types import Environments, ModelTypes

# fi_client = Client(
#     uri="https://api.futureagi.com",
#     api_key="4cd0367544a6489ca4f1f3644b7c7acb",
#     secret_key="6aba50f4f186420588edce689c61c559",
# )
fi_client = Client(
    api_key="5ffab106598343a79720824d380632ce",
    secret_key="faf78735c36c459f8f6be81823950f9d",
)
import pandas as pd

# Read the CSV file using pandas
df = pd.read_csv('/Users/apple/Desktop/startegy.csv')  
df.columns

# Rename the 'ValuesStep1' column to 'strategic_priorities'
df = df.rename(columns={'ValuesStep1': 'strategic_priorities'})
df = df.rename(columns={'ValuesStep2': 'potential_alignment'})
# Drop rows where any of the values are NA
df = df.dropna()

print(len(df))

# Verify the column name change
print(df.columns)

PROMPT_TEMPLATE = '''
You are provided with strategic priorities for company A and value propositions for a company B.

Company A Strategic Priorities: {}
Company B Value Propositions: {}

Compare [Company A]'s strategic priorities with [Company B]'s value proposition. Highlight areas of potential alignment, considering:

How [Company B]'s offerings could support or accelerate [Company A]'s strategic goals
Potential synergies in target markets or customer bases
Complementary technologies or capabilities
Opportunities for innovation or market expansion

For each area of alignment, provide a brief explanation of how [Company B]'s value proposition could specifically address or enhance [Company A]'s strategic priorities.
Focus on the following aspects:

1. Ease of implementation
2. Potential return on investment
3. Time to market
4. Competitive advantage gained

This analysis will help identify the most promising areas for collaboration or partnership between [Company A] and [Company B], based on strategic alignment and mutual benefit."
'''

# Iterate through all rows from index 2 to the end
for index, row in df.iloc[11:15].iterrows():
    if row.get("potential_alignment")!='Did not find any initiatives related to your business.':
        response = fi_client.log(
            "startegy-chat",
            ModelTypes.GENERATIVE_LLM,
            Environments.PRODUCTION,
            "1.2",
            int(time.time()),
            {'chat_history':
            [{'role': 'user',
            'content': PROMPT_TEMPLATE.format(row.get("strategic_priorities"),row.get("strategic_priorities")),
            'variables': {
                'company_a_strategic_priorities': row.get("strategic_priorities"),
                'company_b_value_propositions': row.get("strategic_priorities")
                },
            'prompt_template': PROMPT_TEMPLATE},
            {'role': 'assistant',
            'content': row.get("potential_alignment")}]}
        ).result()
        print(response)