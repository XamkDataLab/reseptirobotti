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
