from fi.client import Client
from fi.utils import generate_random_date
from fi.utils.types import Environments, ModelTypes


chunk_input_1="""
The bustling kitchen of Le Petit Jardin was a stark contrast to the refined dining room where Anton Beaumont sat, his silver-streaked hair neatly combed and his crisp white shirt tucked into tailored charcoal trousers. As the most feared food critic in Paris, his presence sent a ripple of anxiety through the restaurant staff. Anton's pen hovered over his notepad, ready to deliver another scathing review. "Monsieur, your appetizer," the waiter announced, placing a delicate plate before him. Anton eyed the dish skeptically – a simple arrangement of roasted vegetables drizzled with a golden sauce. He raised an eyebrow, unimpressed by its humble appearance. With a sigh, he lifted his fork and took a reluctant bite. The moment the morsel touched his tongue, Anton's world shifted. The familiar bitterness that had clouded his palate for years suddenly dissipated. His eyes widened as a flood of memories washed over him – summer afternoons in his grandmother's garden, the earthy scent of freshly pulled carrots, and the warmth of her weathered hands as she taught him to cook. Anton's notepad slipped from his fingers, clattering to the floor. The other diners turned to stare, but he was lost in a sensory journey. Each bite transported him further into his past, to a time before cynicism had hardened his heart. He could almost hear his grandmother's laughter, feel the sun on his face as they picked herbs together. In the kitchen, young Chef Amélie Rousseau peeked through the swinging doors, her chef's whites splattered with sauce and her curly hair escaping from beneath her toque. She watched the notorious critic with bated breath, unaware that her simple dish – inspired by her own childhood memories – was unraveling years of Anton's carefully constructed walls. As Anton finished the last bite, he found himself fighting back tears. The waiter approached cautiously, unsure how to interpret the critic's unusual behavior. "Is everythting alright, Monsieur?" he asked tentatively. Anton looked up, his eyes glistening. "It's... perfect," he whispered, his voice thick with emotion.
"""
chunk_input_2="""
Please, I must speak with the chef." Amélie emerged from the kitchen, wiping her hands nervously on her apron. She approached Anton's table, bracing herself for criticism. Instead, Anton stood and clasped her hands in his. "My dear," he said, his voice trembling, "you have reminded me of why I fell in love with food in the first place. Thank you." The restaurant fell silent, the other diners and staff frozen in disbelief. Amélie's eyes widened, a blush creeping across her cheeks. "Monsieur, I... I don't know what to say," she stammered. Anton smiled, a genuine warmth spreading across his face for the first time in years. "Say nothing. Just promise me you'll never stop cooking with your heart." As he left the restaurant that night, Anton tore up his notes. Instead of his usual caustic critique, he wrote a glowing review that would change both his and Amélie's lives forever. The bitter critic had rediscovered the sweet taste of nostalgia, and with it, a renewed passion for the culinary world he had once loved so dearly.
"""
chunk_output_1=["""
{
    "panels": [
        {
            "description": "A bustling kitchen with chefs and staff working frantically. In the foreground, Chef Amélie Rousseau is plating a dish of roasted vegetables.",
            "location": "Kitchen of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Chef Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "focused, slightly anxious",
                    "pose": "bending over a plate, carefully arranging vegetables"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Eye-level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Anton Beaumont sitting alone at a table in an elegant dining room, looking stern and critical.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "skeptical, slightly annoyed",
                    "pose": "sitting upright, pen hovering over notepad"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Monsieur, your appetizer.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Slightly above eye-level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Close-up of the plate of roasted vegetables with golden sauce, placed in front of Anton.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": null,
            "dialogues": null,
            "cameraAngle": "Overhead",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Anton taking a bite of the dish, his eyes widening in surprise.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "shocked, enlightened",
                    "pose": "fork raised to mouth, eyes wide"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Eye-level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "A flashback scene showing young Anton in his grandmother's garden, surrounded by vegetables and herbs.",
            "location": "Grandmother's garden",
            "timeOfDay": "Sunny afternoon",
            "characters": [
                {
                    "name": "Young Anton",
                    "dress": "simple t-shirt, shorts",
                    "expression": "joyful, curious",
                    "pose": "kneeling in the garden, holding a carrot"
                },
                {
                    "name": "Grandmother",
                    "dress": "floral print dress, gardening apron, sun hat",
                    "expression": "loving, patient",
                    "pose": "bending down, teaching Anton"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Eye-level",
            "cameraShot": "Wide shot"
        },
        {
            "description": "Back in the restaurant, Anton's notepad clattering to the floor, other diners turning to look.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "overwhelmed, emotional",
                    "pose": "hands trembling, notepad falling"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Low angle",
            "cameraShot": "Wide shot"
        },
        {
            "description": "Split panel: Top half shows Anton lost in his sensory journey. Bottom half shows Chef Amélie peeking through the kitchen doors.",
            "location": "Dining room and Kitchen of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "nostalgic, moved",
                    "pose": "eyes closed, fork midway to mouth"
                },
                {
                    "name": "Chef Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "anxious, hopeful",
                    "pose": "peeking through kitchen doors"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Eye-level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Anton finishing the last bite, fighting back tears.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, eyes glistening",
                    "pose": "putting down fork, wiping corner of eye"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Eye-level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Waiter approaching Anton's table cautiously.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Waiter",
                    "dress": "black vest, white dress shirt, black bow tie, black trousers",
                    "expression": "concerned, uncertain",
                    "pose": "leaning slightly towards Anton"
                },
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, overwhelmed",
                    "pose": "looking up at waiter"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Is everything alright, Monsieur?",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye-level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Close-up of Anton's face as he responds to the waiter.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "deeply moved, eyes glistening",
                    "pose": "looking up, slight smile"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "It's... perfect.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Slightly low angle",
            "cameraShot": "Close up shot"
        }
    ]
}
""",
""" 
{
    "panels": [
        {
            "description": "A bustling kitchen with chefs and staff working frantically. In the foreground, we see the back of Chef Amélie Rousseau as she puts the finishing touches on a plate of roasted vegetables.",
            "location": "Kitchen of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "focused, determined",
                    "pose": "leaning over a plate, carefully drizzling sauce"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Over-the-shoulder shot",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Anton Beaumont sits alone at a table in the elegant dining room, his notepad and pen ready. He looks stern and expectant.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "stern, critical",
                    "pose": "sitting upright, pen poised over notepad"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Eye level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "A waiter presents the appetizer to Anton, who looks at it skeptically.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "skeptical, unimpressed",
                    "pose": "leaning slightly back, eyebrow raised"
                },
                {
                    "name": "Waiter",
                    "dress": "black suit, white shirt, black bow tie",
                    "expression": "polite, slightly nervous",
                    "pose": "bending slightly, presenting the plate"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Monsieur, your appetizer.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Close-up of the plate with roasted vegetables drizzled with golden sauce.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [],
            "dialogues": [],
            "cameraAngle": "Top-down view",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Anton takes a bite of the appetizer, his eyes widening in surprise.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "shocked, enlightened",
                    "pose": "fork raised to mouth, eyes wide"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Eye level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "A montage of Anton's memories: his grandmother's garden, fresh carrots, and her hands teaching him to cook.",
            "location": "Grandmother's garden (memory)",
            "timeOfDay": "Sunny afternoon",
            "characters": [
                {
                    "name": "Young Anton",
                    "dress": "simple t-shirt, shorts",
                    "expression": "happy, curious",
                    "pose": "learning to cook with grandmother"
                },
                {
                    "name": "Grandmother",
                    "dress": "floral apron, simple dress",
                    "expression": "loving, patient",
                    "pose": "teaching Anton to cook"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Various angles",
            "cameraShot": "Wide shot"
        },
        {
            "description": "Back in the restaurant, Anton's notepad slips from his fingers and clatters to the floor. Other diners turn to look.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "overwhelmed, emotional",
                    "pose": "hands slightly shaking, notepad falling"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Low angle",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Chef Amélie peeks through the kitchen doors, watching Anton's reaction anxiously.",
            "location": "Kitchen doorway of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "anxious, hopeful",
                    "pose": "peeking through partially open door"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Eye level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Anton finishes the last bite, visibly moved and fighting back tears.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, teary-eyed",
                    "pose": "setting down fork, hand slightly trembling"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Eye level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "The waiter approaches Anton cautiously, concerned by his unusual behavior.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, overwhelmed",
                    "pose": "looking up at waiter, eyes glistening"
                },
                {
                    "name": "Waiter",
                    "dress": "black suit, white shirt, black bow tie",
                    "expression": "concerned, cautious",
                    "pose": "leaning slightly towards Anton"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Is everything alright, Monsieur?",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Close-up of Anton's face as he responds to the waiter, his expression transformed from cynicism to wonder.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "moved, wonder-struck",
                    "pose": "looking up, eyes glistening"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "It's... perfect.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye level",
            "cameraShot": "Close up shot"
        }
    ]
}
""",
""" 
{
    "panels": [
        {
            "description": "Anton Beaumont sits alone at a table in the refined dining room of Le Petit Jardin. The room is elegantly decorated with soft lighting and tasteful artwork.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "stern, critical",
                    "pose": "sitting upright, pen hovering over notepad"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "The most feared food critic in Paris, ready to deliver another scathing review.",
                    "dialogue_type": "NARRATION"
                }
            ],
            "cameraAngle": "Eye-level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "A waiter approaches Anton's table, carrying a delicate plate with an appetizer.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "skeptical",
                    "pose": "leaning back slightly"
                },
                {
                    "name": "Waiter",
                    "dress": "black and white waiter uniform",
                    "expression": "polite, slightly nervous",
                    "pose": "bending slightly to place the plate"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Monsieur, your appetizer.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Slightly elevated",
            "cameraShot": "Wide shot"
        },
        {
            "description": "Close-up of the appetizer plate, showing a simple arrangement of roasted vegetables drizzled with a golden sauce.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": null,
            "dialogues": null,
            "cameraAngle": "Overhead",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Anton takes a bite of the appetizer, his expression changing from skepticism to surprise.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "surprised, eyes widening",
                    "pose": "fork raised to mouth"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "The moment the morsel touched his tongue, Anton's world shifted.",
                    "dialogue_type": "NARRATION"
                }
            ],
            "cameraAngle": "Eye-level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "A montage of Anton's memories: his grandmother's garden, freshly pulled carrots, and his grandmother's hands.",
            "location": "Grandmother's garden (memory)",
            "timeOfDay": "Sunny afternoon",
            "characters": [
                {
                    "name": "Young Anton",
                    "dress": "casual children's summer clothes",
                    "expression": "joyful",
                    "pose": "helping in the garden"
                },
                {
                    "name": "Grandmother",
                    "dress": "simple floral dress, gardening apron",
                    "expression": "loving",
                    "pose": "teaching young Anton"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Various angles",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Back in the restaurant, Anton's notepad slips from his fingers and clatters to the floor. Other diners turn to look.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "lost in thought, emotional",
                    "pose": "hands slightly trembling"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Low angle",
            "cameraShot": "Wide shot"
        },
        {
            "description": "In the kitchen, Chef Am\u00e9lie Rousseau peeks through the swinging doors, watching Anton's reaction.",
            "location": "Le Petit Jardin restaurant kitchen",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Chef Am\u00e9lie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, toque",
                    "expression": "anxious, hopeful",
                    "pose": "peeking through kitchen doors"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Over-the-shoulder",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Anton finishes the last bite of the appetizer, visibly moved and fighting back tears.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, eyes glistening",
                    "pose": "lowering fork, wiping corner of eye"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Eye-level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "The waiter approaches Anton's table cautiously, concerned by the critic's unusual behavior.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "overwhelmed with emotion",
                    "pose": "looking up at waiter"
                },
                {
                    "name": "Waiter",
                    "dress": "black and white waiter uniform",
                    "expression": "concerned, curious",
                    "pose": "leaning slightly towards Anton"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Is everything alright, Monsieur?",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye-level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Close-up of Anton's face as he responds to the waiter, tears in his eyes and a soft smile on his lips.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, smiling softly",
                    "pose": "looking up at waiter"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "It's... perfect.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Slightly low angle",
            "cameraShot": "Close up shot"
        }
    ]
}
"""
    
]

