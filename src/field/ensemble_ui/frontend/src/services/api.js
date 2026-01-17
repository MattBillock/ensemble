const API_BASE_URL = 'http://localhost:8001';  // Backend on 8001, Firestorm on 8000

/**
 * Custom error class for API errors with status code
 */
export class APIError extends Error {
  constructor(message, status, endpoint) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.endpoint = endpoint;
  }
}

/**
 * Fetch with timeout wrapper
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @param {number} timeoutMs - Timeout in milliseconds (default: 30000)
 * @returns {Promise<Response>} - Fetch response
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = 30000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new APIError(`Request timeout after ${timeoutMs}ms`, 408, url);
    }
    throw error;
  }
}

/**
 * Fetch with automatic response validation and error handling
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @param {*} defaultValue - Default value to return on error (null if not specified)
 * @returns {Promise<*>} - JSON response or default value
 */
async function fetchWithValidation(url, options = {}, defaultValue = null) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText);
      throw new APIError(
        `HTTP ${response.status}: ${errorText || response.statusText}`,
        response.status,
        url
      );
    }

    const text = await response.text();
    if (!text) {
      return defaultValue;
    }

    return JSON.parse(text);
  } catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      console.error(`Request timeout: ${url}`);
      return defaultValue;
    }

    if (error instanceof APIError) {
      console.error(`API Error [${error.status}]: ${error.message}`);
      return defaultValue;
    }

    console.error(`Request failed: ${url}`, error);
    return defaultValue;
  }
}

export const generateSolution = async (problemDescription, budgetTier = 'balanced') => {
  try {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/generate-solution`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          problem: problemDescription,
          budget_tier: budgetTier
        }),
      },
      60000  // 60 second timeout for solution generation
    );

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText);
      throw new APIError(
        `Failed to generate solution: ${errorText || response.statusText}`,
        response.status,
        '/api/generate-solution'
      );
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const continueProject = async (projectId, budgetTier = 'balanced') => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/projects/${encodeURIComponent(projectId)}/continue?budget_tier=${budgetTier}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText);
      throw new APIError(
        `Failed to continue project: ${errorText || response.statusText}`,
        response.status,
        `/api/projects/${projectId}/continue`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('Continue project error:', error);
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

/**
 * Enhanced WebSocket connection with subscriptions, reconnection, and event filtering.
 *
 * @param {Object} options - Connection options
 * @param {Function} options.onEvent - Callback for events: (event) => void
 * @param {Function} options.onConnect - Called when connected: (clientId) => void
 * @param {Function} options.onDisconnect - Called when disconnected: () => void
 * @param {Function} options.onError - Called on error: (error) => void
 * @param {string[]} options.eventTypes - Event types to subscribe to (default: all)
 * @param {Object} options.filters - Event filters like {request_id: "abc123"}
 * @param {boolean} options.autoReconnect - Auto-reconnect on disconnect (default: true)
 * @param {number} options.maxRetries - Max reconnection attempts (default: 10)
 * @returns {Object} - Connection controller with methods: close(), subscribe(), ping()
 */
export const connectEnhancedWebSocket = (options = {}) => {
  const {
    onEvent = () => {},
    onConnect = () => {},
    onDisconnect = () => {},
    onError = () => {},
    eventTypes = null,
    filters = {},
    autoReconnect = true,
    maxRetries = 10,
  } = options;

  let ws = null;
  let clientId = null;
  let reconnectAttempts = 0;
  let reconnectTimeout = null;
  let isClosing = false;
  let currentSubscriptions = eventTypes;
  let currentFilters = filters;

  const connect = () => {
    if (isClosing) return;

    ws = new WebSocket('ws://localhost:8001/ws/events');

    ws.onopen = () => {
      console.log('✅ Enhanced WebSocket connected');
      reconnectAttempts = 0;

      // Subscribe to specific event types if provided
      if (currentSubscriptions) {
        ws.send(JSON.stringify({
          action: 'subscribe',
          event_types: currentSubscriptions,
          filters: currentFilters
        }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        // Handle connection confirmation
        if (message.type === 'connected') {
          clientId = message.data?.client_id;
          onConnect(clientId);
          return;
        }

        // Handle subscription updates
        if (message.type === 'subscription_updated') {
          console.log('📬 Subscriptions updated:', message.data);
          return;
        }

        // Handle pong (keep-alive response)
        if (message.type === 'pong') {
          return;
        }

        // Handle buffered events
        if (message.type === 'buffered_events') {
          const events = message.data?.events || [];
          events.forEach(e => onEvent(e));
          return;
        }

        // Handle errors
        if (message.type === 'error') {
          onError(new Error(message.data?.message || 'Unknown error'));
          return;
        }

        // Regular event
        onEvent(message);

      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ Enhanced WebSocket error:', error);
    };

    ws.onclose = (event) => {
      console.log('🔌 Enhanced WebSocket disconnected', event.code, event.reason);
      clientId = null;
      onDisconnect();

      // Attempt reconnection with exponential backoff
      if (autoReconnect && !isClosing && reconnectAttempts < maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        reconnectAttempts++;
        console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxRetries})`);

        reconnectTimeout = setTimeout(connect, delay);
      } else if (reconnectAttempts >= maxRetries) {
        onError(new Error('Max reconnection attempts reached'));
      }
    };
  };

  // Start connection
  connect();

  // Return controller object
  return {
    /**
     * Close the WebSocket connection
     */
    close: () => {
      isClosing = true;
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.close();
      }
    },

    /**
     * Update subscriptions
     * @param {string[]} eventTypes - Event types to subscribe to
     * @param {Object} newFilters - Event filters
     */
    subscribe: (eventTypes, newFilters = {}) => {
      currentSubscriptions = eventTypes;
      currentFilters = newFilters;

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          action: 'subscribe',
          event_types: eventTypes,
          filters: newFilters
        }));
      }
    },

    /**
     * Send a ping to keep connection alive
     */
    ping: () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'ping' }));
      }
    },

    /**
     * Request buffered events
     */
    getBuffer: () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'get_buffer' }));
      }
    },

    /**
     * Get connection status
     */
    isConnected: () => {
      return ws && ws.readyState === WebSocket.OPEN;
    },

    /**
     * Get client ID
     */
    getClientId: () => clientId
  };
};

