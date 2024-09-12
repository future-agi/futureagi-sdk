import time
import pandas as pd

from fi.client import Client
from fi.utils import generate_random_date
from fi.utils.types import Environments, ModelTypes

# fi_client = Client(
#     uri="https://api.futureagi.com",
#     api_key="6717c567d39d465b94cca6ae80631ac7",
#     secret_key="2b231177673648a1818eac26e791c57e",
# )
fi_client = Client(
    api_key="5ffab106598343a79720824d380632ce",
    secret_key="faf78735c36c459f8f6be81823950f9d",
)


email_data = [{
    "role": "user",
    "content": "Can you please explain the keypoints in this {}",
    "prompt_template": "Can you please explain the keypoints in this {email}",
    "variables": {"email": "Hello team, Please review the attached project plan and provide your comments by end of day tomorrow."}
},
{
    "role": "assistant",
    "content": "The email is requesting the team to review an attached project plan and submit their comments by the end of the day tomorrow."
},
{
    "role": "user",
    "content": "Can you please explain the keypoints in this {}",
    "prompt_template": "Can you please explain the keypoints in this {email}",
    "variables": {"email": "Hi Jane, The deadline for the client report is now next Wednesday. Please adjust your schedule accordingly."}
},
{
    "role": "assistant",
    "content": "The email informs Jane that the deadline for the client report has been moved to next Wednesday and asks her to adjust her schedule."
},
{
    "role": "user",
    "content": "Can you please explain the keypoints in this {}",
    "prompt_template": "Can you please explain the keypoints in this {email}",
    "variables": {"email": "Dear Alex, Please prepare the budget review document and have it ready for our meeting on Friday."}
},
{
    "role": "assistant",
    "content": "The email asks Alex to prepare the budget review document and have it ready for a meeting scheduled on Friday."
},
{
    "role": "user",
    "content": "Can you please explain the keypoints in this {}",
    "prompt_template": "Can you please explain the keypoints in this {email}",
    "variables": {"email": "Hi Sam, I have updated the project timeline. Please find the new dates in the attached file and let me know if there are any concerns."}
},
{
    "role": "assistant",
    "content": "The email informs Sam that the project timeline has been updated and asks him to review the new dates in the attached file and report any concerns."
},
{
    "role": "user",
    "content": "Can you please explain the keypoints in this {}",
    "prompt_template": "Can you please explain the keypoints in this {email}",
    "variables": {"email": "Hello Mary, Our quarterly sales meeting is rescheduled to next Monday. Please confirm your attendance."}
},
{
    "role": "assistant",
    "content": "The email notifies Mary that the quarterly sales meeting has been rescheduled to next Monday and asks her to confirm her attendance."
},
{
    "role": "user",
    "content": "Can you please explain the keypoints in this {}",
    "prompt_template": "Can you please explain the keypoints in this {email}",
    "variables": {"email": "Hi John, We need to finalize the contract by the end of this week. Please review the attached draft and send your comments."}
},
{
    "role": "assistant",
    "content": "The email requests John to finalize the contract by the end of the week and to review the attached draft and send comments."
},
{
    "role": "user",
    "content": "Can you please explain the keypoints in this {}",
    "prompt_template": "Can you please explain the keypoints in this {email}",
    "variables": {"email": "Dear Lisa, The client feedback has been received and needs to be incorporated into the design. Please review the feedback and update the design accordingly."}
},
{
    "role": "assistant",
    "content": "The email informs Lisa that client feedback has been received and needs to be incorporated into the design. She is asked to review the feedback and update the design accordingly."
},
{
    "role": "user",
    "content": "Can you please explain the keypoints in this {}",
    "prompt_template": "Can you please explain the keypoints in this {email}",
    "variables": {"email": "Hi David, Please ensure all team members have completed their performance reviews by the end of this week."}
},
{
    "role": "assistant",
    "content": "The email asks David to make sure that all team members complete their performance reviews by the end of the week."
},
{
    "role": "user",
    "content": "Can you please explain the keypoints in this {}",
    "prompt_template": "Can you please explain the keypoints in this {email}",
    "variables": {"email": "Hello Anna, The system upgrade will take place over the weekend. Ensure that all important data is backed up before Friday evening."}
},
{
    "role": "assistant",
    "content": "The email informs Anna about a system upgrade happening over the weekend and instructs her to back up all important data before Friday evening."
}]


