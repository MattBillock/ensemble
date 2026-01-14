import React, { useState, useEffect } from 'react';

/**
 * Pipeline Tree View Component
 *
 * Displays the hierarchical structure of agents spawned from a prompt,
 * showing parent-child relationships and execution results.
 */
function PipelineTreeView({ requestId, onClose }) {
  const [hierarchy, setHierarchy] = useState({});
  const [agentStates, setAgentStates] = useState({});
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPipelineData();
    const interval = setInterval(fetchPipelineData, 2000); // Refresh every 2 seconds
    return () => clearInterval(interval);
  }, [requestId]);

  const fetchPipelineData = async () => {
    try {
      // Fetch hierarchy and states in parallel
      const [hierarchyRes, statesRes] = await Promise.all([
        fetch(`http://localhost:8001/api/activity/hierarchy${requestId ? `?request_id=${requestId}` : ''}`),
        fetch('http://localhost:8001/api/activity/states')
      ]);

      const hierarchyData = await hierarchyRes.json();
      const statesData = await statesRes.json();

      setHierarchy(hierarchyData.hierarchy || {});
      setAgentStates(statesData.agent_states || {});
      setLoading(false);
    } catch (err) {
      console.error('Error fetching pipeline data:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const toggleNode = (agentId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId);
    } else {
      newExpanded.add(agentId);
    }
    setExpandedNodes(newExpanded);
  };

  const getStatusColor = (status) => {
    const colors = {
      'running': 'text-blue-400',
      'completed': 'text-green-400',
      'failed': 'text-red-400',
      'awaiting_user_input': 'text-yellow-400'
    };
    return colors[status] || 'text-gray-400';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'running': '⚙️',
      'completed': '✅',
      'failed': '❌',
      'awaiting_user_input': '❓'
    };
    return icons[status] || '•';
  };

  const renderAgent = (agentId, depth = 0) => {
    const agent = hierarchy[agentId];
    const state = agentStates[agentId];

    if (!agent) return null;

    const hasChildren = agent.children && agent.children.length > 0;
    const isExpanded = expandedNodes.has(agentId);
    const indentClass = `ml-${depth * 6}`;

    return (
      <div key={agentId} className="mb-2">
        <div
          className={`bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-colors cursor-pointer ${indentClass}`}
          style={{ marginLeft: `${depth * 24}px` }}
          onClick={() => hasChildren && toggleNode(agentId)}
        >
          <div className="p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 flex-1">
                {hasChildren && (
                  <span className="text-gray-400 text-xs">
                    {isExpanded ? '▼' : '▶'}
                  </span>
                )}
                {!hasChildren && <span className="text-xs ml-3"></span>}

                <span className={`text-sm font-semibold ${getStatusColor(agent.status)}`}>
                  {getStatusIcon(agent.status)} {agent.agent_name}
                </span>

                <span className="text-xs text-gray-500 font-mono">
                  {agentId}
                </span>
              </div>

              <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                agent.status === 'completed' ? 'bg-green-500/30 text-green-200' :
                agent.status === 'failed' ? 'bg-red-500/30 text-red-200' :
                agent.status === 'running' ? 'bg-blue-500/30 text-blue-200' :
                'bg-yellow-500/30 text-yellow-200'
              }`}>
                {agent.status}
              </span>
            </div>

            <div className="mt-2 text-xs text-gray-400">
              Type: {agent.agent_type}
            </div>

            {state && agent.status === 'running' && (
              <div className="mt-1 text-xs text-blue-300">
                Current: {state.current_task}
                {state.current_iteration > 0 && (
                  <span className="ml-2">
                    (iteration {state.current_iteration}/{state.max_iterations})
                  </span>
                )}
              </div>
            )}

            {state && agent.status === 'completed' && state.summary && (
              <div className="mt-2 text-xs text-green-300 border-l-2 border-green-500/50 pl-2">
                <span className="font-semibold">Summary: </span>
                {state.summary.length > 150
                  ? `${state.summary.substring(0, 150)}...`
                  : state.summary}
              </div>
            )}

            {state && state.deliverables && state.deliverables.length > 0 && (
              <div className="mt-1 text-xs text-blue-300">
                📦 {state.deliverables.length} deliverable(s)
              </div>
            )}

            {agent.started_at && (
              <div className="mt-1 text-xs text-gray-500">
                Started: {new Date(agent.started_at).toLocaleTimeString()}
                {agent.completed_at && (
                  <span className="ml-2">
                    • Completed: {new Date(agent.completed_at).toLocaleTimeString()}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Render children recursively */}
        {hasChildren && isExpanded && (
          <div className="mt-1">
            {agent.children.map(childId => renderAgent(childId, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  // Find root agents (agents with no parent)
  const getRootAgents = () => {
    return Object.keys(hierarchy).filter(agentId => {
      const agent = hierarchy[agentId];
      return !agent.parent_agent_id || !(agent.parent_agent_id in hierarchy);
    });
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-400">Loading pipeline...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-red-400">Error: {error}</div>
      </div>
    );
  }

  const rootAgents = getRootAgents();

  return (
    <div className="h-full flex flex-col bg-gray-900">
      <div className="flex-shrink-0 border-b border-white/10 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-white">Pipeline Tree View</h3>
            <p className="text-xs text-gray-400">
              {requestId ? `Request: ${requestId}` : 'All agents'}
            </p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {rootAgents.length === 0 ? (
          <div className="text-center text-gray-500 italic py-8">
            No agents in pipeline yet
          </div>
        ) : (
          <div className="space-y-2">
            {rootAgents.map(agentId => renderAgent(agentId, 0))}
          </div>
        )}
      </div>

      <div className="flex-shrink-0 border-t border-white/10 p-3 bg-gray-800/50">
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-1">
            <span className="text-blue-400">⚙️</span> Running
          </div>
          <div className="flex items-center gap-1">
            <span className="text-green-400">✅</span> Completed
          </div>
          <div className="flex items-center gap-1">
            <span className="text-red-400">❌</span> Failed
          </div>
          <div className="flex items-center gap-1">
            <span className="text-yellow-400">❓</span> Waiting
          </div>
        </div>
      </div>
    </div>
  );
}

export default PipelineTreeView;