// WebSocket stats API
export const getWebSocketStats = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/websocket/stats`);
    if (!response.ok) throw new Error('Failed to fetch WebSocket stats');
    return await response.json();
  } catch (error) {
    console.error('Get WebSocket stats error:', error);
    throw error;
  }
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
    // URL encode the question ID since it may contain slashes
    const encodedId = encodeURIComponent(questionId);
    const response = await fetch(`${API_BASE_URL}/api/activity/questions/${encodedId}/answer`, {
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

// Auto-Apply Mode API
export const getAutoApplyConfig = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/self-improvement/auto-apply`);
    if (!response.ok) throw new Error('Failed to fetch auto-apply config');
    return await response.json();
  } catch (error) {
    console.error('Get auto-apply config error:', error);
    throw error;
  }
};

export const setAutoApplyConfig = async (enabled, applyOnAnalysis = true, minPriority = 'medium') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/self-improvement/auto-apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        enabled,
        apply_on_analysis: applyOnAnalysis,
        min_priority: minPriority
      }),
    });
    if (!response.ok) throw new Error('Failed to set auto-apply config');
    return await response.json();
  } catch (error) {
    console.error('Set auto-apply config error:', error);
    throw error;
  }
};

export const applyAllRecommendations = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/self-improvement/apply-all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) throw new Error('Failed to apply all recommendations');
    return await response.json();
  } catch (error) {
    console.error('Apply all recommendations error:', error);
    throw error;
  }
};

