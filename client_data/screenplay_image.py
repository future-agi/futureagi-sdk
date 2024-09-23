from ast import Break
import os
import pprint
import time
from fi.client import Client
from fi.client import ModelTypes, Environments
import time
from PIL import Image
import base64
from io import BytesIO

from fi.utils import generate_random_date

fi_client = Client(
    api_key="5ffab106598343a79720824d380632ce",
    secret_key="faf78735c36c459f8f6be81823950f9d",
)


def to_byte_image(image):
    

    if isinstance(image, str) and os.path.isfile(image):
        image = Image.open(image)
    
    print(image)
    # If image is in RGBA mode (has transparency), convert it to RGB (without alpha)
    if image.mode == "RGBA":
        image = image.convert("RGB")

    buffered = BytesIO()
    image.save(buffered, format="JPEG")

    # Get the byte data
    img_byte = buffered.getvalue()

    # Encode the byte data to base64
    img_base64 = base64.b64encode(img_byte).decode("utf-8")

    # Create the base64 string with the data URI scheme
    img_base64_str = f"data:image/jpeg;base64,{img_base64}"
    # img_base64_str = "data:image/jpeg;base64,{img_base64}"

    # Output the result
    return img_base64_str
sample_images=['toon-1.jpg']
description = """ 
Description: Wider shot of the bank interior, focusing on John and Sarah at the teller window, with other customers and security guards in the background.

Location: City Bank

Dress of John Reeves: gray wig, thick-rimmed glasses, ill-fitting tweed jacket, plain shirt, dark trousers

Dress of Sarah Thompson: professional blouse, name tag

Pose: John Reeves is tense, gripping briefcase, Sarah Thompson is hand hovering over alarm button

High angle Wide shot
"""
# for i in sample_images:

#     res = fi_client.log(
#         "Screenplay-Generated-Image",
#         ModelTypes.GENERATIVE_IMAGE,
#         Environments.PRODUCTION,
#         "v1",
#         #   str(uuid.uuid4()),
#         int(generate_random_date()),
#         {
#             "chat_history": [
#                 {
#                     "role": "user",

#                     "content": [
#                         {"type": "text", "text":description},
                        
#                     ],
#                 },
#                 {
#                     "role": "assistant",
#                     "content": [
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": to_byte_image(i)
#                             },
#                         }
#                     ],
#                 },
#             ]
#         },
#     ).result()
#     print(res.text)
#     break


    
sample_images=['toon-2.png','toon-3.jpg','toon-4.jpg','toon-5.png','toon-6.png','toon-7.png','toon-8.png']

for i in sample_images:

    res = fi_client.log(
        "Screenplay-Generated-Images-Check",
        ModelTypes.GENERATIVE_IMAGE,
        Environments.PRODUCTION,
        "v1",
        #   str(uuid.uuid4()),
        int(generate_random_date()),
        {
            "chat_history": [
                {
                    "role": "user",

                    "content": [
                        {"type": "text", "text":'Check that the image quality is high, with no visible defects. Ensure the character’s facial features, clothing, and physical appearance remain uniform throughout. Make sure the background or setting is consistently depicted across all images.'},
                        
                    ],
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": to_byte_image(i)
                            },
                        }
                    ],
                },
            ]
        },
    ).result()
    print(res.text)
    