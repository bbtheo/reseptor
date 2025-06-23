import os
import re
from dotenv import load_dotenv
from shiny import App, ui, render, reactive
from chatlas import ChatAnthropic

print("[DEBUG] Starting application initialization...")

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Load system prompt from file
system_prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'systemprompt.md')
print(f"[DEBUG] Loading system prompt from: {system_prompt_path}")

with open(system_prompt_path, 'r') as file:
    system_prompt = file.read()
print(f"[DEBUG] System prompt loaded, length: {len(system_prompt)} characters")

def sanitize_filename(title):
    """Convert recipe title to a safe filename"""
    print(f"[DEBUG] Sanitizing filename from: {title}")
    # Remove special characters and replace spaces with underscores
    sanitized = re.sub(r'[^\w\s-]', '', title)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    sanitized = sanitized.strip('_').lower()
    print(f"[DEBUG] Sanitized filename: {sanitized}")
    return sanitized

def extract_recipe_title(recipe_content):
    """Extract the title from the recipe content"""
    print(f"[DEBUG] Extracting title from recipe content, length: {len(recipe_content)}")
    # Look for the first heading (usually # Title or ## Title)
    lines = recipe_content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# '):
            title = line[2:].strip()
            print(f"[DEBUG] Found title: {title}")
            return title
    
    # Fallback
    title = "untitled_recipe"
    print(f"[DEBUG] Using fallback title: {title}")
    return title

def save_recipe(recipe_content):
    """Save recipe to recipes/ directory"""
    print("[DEBUG] Saving recipe...")
    
    # Extract title from recipe content
    title = extract_recipe_title(recipe_content)
    
    # Sanitize filename
    filename = sanitize_filename(title)
    
    # Ensure recipes directory exists
    recipes_dir = os.path.join(os.path.dirname(__file__), 'recipes')
    os.makedirs(recipes_dir, exist_ok=True)
    print(f"[DEBUG] Recipes directory: {recipes_dir}")
    
    # Create full file path
    file_path = os.path.join(recipes_dir, f"{filename}.md")
    print(f"[DEBUG] Saving to file: {file_path}")
    
    # Save the recipe
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(recipe_content)
        print(f"[DEBUG] Recipe saved successfully to: {file_path}")
        return True
    except Exception as e:
        print(f"[DEBUG] Error saving recipe: {e}")
        return False

app_ui = ui.page_fluid(
    ui.h1("Receptor"),
    ui.input_text("user_input", "enter your wish:", width = "100%"),
    ui.input_select("dietary_restrictions", "Dietary Restrictions", 
                    choices={"none": "None", "vegetarian": "Vegetarian", "vegan": "Vegan", 
                            "gluten_free": "Gluten-Free",}),
    ui.input_slider("wildness", "How Wild Should Suggestions Be?", min=1, max=10, value=5),
    ui.input_action_button("send", "Send"),
    ui.input_action_button("save", "Save Recipe"),
    ui.output_ui("save_status"),
    ui.output_ui("response")
)

print("[DEBUG] UI components created")

def server(input, output, session):
    print("[DEBUG] Server function initialized")
    
    chat = ChatAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"), 
        model="claude-3-5-sonnet-20240620",
        system_prompt=system_prompt
    )
    print("[DEBUG] ChatAnthropic instance created")
    
    # Store the current recipe content
    current_recipe = reactive.Value("")
    
    @reactive.event(input.send)
    def get_response():
        print("[DEBUG] Send button pressed!")
        print(f"[DEBUG] User input: {input.user_input()}")
        print(f"[DEBUG] Dietary restriction selected: {input.dietary_restrictions()}")
        print(f"[DEBUG] Wildness level: {input.wildness()}")
        
        dietary_restrictions = get_dietary_restrictions()
        wildness_level = get_wildness()
        
        user_message = f"""User request: {input.user_input()}
Dietary restrictions: {dietary_restrictions}
Wildness level: {wildness_level}"""
        
        print(f"[DEBUG] Sending message to model: {user_message}")
        response = chat.chat(user_message)
        print(f"[DEBUG] Received response from model, length: {len(response.content)} characters")
        
        # Store the recipe content for saving
        current_recipe.set(response.content)
        return response.content
    
    @reactive.event(input.save)
    def save_current_recipe():
        print("[DEBUG] Save button pressed!")
        if current_recipe():
            success = save_recipe(current_recipe())
            if success:
                return ui.div(
                    ui.p(f"✅ Recipe saved successfully!", style="color: green; font-weight: bold;"),
                )
            else:
                return ui.div(
                    ui.p(f"❌ Error saving recipe", style="color: red; font-weight: bold;")
                )
        else:
            return ui.div()
    
    @reactive.calc
    def get_dietary_restrictions():
        restriction = input.dietary_restrictions()
        print(f"[DEBUG] Getting dietary restrictions for: {restriction}")
        restriction_path = os.path.join(os.path.dirname(__file__), 'prompts', 'restrictions', f'{restriction}.md')
        print(f"[DEBUG] Loading restriction file from: {restriction_path}")
        
        with open(restriction_path, 'r') as file:
            content = file.read()
            print(f"[DEBUG] Dietary restriction content loaded, length: {len(content)} characters")
            return content
    
    @reactive.calc
    def get_wildness():
        wildness_value = input.wildness()
        print(f"[DEBUG] Getting wildness level: {wildness_value}")
        
        if wildness_value == 1:
            result = f"Ultra Conservative (1/10): Classic comfort foods only"
        elif wildness_value == 2:
            result = f"Very Conservative (2/10): Traditional family recipes"
        elif wildness_value == 3:
            result = f"Conservative (3/10): Familiar dishes with minor variations"
        elif wildness_value == 4:
            result = f"Moderately Conservative (4/10): Traditional recipes with some twists"
        elif wildness_value == 5:
            result = f"Balanced (5/10): Equal mix of classic and creative dishes"
        elif wildness_value == 6:
            result = f"Moderately Adventurous (6/10): Creative takes on familiar dishes"
        elif wildness_value == 7:
            result = f"Adventurous (7/10): Innovative combinations of known ingredients"
        elif wildness_value == 8:
            result = f"Very Adventurous (8/10): Bold flavor combinations and techniques"
        elif wildness_value == 9:
            result = f"Extremely Adventurous (9/10): Experimental and unique creations"
        else:
            result = f"Ultra Adventurous (10/10): Revolutionary and boundary-pushing recipes"
        
        print(f"[DEBUG] Wildness description: {result}")
        return result

    @output
    @render.ui
    def response():
        print(f"[DEBUG] response() function called, send button count: {input.send()}")
        if input.send() > 0:
            print("[DEBUG] Send button was pressed, generating response...")
            response_content = get_response()
            print(f"[DEBUG] Response generated, length: {len(response_content)} characters")
            return ui.markdown(response_content)
        print("[DEBUG] Send button not pressed, returning empty string")
        return ""

    @output
    @render.ui
    def save_status():
        print(f"[DEBUG] save_status() function called, save button count: {input.save()}")
        if input.save() > 0:
            print("[DEBUG] Save button was pressed, saving recipe...")
            return save_current_recipe()
        return ""

print("[DEBUG] Creating Shiny app...")
app = App(app_ui, server)
print("[DEBUG] Shiny app created successfully")