export const applySingleRecommendation = async (recommendationId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/self-improvement/recommendations/${recommendationId}/apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) throw new Error('Failed to apply recommendation');
    return await response.json();
  } catch (error) {
    console.error('Apply recommendation error:', error);
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

// ========== Swarm State Management API ==========

export const getSwarmSessions = async (limit = 50, status = null) => {
  try {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (status) params.append('status', status);
    const response = await fetch(`${API_BASE_URL}/api/swarm/sessions?${params}`);
    if (!response.ok) throw new Error('Failed to fetch swarm sessions');
    return await response.json();
  } catch (error) {
    console.error('Get swarm sessions error:', error);
    throw error;
  }
};

export const getSwarmSession = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/swarm/sessions/${sessionId}`);
    if (!response.ok) throw new Error('Failed to fetch session');
    return await response.json();
  } catch (error) {
    console.error('Get session error:', error);
    throw error;
  }
};

export const getSwarmAgents = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    if (filters.session_id) params.append('session_id', filters.session_id);
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit.toString());
    const response = await fetch(`${API_BASE_URL}/api/swarm/agents?${params}`);
    if (!response.ok) throw new Error('Failed to fetch swarm agents');
    return await response.json();
  } catch (error) {
    console.error('Get swarm agents error:', error);
    throw error;
  }
};

export const getSwarmAgent = async (agentId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/swarm/agents/${agentId}`);
    if (!response.ok) throw new Error('Failed to fetch agent');
    return await response.json();
  } catch (error) {
    console.error('Get swarm agent error:', error);
    throw error;
  }
};

export const getSwarmStats = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/swarm/stats`);
    if (!response.ok) throw new Error('Failed to fetch swarm stats');
    return await response.json();
  } catch (error) {
    console.error('Get swarm stats error:', error);
    throw error;
  }
};

export const getSwarmEvents = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    if (filters.session_id) params.append('session_id', filters.session_id);
    if (filters.agent_id) params.append('agent_id', filters.agent_id);
    if (filters.event_type) params.append('event_type', filters.event_type);
    if (filters.limit) params.append('limit', filters.limit.toString());
    const response = await fetch(`${API_BASE_URL}/api/swarm/events?${params}`);
    if (!response.ok) throw new Error('Failed to fetch swarm events');
    return await response.json();
  } catch (error) {
    console.error('Get swarm events error:', error);
    throw error;
  }
};

// ========== Recovery System API ==========

export const getStalledAgents = async (thresholdMinutes = 5) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/recovery/stalled?threshold_minutes=${thresholdMinutes}`);
    if (!response.ok) throw new Error('Failed to fetch stalled agents');
    return await response.json();
  } catch (error) {
    console.error('Get stalled agents error:', error);
    throw error;
  }
};

export const getRecoveryQueue = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/recovery/queue`);
    if (!response.ok) throw new Error('Failed to fetch recovery queue');
    return await response.json();
  } catch (error) {
    console.error('Get recovery queue error:', error);
    throw error;
  }
};

export const triggerRecovery = async (agentId, strategy = 'retry') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/recovery/trigger/${agentId}?strategy=${strategy}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to trigger recovery');
    return await response.json();
  } catch (error) {
    console.error('Trigger recovery error:', error);
    throw error;
  }
};

/**
 * Properly restart an agent job in-place.
 * This resets iteration to 0 and re-executes the agent with the same input.
 * Unlike triggerRecovery which creates new agents, this restarts the existing agent.
 */
export const restartAgent = async (agentId, options = {}) => {
  try {
    const params = new URLSearchParams();
    if (options.clearMessages !== undefined) {
      params.append('clear_messages', options.clearMessages);
    }
    if (options.newMaxIterations !== undefined) {
      params.append('new_max_iterations', options.newMaxIterations);
    }
    const queryString = params.toString() ? `?${params.toString()}` : '';

    const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/restart${queryString}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to restart agent');
    return await response.json();
  } catch (error) {
    console.error('Restart agent error:', error);
    throw error;
  }
};

export const scanForStalledAgents = async (thresholdMinutes = 5) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/recovery/scan?threshold_minutes=${thresholdMinutes}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to scan for stalled agents');
    return await response.json();
  } catch (error) {
    console.error('Scan for stalled agents error:', error);
    throw error;
  }
};

export const getRecoveryHistory = async (limit = 50) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/recovery/history?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch recovery history');
    return await response.json();
  } catch (error) {
    console.error('Get recovery history error:', error);
    throw error;
  }
};

// ========== Cost Tracking API ==========

export const getCostSummary = async (days = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/costs/summary?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch cost summary');
    return await response.json();
  } catch (error) {
    console.error('Get cost summary error:', error);
    throw error;
  }
};

export const getCostsByAgent = async (days = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/costs/by-agent?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch costs by agent');
    return await response.json();
  } catch (error) {
    console.error('Get costs by agent error:', error);
    throw error;
  }
};

export const getCostsByModel = async (days = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/costs/by-model?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch costs by model');
    return await response.json();
  } catch (error) {
    console.error('Get costs by model error:', error);
    throw error;
  }
};

export const getCostTrends = async (days = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/costs/trends?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch cost trends');
    return await response.json();
  } catch (error) {
    console.error('Get cost trends error:', error);
    throw error;
  }
};

// ========== Data Retention API ==========

export const getRetentionStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/retention/status`);
    if (!response.ok) throw new Error('Failed to fetch retention status');
    return await response.json();
  } catch (error) {
    console.error('Get retention status error:', error);
    throw error;
  }
};

