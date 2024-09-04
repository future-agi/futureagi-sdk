import os
import time
from fi.client import Client
from fi.client import ModelTypes, Environments
import time
from PIL import Image
import base64
from io import BytesIO

fi_client = Client(
    api_key="5ffab106598343a79720824d380632ce",
    secret_key="faf78735c36c459f8f6be81823950f9d",
)
def to_byte_image(image):

    if (isinstance(image, str) and os.path.isfile(image)):
        image = Image.open(image)

    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    
    # Get the byte data
    img_byte = buffered.getvalue()
    
    # Encode the byte data to base64
    img_base64 = base64.b64encode(img_byte).decode('utf-8')
    
    # Create the base64 string with the data URI scheme
    img_base64_str = f"data:image/jpeg;base64,{img_base64}"
    
    # Output the result
    return img_base64_str



# Define the sequence of filenames
sequence = [
    "gar1_gen.jpg", "gar2_gen.jpg", "gar3_gen.jpg", "gar4_gen.jpg", "gar5_gen.jpg",
    "gar6_gen.jpg", "gar7_gen.jpg", "gar8_gen.jpg", "gar8_web_p.jpg", "gar9_gen.jpg",
    "gar9_web_l.jpg", "gar12_web_l.jpg", "gar13_web_h.jpg", "gar15_web_p.jpg",
    "gar17_web_p.jpg", "gar19_web_l.jpg", "gar22_web_l.jpg", "gar24_web_l.jpg"
]


instructions=['Catalogue photoshoot of A 25-year-old Brazilian male model., wearing T-Shirt with length Waist length sleeve length Short sleeves neckline Crew neck with lower garment culottes culottes, White shoes, Tokyo business district',
              'Catalogue photoshoot of A 28-year-old Italian male exudes elegance and sophistication, embodying the timeless charm of Mediterranean aesthetics., wearing T-shirt with length Hip length sleeve length Short neckline Crew neck with lower garment jeans jeans, White shoes, Tokyo business district',
              'Catalogue photoshoot of A 27-year-old American woman with a strikingly tall and lean physique, exuding confidence with her captivating blue eyes and flowing brunette hair., wearing T-shirt with length Waist length sleeve length Short sleeve neckline Crew neck with lower garment palazzo pants palazzo pants, White shoes, San Francisco café',
              'Catalogue photoshoot of A 27-year-old French woman with a captivating presence, blending elegance and modernity., wearing T-shirt with length Waist length sleeve length Short sleeves neckline Crew neck with lower garment skirt skirt, White shoes, Parisian sidewalk café',  
              'Catalogue photoshoot of A 27-year-old Italian woman with an impeccable sense of style, exuding elegance and grace., wearing T-shirt with length Hip length sleeve length Short sleeve neckline Crew neck with lower garment shorts shorts, White shoes, Seaside coffee shop',
              'Catalogue photoshoot of A 29-year-old French woman with an elegant and poised demeanor., wearing T-Shirt with length Hip length sleeve length Short Sleeve neckline Crew neck with lower garment shorts shorts, White shoes, Central Park bench',
              'Catalogue photoshoot of A 27-year-old Italian woman with an effortlessly chic style and a confident, modern aura., wearing T-shirt with length Waist length sleeve length Short sleeve neckline Crew neck with lower garment jeans jeans, White shoes, Parisian café terrace',
              'Catalogue photoshoot of A 25-year-old French female radiates elegance as she struts down the runway, her lithe frame draped in an avant-garde, asymmetrical silk gown that captures the essence of modern sophistication., wearing T-shirt with length Hip length sleeve length Short sleeves neckline V-neck with lower garment cargo pants cargo pants, White shoes, Bustling Tokyo market',
              'Catalogue photoshoot of A 27-year-old Italian woman with an elegant and poised demeanor., wearing T-shirt with length Waist length sleeve length Short sleeves neckline Crew neck with lower garment culottes culottes, White shoes, Central Park pond',
              'Catalogue photoshoot of A 25-year-old French woman with an elegant demeanor and striking features, suitable for high-fashion runways., wearing T-shirt with length Hip length sleeve length Short sleeves neckline V-neck with lower garment leggings leggings, White shoes, Cozy urban cafe',
              'Catalogue photoshoot of A 26-year-old Japanese female model with a sleek and modern look, exuding a blend of elegance and contemporary flair., wearing T-shirt with length Hip length sleeve length Short sleeves neckline Crew neck with lower garment cargo pants cargo pants, White shoes, Sunny beach boardwalk',
              'Catalogue photoshoot of An elegant 27-year-old French woman with impeccable poise and a captivating presence., wearing T-shirt with length Waist length sleeve length Short sleeve neckline Crew neck with lower garment skirt skirt, White shoes, downtown office lobby',
              'Catalogue photoshoot of A 28-year-old Italian woman with striking features and an elegant demeanor., wearing T-shirt with length Hip length sleeve length Short sleeves neckline Crew neck with lower garment cargo pants cargo pants, White shoes, Japanese tea garden',
              'Catalogue photoshoot of A 25-year-old Italian woman with an elegant presence and a confident demeanor., wearing Shirt with length Hip length sleeve length Long neckline Collared with lower garment cargo pants cargo pants, White shoes, Seaside coffee shop',
              
              'Catalogue photoshoot of A 25-year-old Italian woman with an effortlessly chic style., wearing Shirt with length Hip length sleeve length Short sleeves neckline Collared neck with lower garment skirt skirt, White shoes, Busy airport terminal',
              'Catalogue photoshoot of A 27-year-old Italian woman with a poised demeanor and a love for contemporary fashion., wearing Shirt with length Hip length sleeve length Long sleeves neckline Collared with lower garment leggings leggings, White shoes, Parisian coffee shop',
              'Catalogue photoshoot of A 25-year-old Japanese female with an elegant demeanor and striking features., wearing Shirt with length Hip length sleeve length Long sleeve neckline Collared with lower garment leggings leggings, White shoes, Tokyo night market',
              'Catalogue photoshoot of A 25-year-old Italian woman with an elegant appearance and a captivating presence., wearing Shirt with length Hip length sleeve length Long sleeves neckline Collared with lower garment palazzo pants palazzo pants, White shoes, Parisian coffee shop'
              ]

