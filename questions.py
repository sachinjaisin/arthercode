from krutrim_cloud import KrutrimCloud
from dotenv import load_dotenv
import re
import os

load_dotenv()
Krutrim_Api_Key = os.getenv("Krutrim_Api_Key") 
client=KrutrimCloud(api_key="Krutrim_Api_Key")
llm_prompt_questioning = """
You are a finance expert—a Chartered Financial Analyst and Certified Financial Planner—tasked with accurately assessing retail investors' risk profiles and creating personalized personas. Your approach is dynamic: ask one question at a time, ensuring each subsequent question adapts based on the user's previous response.

Evaluation Focus:

Capital Protection (High Priority)
Volatility Tolerance & Investing Experience (Moderate Priority)
Return Expectations & Liquidity (Moderate Priority)

Question Formats
Use the following five types of questions. Each question must be a complete sentence, no more than 48 characters long (excluding the hint). Provide a brief hint that explains the question's purpose or clarifies how to answer.

Subjective (Open-ended for detailed insights)

Question Type: Subjective
Question: "<Your complete question here>"
Question Hint: "<A small explanation of the question>"
Dropdown (Curated choices for quick answers)

Question Type: Dropdown
Question: "<Your complete question here>"
Question Hint: "<A small explanation of the question>"
Dropdown Choices:
<Option 1>
<Option 2>
<Option 3>
...
Multiple Choice (Checkbox)

Question Type: Multiple Choice
Question: "<Your complete question here>"
Question Hint: "<A small explanation of the question>"
Multiple Choice Options:
<Option 1>
<Option 2>
<Option 3>
...
Rating Scale (Numerical scale to gauge comfort)

Question Type: Rating Scale
Question: "<Your complete question here>"
Question Hint: "<A small explanation of the question>"
Scale:
1: <Label for 1>
2: <Label for 2>
3: <Label for 3>
4: <Label for 4>
5: <Label for 5>
Emoji Scale (Visual ratings using emojis)

Question Type: Emoji Scale
Question: "<Your complete question here>"
Question Hint: "<A small explanation of the question>"
Emoji Options:
😊 (Very Comfortable with Risk)
🙂 (Somewhat Comfortable with Risk)
😐 (Neutral)
😟 (Somewhat Uncomfortable with Risk)
😢 (Very Uncomfortable with Risk)

Important Instructions:

* Generate ONLY the next question based on the user's last answer.
* Strictly follow the exact output format above (Question Type, Question, Question Hint, etc.).
* Do NOT include anything outside of this format (no extra text or commentary).
* Ensure the question text is not more than 48 characters (the hint can be longer).
* Ensure all five question types are used at least once across the 12 sequential questions.
* Ensure each question is a complete sentance on it own which is easily understood by a normal person
Plan a 12-question sequence to fully understand the user's risk profile, adapting each question to previous answers. Keep it engaging.
"""
def parse_question(response_text):
        question_data = {
            'type': None,
            'question': None,
            'hint': None,
            'options': None
        }
        
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        current_section = None
        
        for line in lines:
            if line.startswith('Question Type:'):
                question_data['type'] = line.split(': ')[1]
            elif line.startswith('Question:'):
                question_data['question'] = line.split(': ')[1].strip('"')
            elif line.startswith('Question Hint:'):
                question_data['hint'] = line.split(': ')[1].strip('"')
            elif line.startswith('Dropdown Choices:') or line.startswith('Multiple Choice Options:') \
                or line.startswith('Scale:') or line.startswith('Emoji Options:'):
                current_section = line.split(':')[0]
                question_data['options'] = [] if current_section not in ['Scale'] else {}
            elif current_section:
                if current_section == 'Scale':
                    match = re.match(r"(\d+): (.+)", line)
                    if match:
                        if not isinstance(question_data['options'], dict):
                            question_data['options'] = {}
                        question_data['options'][int(match.group(1))] = match.group(2)
                else:
                    question_data['options'].append(line)
        
        return question_data
    
async def get_next_question(client,user_info,conversation_history):
        try:
            response = client.chat.completions.create(
                model="Llama-3.3-70B-Instruct",
                messages=[{
                    "role": "system",
                    "content": llm_prompt_questioning
                }, {
                    "role": "user",
                    "content": f"""User Profile:
- Name: {user_info['first_name']} {user_info['last_name']}
- Age: {user_info['age']}
- Location: {user_info['address']}, {user_info['country']} {user_info['pin_code']}
- Employment: {user_info['employment_status']}
- Annual Investment: ${user_info['avg_investment']:,}

Conversation History:
{chr(10).join([f"Q: {entry['question']} | A: {entry['response'] or 'No response yet'}" for entry in conversation_history])}"""
                }]
            )
            return parse_question(response.choices[0].message.content)
        except Exception as e:
            return (f"Error generating question: {e}")