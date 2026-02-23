import logging
from datetime import datetime

# Assume these are your OpenClaw LLM call wrappers

def call_model_api(model_name, prompt):
    # Placeholder for actual model invocation
    # Raise TokenLimitError when token limit hit
    pass

# Custom exception to simulate token limit errors
class TokenLimitError(Exception):
    pass


def log_fallback(session, forced_model, error, prompt, fallback_model):
    timestamp = datetime.utcnow().isoformat() + 'Z'
    truncated_prompt = prompt[:512] + '...' if len(prompt) > 512 else prompt
    log_entry = f"{timestamp} - Model fallback: {forced_model} hit an error: {error}."
    log_entry += f" Falling back to {fallback_model}. Prompt: {truncated_prompt}"
    # Log to console or persistent storage
    logging.warning(log_entry)


def alert_user(session, message):
    # Send alert message to user session
    print(f"ALERT to Session {session.get('id', '[unknown]')}: {message}")


def call_forced_model_with_fallback(session, prompt):
    forced_model = session.get('forced_model')
    if not forced_model:
        # No forced model active, use default routing
        return call_model_api('default', prompt)

    try:
        response = call_model_api(forced_model, prompt)
        return response
    except TokenLimitError as e:
        fallback_model = 'github-copilot/gpt-5.2'
        log_fallback(session, forced_model, e, prompt, fallback_model)
        alert_user(session, f"Model {forced_model} hit token limit; falling back to {fallback_model}.")
        # Clear forced model lock if you want
        session.pop('forced_model', None)
        session.pop('model_expiration', None)
        response = call_model_api(fallback_model, prompt)
        return response
    except Exception as e:
        # Rethrow other errors
        raise

# Example test sequence
if __name__ == '__main__':
    test_session = {'id': 'session123', 'forced_model': 'copilot-opus-4.6'}
    test_prompt = 'Explain advanced fallback routing logic.'
    try:
        result = call_forced_model_with_fallback(test_session, test_prompt)
        print('Response:', result)
    except Exception as ex:
        print('Error during call:', ex)
