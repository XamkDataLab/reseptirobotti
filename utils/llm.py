import streamlit as st

def get_LLM_response(user_text, task_description, system_prompt):
    try:
        formatted_task_description = task_description.format(user_text)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_task_description}
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-4-0125-preview",  
            messages=messages,
        )

        if chat_completion.choices:
            return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "Error"

system_prompt1= "you are a helpful assistant specializing in scientific publications"
task_description1 = """The following is a description of what user wants to find in a big database that contains either scientific publications or patent data. The database supports boolean queries. Formulate the following description into a comprehensive, nuanced and valid boolean query. Provide the suggested query as one line query string formatted as code:\n {}"""