export const triggerCleanup = async (dryRun = true) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/retention/cleanup?dry_run=${dryRun}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to trigger cleanup');
    return await response.json();
  } catch (error) {
    console.error('Trigger cleanup error:', error);
    throw error;
  }
};

export const archiveSession = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/retention/archive/${sessionId}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to archive session');
    return await response.json();
  } catch (error) {
    console.error('Archive session error:', error);
    throw error;
  }
};

// ========== Streaming Control API ==========

export const getStreamingConfig = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/streaming/config`);
    if (!response.ok) throw new Error('Failed to fetch streaming config');
    return await response.json();
  } catch (error) {
    console.error('Get streaming config error:', error);
    throw error;
  }
};

export const updateStreamingConfig = async (config) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/streaming/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error('Failed to update streaming config');
    return await response.json();
  } catch (error) {
    console.error('Update streaming config error:', error);
    throw error;
  }
};

export const startStreaming = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/streaming/start`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to start streaming');
    return await response.json();
  } catch (error) {
    console.error('Start streaming error:', error);
    throw error;
  }
};

export const stopStreaming = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/streaming/stop`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to stop streaming');
    return await response.json();
  } catch (error) {
    console.error('Stop streaming error:', error);
    throw error;
  }
};

// ========== System Polish API ==========

export const startSystemPolish = async (config = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/system-polish/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scope: config.scope || 'full',
        iterations_per_agent: config.iterationsPerAgent || 100,
        time_range_days: config.timeRangeDays || 30,
        auto_apply: config.autoApply || false,
        focus_areas: config.focusAreas || ['performance', 'costs', 'quality', 'focus', 'redundancy']
      }),
    });
    if (!response.ok) throw new Error('Failed to start system polish');
    return await response.json();
  } catch (error) {
    console.error('Start system polish error:', error);
    throw error;
  }
};

export const getPolishStatus = async (polishId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/system-polish/status/${polishId}`);
    if (!response.ok) throw new Error('Failed to get polish status');
    return await response.json();
  } catch (error) {
    console.error('Get polish status error:', error);
    throw error;
  }
};

export const getPolishHistory = async (limit = 10) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/system-polish/history?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to get polish history');
    return await response.json();
  } catch (error) {
    console.error('Get polish history error:', error);
    throw error;
  }
};

// ========== Guardrail System API ==========

export const getGuardrailStats = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/guardrails/stats`);
    if (!response.ok) throw new Error('Failed to get guardrail stats');
    return await response.json();
  } catch (error) {
    console.error('Get guardrail stats error:', error);
    throw error;
  }
};

export const getGuardrailsForAgent = async (agentType) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/guardrails/agent/${encodeURIComponent(agentType)}`);
    if (!response.ok) throw new Error('Failed to get guardrails for agent');
    return await response.json();
  } catch (error) {
    console.error('Get guardrails for agent error:', error);
    throw error;
  }
};

// ========== Pending Review API ==========

export const getPendingReviews = async (status = 'pending', limit = 50) => {
  try {
    const params = new URLSearchParams({ status, limit: limit.toString() });
    const response = await fetch(`${API_BASE_URL}/api/pending-reviews?${params}`);
    if (!response.ok) throw new Error('Failed to fetch pending reviews');
    return await response.json();
  } catch (error) {
    console.error('Get pending reviews error:', error);
    throw error;
  }
};

