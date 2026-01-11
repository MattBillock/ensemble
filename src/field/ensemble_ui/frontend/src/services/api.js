const API_BASE_URL = 'http://localhost:8000';

export const generateSolution = async (problemDescription, budgetTier = 'balanced') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/generate-solution`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        problem: problemDescription,
        budget_tier: budgetTier
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to generate solution');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const getApplicationStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/status`);
    if (!response.ok) throw new Error('Failed to fetch status');
    return await response.json();
  } catch (error) {
    console.error('Status API Error:', error);
    throw error;
  }
};

export const connectWebSocket = (onMessage, onError) => {
  const ws = new WebSocket(`ws://localhost:8000/ws/agent-status`);

  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('WebSocket message error:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (onError) onError(error);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
  };

  return ws;
};
