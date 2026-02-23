import model_fallback_routing

# Define a fake token limit error for testing
class FakeTokenLimitError(Exception):
    pass

# Override the call_model_api function to simulate token limit on Copilot Opus 4.6

def fake_call_model_api(model, prompt):
    if model == 'copilot-opus-4.6':
        raise FakeTokenLimitError('Token limit exceeded')
    return f'Response from {model}'

model_fallback_routing.call_model_api = fake_call_model_api
model_fallback_routing.TokenLimitError = FakeTokenLimitError

# Prepare a test session forcing Copilot Opus 4.6
test_session = {'id': 'test-session-1', 'forced_model': 'copilot-opus-4.6'}

# Test prompt
test_prompt = 'Test fallback due to token limit.'

# Run the call and print result
result = model_fallback_routing.call_forced_model_with_fallback(test_session, test_prompt)
print('Test result:', result)