export const getPendingReviewContent = async (reviewId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/pending-reviews/${reviewId}/content`);
    if (!response.ok) throw new Error('Failed to fetch review content');
    return await response.json();
  } catch (error) {
    console.error('Get review content error:', error);
    throw error;
  }
};

export const approvePendingReview = async (reviewId, overrideParams = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/pending-reviews/${reviewId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ review_id: reviewId, override_params: overrideParams }),
    });
    if (!response.ok) throw new Error('Failed to approve review');
    return await response.json();
  } catch (error) {
    console.error('Approve review error:', error);
    throw error;
  }
};

export const rejectPendingReview = async (reviewId, reason = '') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/pending-reviews/${reviewId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    });
    if (!response.ok) throw new Error('Failed to reject review');
    return await response.json();
  } catch (error) {
    console.error('Reject review error:', error);
    throw error;
  }
};

export const approveAllPendingReviews = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/pending-reviews/approve-all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) throw new Error('Failed to approve all reviews');
    return await response.json();
  } catch (error) {
    console.error('Approve all reviews error:', error);
    throw error;
  }
};

export const scanForPendingReviews = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/pending-reviews/scan`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to scan for reviews');
    return await response.json();
  } catch (error) {
    console.error('Scan for reviews error:', error);
    throw error;
  }
};

export const reconcilePendingReviews = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/pending-reviews/reconcile`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to reconcile reviews');
    return await response.json();
  } catch (error) {
    console.error('Reconcile reviews error:', error);
    throw error;
  }
};

export const getAgentImprovementReports = async (limit = 50) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent-improvement-reports?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch improvement reports');
    return await response.json();
  } catch (error) {
    console.error('Get improvement reports error:', error);
    throw error;
  }
};

// ========== Agent Stats API ==========

export const getAgentStats = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent-stats`);
    if (!response.ok) throw new Error('Failed to fetch agent stats');
    return await response.json();
  } catch (error) {
    console.error('Get agent stats error:', error);
    throw error;
  }
};

export const getAgentDetails = async (agentClass) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent-stats/${encodeURIComponent(agentClass)}`);
    if (!response.ok) throw new Error('Failed to fetch agent details');
    return await response.json();
  } catch (error) {
    console.error('Get agent details error:', error);
    throw error;
  }
};

export const getRunningAgents = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agents/running`);
    if (!response.ok) throw new Error('Failed to fetch running agents');
    return await response.json();
  } catch (error) {
    console.error('Get running agents error:', error);
    throw error;
  }
};

/**
 * Submit a bug fix request
 * @param {Object} bugData - Bug fix request data
 * @param {string} bugData.bug_description - Description of the bug
 * @param {string[]} [bugData.reproduction_steps] - Steps to reproduce
 * @param {string} [bugData.expected_behavior] - Expected behavior
 * @param {string} [bugData.actual_behavior] - Actual behavior
 * @param {string[]} [bugData.affected_files] - Files that might be affected
 * @param {string} [bugData.priority] - Priority level (critical, high, medium, low)
 * @param {boolean} [bugData.auto_apply] - Whether to auto-apply the fix
 * @param {string} [bugData.budget_tier] - Budget tier for the fix
 */
export const submitBugFix = async (bugData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/fix-bug`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bugData)
    });
    if (!response.ok) throw new Error('Failed to submit bug fix request');
    return await response.json();
  } catch (error) {
    console.error('Submit bug fix error:', error);
    throw error;
  }
};

/**
 * Get list of completed reports (bug fixes, etc.)
 * @param {number} [limit=50] - Maximum number of reports to return
 */
export const getCompletedReports = async (limit = 50) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/completed-reports?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch completed reports');
    return await response.json();
  } catch (error) {
    console.error('Get completed reports error:', error);
    throw error;
  }
};

/**
 * Get the content of a specific completed report
 * @param {string} reportId - ID of the report (filename without extension)
 */
export const getCompletedReportContent = async (reportId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/completed-reports/${encodeURIComponent(reportId)}/content`);
    if (!response.ok) throw new Error('Failed to fetch report content');
    return await response.json();
  } catch (error) {
    console.error('Get completed report content error:', error);
    throw error;
  }
};