chunk_output_2=[
    
    """
    {
    "panels": [
        {
            "description": "Anton standing up from his table, clasping Chef Amélie's hands in his. Other diners and staff in the background are frozen in surprise.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, eyes glistening",
                    "pose": "standing, holding Amélie's hands"
                },
                {
                    "name": "Chef Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "surprised, nervous",
                    "pose": "hands being held by Anton"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "My dear, you have reminded me of why I fell in love with food in the first place. Thank you.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye-level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Close-up of Amélie's face, showing her reaction to Anton's words.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Chef Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "shocked, blushing",
                    "pose": "eyes widened"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Monsieur, I... I don't know what to say.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Slightly low angle",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Anton smiling warmly at Amélie, the restaurant still silent in the background.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "warm, genuine smile",
                    "pose": "looking directly at Amélie"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Say nothing. Just promise me you'll never stop cooking with your heart.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye-level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Anton leaving the restaurant, silhouetted in the doorway.",
            "location": "Entrance of Le Petit Jardin",
            "timeOfDay": "Night",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "contemplative",
                    "pose": "walking through the doorway"
                }
            ],
            "dialogues": null,
            "cameraAngle": "From inside the restaurant",
            "cameraShot": "Long shot"
        },
        {
            "description": "Anton tearing up his notes outside the restaurant.",
            "location": "Street outside Le Petit Jardin",
            "timeOfDay": "Night",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "determined, liberated",
                    "pose": "hands tearing paper"
                }
            ],
            "dialogues": null,
            "cameraAngle": "Eye-level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Split panel: Left side shows Anton writing at his desk. Right side shows Amélie cooking in her kitchen, both looking inspired.",
            "location": "Anton's study / Le Petit Jardin kitchen",
            "timeOfDay": "Night",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "casual sweater, comfortable pants",
                    "expression": "focused, inspired",
                    "pose": "writing at desk"
                },
                {
                    "name": "Chef Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "confident, passionate",
                    "pose": "cooking at stove"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "The bitter critic had rediscovered the sweet taste of nostalgia, and with it, a renewed passion for the culinary world he had once loved so dearly.",
                    "dialogue_type": "NARRATION"
                }
            ],
            "cameraAngle": "Eye-level",
            "cameraShot": "Mid body shot"
        }
    ]
}
    """,
    """ 
    
{
    "panels": [
        {
            "description": "Anton stands up from his table, his face filled with emotion. He's addressing the waiter who looks surprised.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, earnest",
                    "pose": "standing, gesturing towards the kitchen"
                },
                {
                    "name": "Waiter",
                    "dress": "black suit, white shirt, black bow tie",
                    "expression": "surprised",
                    "pose": "standing attentively"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Please, I must speak with the chef.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Amélie emerges from the kitchen, looking nervous as she approaches Anton's table.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "nervous, apprehensive",
                    "pose": "walking towards Anton's table, wiping hands on apron"
                },
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, eager",
                    "pose": "standing, waiting for Amélie"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Eye level",
            "cameraShot": "Wide shot"
        },
        {
            "description": "Anton clasps Amélie's hands in his, his face full of genuine emotion.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "moved, grateful",
                    "pose": "holding Amélie's hands"
                },
                {
                    "name": "Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "surprised, touched",
                    "pose": "hands clasped by Anton"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "My dear, you have reminded me of why I fell in love with food in the first place. Thank you.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "The entire restaurant is silent, with diners and staff frozen in disbelief.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Diners",
                    "dress": "various elegant evening wear",
                    "expression": "shocked, curious",
                    "pose": "paused mid-action, staring at Anton and Amélie"
                },
                {
                    "name": "Staff",
                    "dress": "black suits, white shirts, black bow ties",
                    "expression": "amazed, frozen",
                    "pose": "standing still, watching the scene"
                }
            ],
            "dialogues": [],
            "cameraAngle": "High angle",
            "cameraShot": "Wide shot"
        },
        {
            "description": "Close-up of Amélie's face, blushing and stammering in response to Anton's words.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "blushing, overwhelmed",
                    "pose": "looking up at Anton, lips parted in speech"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Monsieur, I... I don't know what to say.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Anton smiles warmly at Amélie, his face transformed by genuine happiness.",
            "location": "Dining room of Le Petit Jardin",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "warm, genuinely happy",
                    "pose": "smiling at Amélie"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Say nothing. Just promise me you'll never stop cooking with your heart.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Anton leaves the restaurant, pausing at the door to look back with a smile.",
            "location": "Entrance of Le Petit Jardin",
            "timeOfDay": "Night",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "content, reflective",
                    "pose": "standing at the door, turning back to look inside"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Eye level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Anton sits at his desk at home, tearing up his original notes.",
            "location": "Anton's home office",
            "timeOfDay": "Late night",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "determined, inspired",
                    "pose": "sitting at desk, tearing paper"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Eye level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Close-up of Anton's hands writing a glowing review, his face visible in the background.",
            "location": "Anton's home office",
            "timeOfDay": "Late night",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "focused, passionate",
                    "pose": "writing intensely"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "The bitter critic had rediscovered the sweet taste of nostalgia, and with it, a renewed passion for the culinary world he had once loved so dearly.",
                    "dialogue_type": "NARRATION"
                }
            ],
            "cameraAngle": "Top-down view",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Split panel showing Amélie in her kitchen and Anton at his desk, both looking hopeful and inspired.",
            "location": "Le Petit Jardin kitchen / Anton's home office",
            "timeOfDay": "Next day",
            "characters": [
                {
                    "name": "Amélie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, white apron, chef's toque",
                    "expression": "hopeful, inspired",
                    "pose": "cooking with enthusiasm"
                },
                {
                    "name": "Anton Beaumont",
                    "dress": "casual button-up shirt, comfortable trousers",
                    "expression": "content, inspired",
                    "pose": "reading his published review in a newspaper"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Eye level",
            "cameraShot": "Wide shot"
        }
    ]
}
    """,
    """ 
    {
    "panels": [
        {
            "description": "Anton stands up from his table, his face filled with emotion as he addresses the waiter.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, earnest",
                    "pose": "standing, leaning towards the waiter"
                },
                {
                    "name": "Waiter",
                    "dress": "black and white waiter uniform",
                    "expression": "surprised",
                    "pose": "standing attentively"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Please, I must speak with the chef.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye-level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Chef Am\u00e9lie emerges from the kitchen, looking nervous as she approaches Anton's table.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Chef Am\u00e9lie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, toque, apron",
                    "expression": "nervous, apprehensive",
                    "pose": "walking towards Anton's table, wiping hands on apron"
                },
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "emotional, eager",
                    "pose": "standing, watching Am\u00e9lie approach"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Slightly elevated",
            "cameraShot": "Wide shot"
        },
        {
            "description": "Anton clasps Am\u00e9lie's hands in his, his face filled with gratitude and emotion.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "grateful, emotional",
                    "pose": "holding Am\u00e9lie's hands"
                },
                {
                    "name": "Chef Am\u00e9lie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, toque, apron",
                    "expression": "surprised, confused",
                    "pose": "hands clasped by Anton"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "My dear, you have reminded me of why I fell in love with food in the first place. Thank you.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye-level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "The restaurant falls silent, with other diners and staff frozen in disbelief.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Restaurant Patrons",
                    "dress": "various elegant evening wear",
                    "expression": "shocked, surprised",
                    "pose": "frozen mid-action"
                },
                {
                    "name": "Restaurant Staff",
                    "dress": "black and white waiter uniforms",
                    "expression": "astonished",
                    "pose": "paused in their tasks"
                }
            ],
            "dialogues": [],
            "cameraAngle": "High angle",
            "cameraShot": "Wide shot"
        },
        {
            "description": "Close-up of Am\u00e9lie's face, showing her widened eyes and blushing cheeks.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Chef Am\u00e9lie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, toque, apron",
                    "expression": "blushing, eyes widened in surprise",
                    "pose": "facing Anton"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Monsieur, I... I don't know what to say.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Eye-level",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Anton smiles warmly at Am\u00e9lie, his face softened with genuine emotion.",
            "location": "Le Petit Jardin restaurant dining room",
            "timeOfDay": "Evening",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "warm smile, eyes crinkled with joy",
                    "pose": "facing Am\u00e9lie"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Say nothing. Just promise me you'll never stop cooking with your heart.",
                    "dialogue_type": "DIALOGUE"
                }
            ],
            "cameraAngle": "Slightly low angle",
            "cameraShot": "Close up shot"
        },
        {
            "description": "Anton leaves the restaurant, pausing at the door to look back with a smile.",
            "location": "Le Petit Jardin restaurant entrance",
            "timeOfDay": "Night",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "content, reflective",
                    "pose": "standing at the door, looking back"
                }
            ],
            "dialogues": [],
            "cameraAngle": "Eye-level",
            "cameraShot": "Mid body shot"
        },
        {
            "description": "Anton tears up his notes outside the restaurant, scattering the pieces to the wind.",
            "location": "Street outside Le Petit Jardin",
            "timeOfDay": "Night",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "crisp white shirt, tailored charcoal trousers",
                    "expression": "determined, liberated",
                    "pose": "tearing paper, arms outstretched"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "Instead of his usual caustic critique, he wrote a glowing review that would change both his and Am\u00e9lie's lives forever.",
                    "dialogue_type": "NARRATION"
                }
            ],
            "cameraAngle": "Low angle",
            "cameraShot": "Wide shot"
        },
        {
            "description": "Montage of Anton writing his review, intercut with scenes of Am\u00e9lie cooking in her kitchen.",
            "location": "Anton's study / Le Petit Jardin kitchen",
            "timeOfDay": "Various times",
            "characters": [
                {
                    "name": "Anton Beaumont",
                    "dress": "comfortable home attire",
                    "expression": "focused, inspired",
                    "pose": "writing at desk"
                },
                {
                    "name": "Chef Am\u00e9lie Rousseau",
                    "dress": "white chef's jacket, black and white checkered pants, toque",
                    "expression": "passionate, creative",
                    "pose": "cooking in kitchen"
                }
            ],
            "dialogues": [
                {
                    "dialogue": "The bitter critic had rediscovered the sweet taste of nostalgia, and with it, a renewed passion for the culinary world he had once loved so dearly.",
                    "dialogue_type": "NARRATION"
                }
            ],
            "cameraAngle": "Various angles",
            "cameraShot": "Mid body shot"
        }
    ]
}
    """
]

fi_client = Client(
    api_key="5ffab106598343a79720824d380632ce",
    secret_key="faf78735c36c459f8f6be81823950f9d",
)
Name='Screenplay'

for row in chunk_output_1:
    
    response = fi_client.log(
        Name,
        ModelTypes.GENERATIVE_LLM,
        Environments.PRODUCTION,
        "v2",
        int(generate_random_date()),
        {
            "chat_history": [
                {"role": "user", "content":  chunk_input_1},
                {"role": "assistant",
                "content": row}
            ],
        }
    ).result()
    print(response.text)
    
for row in chunk_output_2:
    
    response = fi_client.log(
        Name,
        ModelTypes.GENERATIVE_LLM,
        Environments.PRODUCTION,
        "v2",
        int(generate_random_date()),
        {
            "chat_history": [
                {"role": "user", "content":  chunk_input_2},
                {"role": "assistant",
                "content": row}
            ],
        }
    ).result()
    print(response.text)
    