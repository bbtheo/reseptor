import os
from dotenv import load_dotenv
from shiny import App, ui, render, reactive
from chatlas import ChatAnthropic

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Load system prompt from file
system_prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'systemprompt.md')

with open(system_prompt_path, 'r') as file:
    system_prompt = file.read()

app_ui = ui.page_fluid(
    ui.h1("Receptor"),
    ui.input_text("user_input", "enter your wish:", width = "100%"),
    ui.input_select("dietary_restrictions", "Dietary Restrictions", 
                    choices={"none": "None", "vegetarian": "Vegetarian", "vegan": "Vegan", 
                            "gluten_free": "Gluten-Free",}),
    ui.input_slider("wildness", "How Wild Should Suggestions Be?", min=1, max=10, value=5),
    ui.input_action_button("send", "Send"),
    ui.output_ui("response")
)

def server(input, output, session):
    chat = ChatAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"), 
        model="claude-3-5-sonnet-20240620",
        system_prompt=system_prompt
    )
    
    @reactive.event(input.send)
    def get_response():
        dietary_restrictions = get_dietary_restrictions()
        wildness_level = get_wildness()
        user_message = f"""User request: {input.user_input()}
Dietary restrictions: {dietary_restrictions}
Wildness level: {wildness_level}"""
        print(user_message)
        response = chat.chat(user_message)
        return response.content
    
    @reactive.calc
    def get_dietary_restrictions():
        restriction = input.dietary_restrictions()
        restriction_path = os.path.join(os.path.dirname(__file__), 'prompts', 'restrictions', f'{restriction}.md')
        with open(restriction_path, 'r') as file:
            return file.read()
    
    @reactive.calc
    def get_wildness():
        wildness_value = input.wildness()
        if wildness_value == 1:
            return f"Ultra Conservative (1/10): Classic comfort foods only"
        elif wildness_value == 2:
            return f"Very Conservative (2/10): Traditional family recipes"
        elif wildness_value == 3:
            return f"Conservative (3/10): Familiar dishes with minor variations"
        elif wildness_value == 4:
            return f"Moderately Conservative (4/10): Traditional recipes with some twists"
        elif wildness_value == 5:
            return f"Balanced (5/10): Equal mix of classic and creative dishes"
        elif wildness_value == 6:
            return f"Moderately Adventurous (6/10): Creative takes on familiar dishes"
        elif wildness_value == 7:
            return f"Adventurous (7/10): Innovative combinations of known ingredients"
        elif wildness_value == 8:
            return f"Very Adventurous (8/10): Bold flavor combinations and techniques"
        elif wildness_value == 9:
            return f"Extremely Adventurous (9/10): Experimental and unique creations"
        else:
            return f"Ultra Adventurous (10/10): Revolutionary and boundary-pushing recipes"

    @output
    @render.ui
    def response():
        if input.send() > 0:
            return ui.markdown(get_response())
        return ""

app = App(app_ui, server)