/**
 * Spawn a new task from a completed report
 * @param {string} reportId - ID of the source report
 * @param {Object} options - Spawn options
 * @param {string} options.problemDescription - Description of the follow-up task
 * @param {string} [options.budgetTier='balanced'] - Budget tier for the task
 * @param {boolean} [options.autoContinue=true] - Whether to auto-continue through milestones
 * @param {boolean} [options.fullyAutonomous=false] - Whether to bypass all confirmations
 */
export const spawnTaskFromReport = async (reportId, options) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/completed-reports/${encodeURIComponent(reportId)}/spawn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        problem_description: options.problemDescription,
        budget_tier: options.budgetTier || 'balanced',
        auto_continue: options.autoContinue !== false,
        fully_autonomous: options.fullyAutonomous || false
      })
    });
    if (!response.ok) throw new Error('Failed to spawn task from report');
    return await response.json();
  } catch (error) {
    console.error('Spawn task from report error:', error);
    throw error;
  }
};

/**
 * Get tasks that were spawned from a specific report
 * @param {string} reportId - ID of the report to get spawned tasks for
 */
export const getSpawnedTasksForReport = async (reportId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/completed-reports/${encodeURIComponent(reportId)}/spawned-tasks`);
    if (!response.ok) throw new Error('Failed to fetch spawned tasks');
    return await response.json();
  } catch (error) {
    console.error('Get spawned tasks error:', error);
    return { spawned_tasks: [], count: 0 };
  }
};

// ==================== Metrics API ====================

/**
 * Get model performance metrics
 * @param {number} [days=30] - Number of days to include
 */
export const getModelMetrics = async (days = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/metrics/models?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch model metrics');
    return await response.json();
  } catch (error) {
    console.error('Get model metrics error:', error);
    return { models: [] };
  }
};

/**
 * Get agent performance metrics
 * @param {number} [days=30] - Number of days to include
 */
export const getAgentMetrics = async (days = 30) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/metrics/agents?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch agent metrics');
    return await response.json();
  } catch (error) {
    console.error('Get agent metrics error:', error);
    return { agents: [] };
  }
};

// ==================== YOLO Mode API ====================

/**
 * Get current YOLO mode status
 * When enabled, all tasks run fully autonomous without human review
 */
export const getYoloMode = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/yolo-mode`);
    if (!response.ok) throw new Error('Failed to fetch YOLO mode status');
    return await response.json();
  } catch (error) {
    console.error('Get YOLO mode error:', error);
    return { enabled: false };
  }
};

/**
 * Set YOLO mode status
 * @param {boolean} enabled - Whether to enable YOLO mode
 */
export const setYoloMode = async (enabled) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/yolo-mode?enabled=${enabled}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to set YOLO mode');
    return await response.json();
  } catch (error) {
    console.error('Set YOLO mode error:', error);
    throw error;
  }
};

/**
 * Enable YOLO mode (shortcut)
 */
export const enableYoloMode = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/yolo-mode/enable`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to enable YOLO mode');
    return await response.json();
  } catch (error) {
    console.error('Enable YOLO mode error:', error);
    throw error;
  }
};

/**
 * Disable YOLO mode (shortcut)
 */
export const disableYoloMode = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/yolo-mode/disable`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to disable YOLO mode');
    return await response.json();
  } catch (error) {
    console.error('Disable YOLO mode error:', error);
    throw error;
  }
};

// ==================== Swarm Pause/Resume API ====================

/**
 * Get the current swarm pause status
 */
export const getSwarmPauseStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/swarm/pause-status`);
    if (!response.ok) throw new Error('Failed to fetch swarm pause status');
    return await response.json();
  } catch (error) {
    console.error('Get swarm pause status error:', error);
    return { paused: false, running_agents: 0 };
  }
};

/**
 * Pause the entire agent swarm
 * Running agents will stop at their next checkpoint
 * @param {string} [reason] - Optional reason for pausing
 */
export const pauseSwarm = async (reason = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/swarm/pause`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    });
    if (!response.ok) throw new Error('Failed to pause swarm');
    return await response.json();
  } catch (error) {
    console.error('Pause swarm error:', error);
    throw error;
  }
};

