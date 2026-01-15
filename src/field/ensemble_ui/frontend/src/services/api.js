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
