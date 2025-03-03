import time

from google.genai import errors, types

from utils import print_error


def get_rating(client, instruction, description):
    """Get a job match rating from Gemini AI model.

    Takes a job description and returns a rating indicating how well
    the candidate's resume matches the job requirements. Uses the system prompt
    which contains the resume and rating criteria.

    Returns:
        int: Rating from 1-100, where 1 is no match and 100 is perfect match
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-thinking-exp",
            config=types.GenerateContentConfig(system_instruction=instruction),
            contents=description,
        )
        return int(response.text)
    except errors.APIError as e:
        if e.code == 429:
            print_error(
                f"{time.strftime('%Y-%m-%d %H:%M:%S')} Rate limit exceeded: {e}, waiting 10 seconds"
            )
            time.sleep(10)
            return get_rating(description)
        raise


def get_suggestions(client, instruction, description):
    """Get resume suggestions from Gemini AI model.

    Takes a job description and returns several resume suggestions.

    Returns:
        str: Resume suggestions
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-thinking-exp",
            config=types.GenerateContentConfig(system_instruction=instruction),
            contents=description,
        )
        return response.text
    except errors.APIError as e:
        if e.code == 429:
            print_error(
                f"{time.strftime('%Y-%m-%d %H:%M:%S')} Rate limit exceeded: {e}, waiting 10 seconds"
            )
            time.sleep(10)
            return get_suggestions(description)
        raise
