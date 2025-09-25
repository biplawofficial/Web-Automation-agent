import ollama
import re

class mainLLM:
    def __init__(self):
        self.model = "gemma3:4b"
    
    def call_llm(self, prompt: str):
        try:
            response = ollama.generate(model=self.model, prompt=prompt)
            result = response['response']
            return result
        except Exception as e:
            return f"Error: {e}"
    
    def get_action_plan(self, user_input: str, available_tools: str):
        prompt = f"""
        you have access to those tools for web navigation and data extraction from the browser environment:
        {available_tools}
        User wants to: {user_input}
        Create a complete web navigation plan To get the required information from the web. Return ONLY JSON:
        {{
            "goal": "{user_input}",
            "steps": [
                {{  
                    "order": 1,
                    "action": "search_google_safely",
                    "query": "search query",
                    "description": "What to look for in the search results"
                }},
                {{
                    "order": 2,
                    "action": "click_result", 
                    "target": "which result to click",
                    "description": "navigate to specific site"
                }},
                {{
                    "order": 3,
                    "action": "extract_data",
                    "what": "what information to extract",
                    "description": "final data extraction"
                }}
                ... and so on up to 7 steps max.
            ]
        }}
        note:
        -The target in the click_result should be an element that should be available on the page after the search or an element that is likely to be present on the page.
        -make use of save_results action to store intermediate results if needed.
        -You should even go to new page and again search for something else if needed to achieve the goal.
        Keep it to min 3-7 steps max. Be specific about search queries and targets.
        """
        return self.call_llm(prompt)
    
    def extract_final_data(self, content: str, original_goal: str):
        """Final call to extract structured data"""
        prompt = f"""
        Original goal: {original_goal}
        Page content: {content[:1500]}
        Extract the requested information in clear format.
        return proper detailed humanized formatted text it should be easy to read clear and detailed and up to point and should be what is asked.
        it is the final answer to the user so dont include any other info. you are an expert in writing detailed and clear text.
        Provide the final answer below:
        it should be detailed and up to point.
        it should be less than 150 words.
        clearly mention the source of information with each valid point eg amazon flipkart wikipedia etc.
        Dont make things bold or highlighted.keep normal text format.
        """
        #return 
        return self.call_llm(prompt)