concept = [
        {
            "role": "user",
         "content": "Can you please explain photosynthesis",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "photosynthesis"},
     },
     {
         "role": "assistant",
         "content": "Photosynthesis is how plants make food using sunlight, water, and carbon dioxide.",
     },
     {
         "role": "user",
         "content": "Can you please explain the theory of relativity",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "theory of relativity"},
     },
     {
         "role": "assistant",
         "content": "The theory of relativity, proposed by Albert Einstein, consists of the special and general theories which describe the relationship between space, time, and gravity.",
     },
     {
         "role": "user",
         "content": "Can you please explain Newton's laws of motion",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "Newton's laws of motion"},
     },
     {
         "role": "assistant",
         "content": "Newton's laws of motion describe the relationship between the motion of an object and the forces acting on it. They include: 1) An object in motion stays in motion unless acted upon by an external force. 2) The force on an object is equal to its mass times its acceleration. 3) For every action, there is an equal and opposite reaction.",
     },
     {
         "role": "user",
         "content": "Can you please explain market equilibrium",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "market equilibrium"},
     },
     {
         "role": "assistant",
         "content": "Market equilibrium is the state where the quantity of a good demanded by consumers equals the quantity supplied by producers, resulting in a stable market price.",
     },
     {
         "role": "user",
         "content": "Can you please explain genetic inheritance",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "genetic inheritance"},
     },
     {
         "role": "assistant",
         "content": "Genetic inheritance is the process by which genetic information is passed from parents to offspring through genes, determining inherited traits and characteristics.",
     },
     {
         "role": "user",
         "content": "Can you please explain quantum mechanics",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "quantum mechanics"},
     },
     {
         "role": "assistant",
         "content": "Quantum mechanics is a fundamental theory in physics that describes the behavior of particles at the atomic and subatomic levels, including phenomena such as wave-particle duality and quantization.",
     },
     {
         "role": "user",
         "content": "Can you please explain the theory of evolution",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "theory of evolution"},
     },
     {
         "role": "assistant",
         "content": "The theory of evolution by natural selection, proposed by Charles Darwin, suggests that organisms evolve over time through the selection of traits that enhance survival and reproduction.",
     },
     {
         "role": "user",
         "content": "Can you please explain social contract theory",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "social contract theory"},
     },
     {
         "role": "assistant",
         "content": "Social contract theory posits that individuals agree to form societies and abide by collective rules in exchange for protection and benefits, forming the basis for political and moral legitimacy.",
     },
     {
         "role": "user",
         "content": "Can you please explain cognitive development",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "cognitive development"},
     },
     {
         "role": "assistant",
         "content": "Cognitive development refers to the progression of mental abilities and processes such as thinking, learning, and problem-solving from infancy through adulthood.",
     },
     {
         "role": "user",
         "content": "Can you please explain the cell division process",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "cell division process"},
     },
     {
         "role": "assistant",
         "content": "Cell division is the process by which a cell divides to produce two or more daughter cells. It includes processes such as mitosis (for growth and repair) and meiosis (for producing gametes).",
     },
     {
         "role": "user",
         "content": "Can you please explain the principle of utility",
         "prompt_template": "Can you please explain $concept$",
         "variables": {"concept": "principle of utility"},
     },
     {
         "role": "assistant",
         "content": "The principle of utility is an ethical theory which suggests that the best action is the one that maximizes overall happiness or well-being for the greatest number of people.",
     }
     ]


for row in range(0, len(email_data), 2):
        
    
    
    response = fi_client.log(
        "Prompt-Template-final-1",
        ModelTypes.GENERATIVE_LLM,
        Environments.PRODUCTION,
        "v2",
        int(generate_random_date()),
        {
            "chat_history": [
                {"role": "user", "content":  email_data[row]['content'].format(email_data[row]['variables']['email'])
                 ,'variables': email_data[row]['variables'],
            'prompt_template': email_data[row]['prompt_template']},
                
                {"role": "assistant",
                "content": email_data[row+1]['content']}
            ],
        }
    ).result()
    print(response)
    
    # break