garment_images = [
    "Garment/gar1_gen.jpg", "Garment/gar2_gen.jpg", "Garment/gar3_gen.jpg", "Garment/gar4_gen.jpg", "Garment/gar5_gen.jpg",
    "Garment/gar6_gen.jpg", "Garment/gar7_gen.jpg", "Garment/gar8_gen.jpg", "Garment/gar8_web_p.jpg", "Garment/gar9_gen.jpg",
    "Garment/gar9_web_l.jpg", "Garment/gar12_web_l.jpg", "Garment/gar13_web_h.jpg", "Garment/gar15_web_p.jpg",
    "Garment/gar17_web_p.jpg", "Garment/gar19_web_l.jpg", "Garment/gar22_web_l.jpg", "Garment/gar24_web_l.jpg"
]


outputs_images = [
    "outputs/gar1_gen_output_100000.png", "outputs/gar2_gen_output_100000.png", "outputs/gar3_gen_output_100000.png", "outputs/gar4_gen_output_100000.png", "outputs/gar5_gen_output_100000.png",
    "outputs/gar6_gen_output_100000.png", "outputs/gar7_gen_output_100000.png", "outputs/gar8_gen_output_100000.png", "outputs/gar8_web_p_output_100000.png", "outputs/gar9_gen_output_100000.png",
    "outputs/gar9_web_l_output_100000.png", "outputs/gar12_web_l_output_100000.png", "outputs/gar13_web_h_output_100000.png", "outputs/gar15_web_p_output_100000.png",
    "outputs/gar17_web_p_output_100000.png", "outputs/gar19_web_l_output_100000.png", "outputs/gar22_web_l_output_100000.png", "outputs/gar24_web_l_output_100000.png"
]

base_humans_images=[
    "base-humans/gar1_gen_virtual_human.png", "base-humans/gar2_gen_virtual_human.png", "base-humans/gar3_gen_virtual_human.png", "base-humans/gar4_gen_virtual_human.png", "base-humans/gar5_gen_virtual_human.png",
    "base-humans/gar6_gen_virtual_human.png", "base-humans/gar7_gen_virtual_human.png", "base-humans/gar8_gen_virtual_human.png", "base-humans/gar8_web_p_virtual_human.png", "base-humans/gar9_gen_virtual_human.png",
    "base-humans/gar9_web_l_virtual_human.png", "base-humans/gar12_web_l_virtual_human.png", "base-humans/gar13_web_h_virtual_human.png", "base-humans/gar15_web_p_virtual_human.png",
    "base-humans/gar17_web_p_virtual_human.png", "base-humans/gar19_web_l_virtual_human.png", "base-humans/gar22_web_l_virtual_human.png", "base-humans/gar24_web_l_virtual_human.png"
]
counter=0
for i in instructions:
	fi_client.log(
	"drive_data_test_final",
	ModelTypes.GENERATIVE_IMAGE,
	Environments.PRODUCTION,
	"v1",
	#   str(uuid.uuid4()),
	int(time.time()),
	{
		"chat_history": [
			{
				"role": "user",
				"content": [
					{"type": "text", "text": i },
					{"type": "image_url", "image_url": {"url": to_byte_image(base_humans_images[counter])}},
     				{"type": "image_url", "image_url": {"url": to_byte_image(garment_images[counter])}},
				]
			},
			{
				"role": "assistant",
				"content": [
					{"type": "image_url", "image_url": {"url": to_byte_image(outputs_images[counter])}}
				]
			}
		]
	}
	).result()
	counter=counter+1
	
	

