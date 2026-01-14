const API_BASE_URL = 'http://localhost:8001';  // Backend on 8001, Firestorm on 8000

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

export const sendMessageToAgent = async (agentId, message) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: agentId,
        message: message
      }),
    });

    if (!response.ok) throw new Error('Failed to send message');
    return await response.json();
  } catch (error) {
    console.error('Send message error:', error);
    throw error;
  }
};

export const connectWebSocket = (onMessage, onError) => {
  const ws = new WebSocket(`ws://localhost:8001/ws/agent-status`);  // Backend on 8001

  ws.onopen = () => {
    console.log('✅ WebSocket connected');
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
    console.error('❌ WebSocket error:', error);
    // Don't call onError immediately - wait for close event
    // This prevents premature error messages during backend restart
  };

  ws.onclose = () => {
    console.log('🔌 WebSocket disconnected - will reconnect on next message');
    // Only call error handler on close, not on error event
    if (onError) onError(new Error('WebSocket disconnected'));
  };

  return ws;
};

// Activity Tracking API
export const getRecentActivities = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    if (filters.agent_id) params.append('agent_id', filters.agent_id);
    if (filters.request_id) params.append('request_id', filters.request_id);
    if (filters.activity_types) params.append('activity_types', filters.activity_types);
    if (filters.limit) params.append('limit', filters.limit.toString());

    const response = await fetch(`${API_BASE_URL}/api/activity/recent?${params}`);
    if (!response.ok) throw new Error('Failed to fetch activities');
    return await response.json();
  } catch (error) {
    console.error('Get activities error:', error);
    throw error;
  }
};

export const getAgentHierarchy = async (requestId = null) => {
  try {
    const params = requestId ? `?request_id=${requestId}` : '';
    const response = await fetch(`${API_BASE_URL}/api/activity/hierarchy${params}`);
    if (!response.ok) throw new Error('Failed to fetch hierarchy');
    return await response.json();
  } catch (error) {
    console.error('Get hierarchy error:', error);
    throw error;
  }
};

export const getAllAgentStates = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/activity/states`);
    if (!response.ok) throw new Error('Failed to fetch agent states');
    return await response.json();
  } catch (error) {
    console.error('Get agent states error:', error);
    throw error;
  }
};

export const getAgentState = async (agentId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/activity/states/${agentId}`);
    if (!response.ok) throw new Error('Failed to fetch agent state');
    return await response.json();
  } catch (error) {
    console.error('Get agent state error:', error);
    throw error;
  }
};

export const getPendingQuestions = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/activity/questions`);
    if (!response.ok) throw new Error('Failed to fetch questions');
    return await response.json();
  } catch (error) {
    console.error('Get questions error:', error);
    throw error;
  }
};

export const answerQuestion = async (questionId, answer) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/activity/questions/${questionId}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer }),
    });
    if (!response.ok) throw new Error('Failed to submit answer');
    return await response.json();
  } catch (error) {
    console.error('Answer question error:', error);
    throw error;
  }
};

export const getGeneratedFiles = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    if (filters.agent_id) params.append('agent_id', filters.agent_id);
    if (filters.request_id) params.append('request_id', filters.request_id);
    if (filters.limit) params.append('limit', filters.limit.toString());

    const response = await fetch(`${API_BASE_URL}/api/activity/files?${params}`);
    if (!response.ok) throw new Error('Failed to fetch generated files');
    return await response.json();
  } catch (error) {
    console.error('Get generated files error:', error);
    throw error;
  }
};

// Timeline View API
export const getRequests = async (limit = 50) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/requests?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch requests');
    return await response.json();
  } catch (error) {
    console.error('Get requests error:', error);
    throw error;
  }
};

export const getRequestTimeline = async (requestId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/requests/${requestId}/timeline`);
    if (!response.ok) throw new Error('Failed to fetch timeline');
    return await response.json();
  } catch (error) {
    console.error('Get timeline error:', error);
    throw error;
  }
};

export const getGitRepoInfo = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/git/repo-info`);
    if (!response.ok) throw new Error('Failed to fetch git info');
    return await response.json();
  } catch (error) {
    console.error('Get git info error:', error);
    throw error;
  }
};

export const getDeliverables = async (requestId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/deliverables/${requestId}`);
    if (!response.ok) throw new Error('Failed to fetch deliverables');
    return await response.json();
  } catch (error) {
    console.error('Get deliverables error:', error);
    throw error;
  }
};

// Self-Improvement Loop API
export const getSelfImprovementStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/self-improvement/status`);
    if (!response.ok) throw new Error('Failed to fetch self-improvement status');
    return await response.json();
  } catch (error) {
    console.error('Get self-improvement status error:', error);
    throw error;
  }
};

export const runSelfImprovementAnalysis = async (days = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/self-improvement/analyze?days=${days}`);
    if (!response.ok) throw new Error('Failed to run analysis');
    return await response.json();
  } catch (error) {
    console.error('Run analysis error:', error);
    throw error;
  }
};

export const getRecommendations = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/self-improvement/recommendations`);
    if (!response.ok) throw new Error('Failed to fetch recommendations');
    return await response.json();
  } catch (error) {
    console.error('Get recommendations error:', error);
    throw error;
  }
};

export const getAgentFeedback = async (agentName) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/self-improvement/feedback/${encodeURIComponent(agentName)}`);
    if (!response.ok) throw new Error('Failed to fetch agent feedback');
    return await response.json();
  } catch (error) {
    console.error('Get agent feedback error:', error);
    throw error;
  }
};

export const approveRecommendation = async (recommendationId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/self-improvement/recommendations/${recommendationId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) throw new Error('Failed to approve recommendation');
    return await response.json();
  } catch (error) {
    console.error('Approve recommendation error:', error);
    throw error;
  }
};

export const rejectRecommendation = async (recommendationId, reason = '') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/self-improvement/recommendations/${recommendationId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recommendation_id: recommendationId, reason }),
    });
    if (!response.ok) throw new Error('Failed to reject recommendation');
    return await response.json();
  } catch (error) {
    console.error('Reject recommendation error:', error);
    throw error;
  }
};

// Achievement System API
export const getAllAchievements = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/achievements`);
    if (!response.ok) throw new Error('Failed to fetch achievements');
    return await response.json();
  } catch (error) {
    console.error('Get achievements error:', error);
    throw error;
  }
};

export const getRecentAchievements = async (limit = 10) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/achievements/recent?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch recent achievements');
    return await response.json();
  } catch (error) {
    console.error('Get recent achievements error:', error);
    throw error;
  }
};

export const getAchievementStats = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/achievements/stats`);
    if (!response.ok) throw new Error('Failed to fetch achievement stats');
    return await response.json();
  } catch (error) {
    console.error('Get achievement stats error:', error);
    throw error;
  }
};

export const getAgentAchievements = async (agentClass) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/achievements/agent/${encodeURIComponent(agentClass)}`);
    if (!response.ok) throw new Error('Failed to fetch agent achievements');
    return await response.json();
  } catch (error) {
    console.error('Get agent achievements error:', error);
    throw error;
  }
};
