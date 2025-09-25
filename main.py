import asyncio
import requests
import json
from playwright.sync_api import sync_playwright
import time
import random
from agent import mainLLM
import re

class SimpleAgent:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch( #browser instance modified to reduct bot like behavior
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        user_agents = [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self.context = self.browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=random.choice(user_agents),
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        self.page = self.context.new_page()
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            })
        """)
        self.tools = {
            "search_google_safely": {
                "method": self.search_google_safely,
                "description": "Search Google for a query and return top results takes the target query as input string",
            },
            "click_result": {
                "method": self.smart_click,
                "description": "To click on a search result based on the context provided takes a target as input string",
            },
            "extract_data": {
                "method": self.extract_visible_content,
                "description": "Extract visible text content from the current page and filters out unnecessary content of the raw webpage"
            },
            "close_browser": {
                "method": self.close,
                "description": "Close the browser and cleanup resources"
            },
            "get_page_info": {
                "method": self.get_page_info,
                "description": "Get current page information such as URL, title, and a preview of the content"
            },"save_results":{
                "method": self.save_results,
                "description": "Append results to a local file for record-keeping of current context(i.e the last step web page context will be saved using extract data use this when you want to save the current context) and then using this at the last step to get final results"
            }
        }

    def save_results(self):
        try:
            with open("results_log.txt", "a") as f:
                f.write(f"URL: {self.page.url}\n")
                f.write(f"Title: {self.page.title()}\n")
                f.write(f"Content Preview: {self.extract_visible_content()[:500]}\n")
                f.write("="*50 + "\n")
            return "Results saved to results_log.txt"
        except Exception as e:
            return f"Error saving results: {e}"
    def human_like_delay(self, min_sec=1, max_sec=4):
        time.sleep(random.uniform(min_sec, max_sec))

    def human_like_mouse_movement(self):
        try:

            for _ in range(3):
                x = random.randint(100, 1200)
                y = random.randint(100, 600)
                self.page.mouse.move(x, y)
                time.sleep(0.2)
        except:
            pass
    
    def search_google_safely(self, query: str):
        try:
            print(f"🔍 Searching for: {query}")
            self.page.goto("https://www.google.com", wait_until="networkidle")
            self.human_like_delay(1, 3)
            search_box = "textarea[name='q'], input[name='q']"
            self.page.click(search_box)
            self.human_like_delay(0.5, 1)
            for char in query:
                self.page.type(search_box, char, delay=random.randint(50, 150))
                if random.random() > 0.8:  # Random pauses
                    time.sleep(random.uniform(0.1, 0.3))
            self.page.press(search_box, "Enter")
            self.human_like_delay(3, 5)
            if "unusual traffic" in self.page.content().lower() or "detected unusual traffic" in self.page.content().lower():
                print("🚫 Blocked by Google. Trying alternative approach...")
                return self.use_alternative_search_engine(query)
            return self.get_page_info()
        except Exception as e:
            return {"error": str(e)}
    
    def use_alternative_search_engine(self, query: str):
        alternatives = [
            ("https://search.yahoo.com", "input[name='p']"),
            ("https://duckduckgo.com", "input[name='q']"),
            ("https://www.bing.com", "input[name='q']"),
        ]
        for url, selector in alternatives:
            try:
                self.page.goto(url, wait_until="networkidle")
                self.page.fill(selector, query)
                self.page.press(selector, "Enter")
                return self.get_page_info()
            except:
                continue
        return {"error": "All search engines blocked"}
    
    def smart_click(self, target: str):
        strategies = [
            f"a:has-text('{target}')",
            f"h3:has-text('{target}')",
            f"div:has-text('{target}')",
            f"span:has-text('{target}')",
            f"button:has-text('{target}')",
            f"a:has-text(/:.*{target}.*/i)",
            f"h3:has-text(/:.*{target}.*/i)",
        ]
        
        for selector in strategies:
            try:
                if self.page.locator(selector).count() > 0:
                    self.human_like_mouse_movement()
                    self.page.click(selector)
                    self.human_like_delay(1, 2)
                    if self.page.url != self.page.context.pages[0].url:
                        return self.get_page_info()
            except:
                continue
        return "Click failed - element not found"

    def extract_visible_content(self):
        try:
            content = self.page.evaluate("""
                () => {
                    const elementsToRemove = document.querySelectorAll('script, style, nav, footer, header');
                    elementsToRemove.forEach(el => el.remove());
                    return document.body.innerText;
                }
            """)
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            clean_content = '\n'.join(lines[:100])
            return clean_content[:2000]
        except Exception as e:
            return f"Extraction error: {e}"
    
    def get_page_info(self):
        try:
            return {
                "url": self.page.url,
                "title": self.page.title(),
                "content_preview": self.extract_visible_content()[:500]
            }
        except:
            return {"error": "Could not get page info"}
    
    def close(self):
        self.browser.close()
        self.playwright.stop()

    
    def get_tools_prompt(self):
        tools_text = ""
        for tool_name, tool_info in self.tools.items():
            tools_text += f"• {tool_name}: {tool_info['description']}\n"
        return tools_text
    def parse_json(self, text: str):
        """Extract JSON from LLM response"""
        try:
            clean_text = re.sub(r'[^\x00-\x7F]+', '', text)
            json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"error": "No JSON found in response"}
        except Exception as e:
            return {"error": f"JSON parsing failed: {e}"}
    

def main():
    agent = SimpleAgent()
    mainllm=mainLLM()
    try:
        while True:
            input_query=input("How can I assist you! \n")
            if input_query.lower() in ["exit", "quit", "q"]:
                print("Thank you for using the agent. Goodbye!")
                break  
            available_tools=agent.get_tools_prompt()
            action_plan_json=mainllm.get_action_plan(input_query,available_tools)
            action_plan=agent.parse_json(action_plan_json)
            print("Action Plan:", json.dumps(action_plan, indent=2))
            try:
                results = []
                ind=0
                
                for i, step in enumerate(action_plan.get("steps", [])):
                    print(f"\n{i+1}. ⚡ Executing: {step.get('description', 'Unknown step')}")
                    
                    action = step.get("action", "")
                    if action in agent.tools:
                        method = agent.tools[action]["method"]
                        params = {k: v for k, v in step.items() if k not in ["order", "action", "description"]}
                        print(f"Executing Step {step['order']}: {action} with params {params}")
                        
                        if action =="extract_data":
                            result=method()
                            results.append({"index":ind+1,"result": result})
                            ind+=1
                        elif action =="save_results":
                            results.append({"index":ind+1,"result": results})
                            ind+=1
                        else:
                            result = method(**params) if params else method()
                        print(f"✅ Step {i+1} completed")
                        page_content = str(result).lower()
                        if "unusual traffic" in page_content or "blocked" in page_content or "captcha" in page_content:
                            print("\n🚫 We've been blocked! Please solve the CAPTCHA manually.")
                            print("Press Enter to continue after solving...")
                            input()
                    else:
                        print(f"❌ Unknown action: {action}")
                
                # Final extraction after all steps
                print("\n📊 Analyzing final results...")
                final_content = agent.extract_visible_content()

                if not final_content:
                    print("❌ No final content extracted")
                    final_results = {"error": "No content extracted"}
                else:
                    results_str = "\n".join([f"Step {r['index']} : {r['result']}" for r in results])
                    final_response = mainllm.extract_final_data( results_str, input_query)
                    print(final_response)
                #     final_results = agent.parse_json(final_response)
                
                # print(f"\n🎯 Final Results:")
                # print(json.dumps(final_results, indent=2))
                
            except Exception as e:
                print(f"❌ Error during execution: {e}")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:    
        agent.close()
if __name__ == "__main__":
    main()