/**
 * Resume the agent swarm after a pause
 */
export const resumeSwarm = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/swarm/resume`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to resume swarm');
    return await response.json();
  } catch (error) {
    console.error('Resume swarm error:', error);
    throw error;
  }
};

/**
 * Toggle the swarm pause state
 * @param {string} [reason] - Optional reason if pausing
 */
export const toggleSwarmPause = async (reason = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/swarm/toggle-pause`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    });
    if (!response.ok) throw new Error('Failed to toggle swarm pause');
    return await response.json();
  } catch (error) {
    console.error('Toggle swarm pause error:', error);
    throw error;
  }
};

// ========== Agent Cleanup API ==========

/**
 * Preview agents that would be cleaned up
 * @param {boolean} includeCompleted - Include completed agents
 * @param {boolean} includeRunning - Include running agents
 * @param {boolean} includeFailed - Include failed agents
 */
export const previewCleanup = async (includeCompleted = true, includeRunning = false, includeFailed = true) => {
  try {
    const params = new URLSearchParams({
      include_completed: includeCompleted,
      include_running: includeRunning,
      include_failed: includeFailed
    });
    const response = await fetch(`${API_BASE_URL}/api/swarm/cleanup/preview?${params}`);
    if (!response.ok) throw new Error('Failed to preview cleanup');
    return await response.json();
  } catch (error) {
    console.error('Preview cleanup error:', error);
    throw error;
  }
};

/**
 * Clear agents by status from the UI
 * @param {string[]} statuses - Statuses to clear (e.g., ['completed', 'failed'])
 * @param {boolean} preserveRunning - Always preserve running agents (default true)
 */
export const clearAgentStates = async (statuses = ['completed'], preserveRunning = true) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/swarm/cleanup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        statuses: statuses,
        preserve_running: preserveRunning
      })
    });
    if (!response.ok) throw new Error('Failed to clear agents');
    return await response.json();
  } catch (error) {
    console.error('Clear agents error:', error);
    throw error;
  }
};

/**
 * Clear only completed agents (convenience wrapper)
 */
export const clearCompletedAgents = async () => {
  return clearAgentStates(['completed'], true);
};

/**
 * Clear completed and failed agents
 */
export const clearFinishedAgents = async () => {
  return clearAgentStates(['completed', 'failed', 'error', 'forever_failed'], true);
};

// ========== Agent Definition Management API ==========

/**
 * List all agent definitions by category
 */
export const getAgentDefinitions = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent-definitions`);
    if (!response.ok) throw new Error('Failed to fetch agent definitions');
    return await response.json();
  } catch (error) {
    console.error('Get agent definitions error:', error);
    throw error;
  }
};

/**
 * Get a specific agent definition
 */
export const getAgentDefinition = async (category, filename) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent-definitions/${category}/${filename}`);
    if (!response.ok) throw new Error('Failed to fetch agent definition');
    return await response.json();
  } catch (error) {
    console.error('Get agent definition error:', error);
    throw error;
  }
};

/**
 * Update an agent definition
 */
export const updateAgentDefinition = async (category, filename, content) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent-definitions/${category}/${filename}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    if (!response.ok) throw new Error('Failed to update agent definition');
    return await response.json();
  } catch (error) {
    console.error('Update agent definition error:', error);
    throw error;
  }
};

/**
 * Restore an agent definition from backup
 */
export const restoreAgentDefinition = async (category, filename) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent-definitions/${category}/${filename}/restore`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to restore agent definition');
    return await response.json();
  } catch (error) {
    console.error('Restore agent definition error:', error);
    throw error;
  }
};

/**
 * Get the agent definition template
 */
export const getAgentTemplate = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent-definitions/template`);
    if (!response.ok) throw new Error('Failed to fetch agent template');
    return await response.json();
  } catch (error) {
    console.error('Get agent template error:', error);
    throw error;
  }
};

/**
 * Clear all activities from the activity tracker
 * Note: This clears the in-memory activities, not persisted data
 */
export const clearActivities = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/activity/clear`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to clear activities');
    return await response.json();
  } catch (error) {
    console.error('Clear activities error:', error);
    throw error;
  }
};
