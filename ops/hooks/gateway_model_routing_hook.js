const sessionForcedFlagKey = 'forced_model';
const sessionToggleConfirmKey = 'awaiting_toggle_confirm';

async function sendMessageToUser(sessionId, message) {
  // Implement message sending to your user/session interface
  console.log(`Message to session ${sessionId}: ${message}`);
}

async function routeModel(session, prompt) {
  const lowerPrompt = prompt.toLowerCase();

  if (lowerPrompt.includes('think hard')) {
    session[sessionForcedFlagKey] = 'github-copilot/gpt-5.2';
    session[sessionToggleConfirmKey] = false;
    console.log(`Session ${session.id}: Forced model set to GPT-5.2 due to 'think hard' command.`);
    await sendMessageToUser(session.id, "Engaged GPT-5.2 for this session due to 'think hard'.");
    // Return or continue routing as desired
  }

  if (lowerPrompt.includes('default thinking')) {
    session[sessionToggleConfirmKey] = true;
    console.log(`Session ${session.id}: User requested default thinking toggle.`);
    await sendMessageToUser(session.id, "Do you want to switch back to default model routing? Please reply with yes or no.");
  }

  if (session[sessionToggleConfirmKey]) {
    if (lowerPrompt.match(/^(yes|confirm|yep)$/)) {
      delete session[sessionForcedFlagKey];
      session[sessionToggleConfirmKey] = false;
      console.log(`Session ${session.id}: Forced model cleared, reverted to default.`);
      await sendMessageToUser(session.id, "Model routing reset to default. Using standard routing.");
      // After clearing, route with default
      return defaultRouting(session, prompt);
    } else if (lowerPrompt.match(/^(no|cancel|stop)$/)) {
      session[sessionToggleConfirmKey] = false;
      console.log(`Session ${session.id}: Toggle cancelled, keeping forced model.`);
      await sendMessageToUser(session.id, "Continuing with forced model routing.");
    }
  }

  if (session[sessionForcedFlagKey]) {
    return callModelAPI(session[sessionForcedFlagKey], prompt);
  }

  return defaultRouting(session, prompt);
}

// Dummy placeholders for real implementations
async function callModelAPI(model, prompt) {
  return `Response from model ${model} for prompt: ${prompt}`;
}

async function defaultRouting(session, prompt) {
  return `Default model response for prompt: ${prompt}`;
}

module.exports = { routeModel };
