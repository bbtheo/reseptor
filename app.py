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
    ui.input_action_button("send", "Create recipe", width="100%"),
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
        response = chat.chat(input.user_input())
        return response.content
    
    @output
    @render.ui
    def response():
        if input.send() > 0:
            return ui.markdown(get_response())
        return ""

app = App(app_ui, server)
