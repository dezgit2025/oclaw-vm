const fs = require('fs');
const path = require('path');

const LOGFILE = path.join(__dirname, '../logs/model_routing.log');

function logRouting(sessionKey, modelId, prompt) {
  const timestamp = new Date().toISOString();
  const promptExcerpt = (prompt || '').substring(0, 100).replace(/\n/g, ' ');
  const logLine = `${timestamp} - session:${sessionKey} - model:${modelId} - prompt:'${promptExcerpt}'\n`;
  fs.appendFileSync(LOGFILE, logLine);
}

module.exports = (event) => {
  // This hook receives routing events
  try {
    if (event && event.sessionKey && event.modelId) {
      logRouting(event.sessionKey, event.modelId, event.prompt || '');
    }
  } catch (e) {
    console.error('Failed to log routing:', e);
  }
};
