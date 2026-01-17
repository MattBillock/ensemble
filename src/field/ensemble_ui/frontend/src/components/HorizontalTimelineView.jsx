import React, { useState, useEffect, useRef } from 'react';
import { Badge, Card, Button, Collapse } from 'react-bootstrap';
import { generateWhimsicalName } from '../utils/whimsicalNames';

/**
 * Horizontal Timeline View Component
 *
 * Displays agent execution as horizontal timelines with branching paths.
 * Each request/prompt gets its own track with AI-generated title.
 */
function HorizontalTimelineView({ initialRequestId = null }) {
  const [requests, setRequests] = useState([]);
  const [selectedRequest, setSelectedRequest] = useState(initialRequestId);
  const [timelineData, setTimelineData] = useState(null);
  const [githubInfo, setGithubInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const containerRef = useRef(null);
  const hasInitialized = useRef(false);

  // Handle initialRequestId prop changes
  useEffect(() => {
    if (initialRequestId && initialRequestId !== selectedRequest) {
      setSelectedRequest(initialRequestId);
    }
  }, [initialRequestId]);

  // Fetch requests and GitHub info on mount
  useEffect(() => {
    fetchRequests();
    fetchGitHubInfo();
    const interval = setInterval(fetchRequests, 2000);
    return () => clearInterval(interval);
  }, []);

  // Fetch timeline when request is selected
  useEffect(() => {
    if (selectedRequest) {
      fetchTimeline(selectedRequest);
    }
  }, [selectedRequest]);

  const fetchRequests = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/requests?limit=20');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setRequests(data.requests || []);
      setLoading(false);

      // Auto-select first request if none selected and no initial request provided
      if (!selectedRequest && !hasInitialized.current && data.requests?.length > 0) {
        hasInitialized.current = true;
        setSelectedRequest(data.requests[0].request_id);
      }
    } catch (error) {
      console.error('Error fetching requests:', error);
      setRequests([]);
      setLoading(false);
    }
  };

  const fetchTimeline = async (requestId) => {
    try {
      const response = await fetch(`http://localhost:8001/api/requests/${requestId}/timeline`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setTimelineData(data);
    } catch (error) {
      console.error('Error fetching timeline:', error);
      setTimelineData(null);
    }
  };

  const fetchGitHubInfo = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/git/repo-info');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setGithubInfo(data);
    } catch (error) {
      console.error('Error fetching GitHub info:', error);
      setGithubInfo(null);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return '#fbbf24';
      case 'completed': return '#10b981';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusBg = (status) => {
    switch (status) {
      case 'running': return 'warning';
      case 'completed': return 'success';
      case 'failed': return 'danger';
      default: return 'secondary';
    }
  };

  // Calculate horizontal position as percentage of timeline
  const calculatePosition = (timestamp, timelineStart, timelineEnd) => {
    if (!timestamp || !timelineStart || !timelineEnd) return 0;
    const start = new Date(timelineStart).getTime();
    const end = new Date(timelineEnd).getTime();
    const current = new Date(timestamp).getTime();
    const duration = end - start || 1;
    return Math.min(100, Math.max(0, ((current - start) / duration) * 100));
  };

  // Build tree structure for agents
  const buildAgentTree = (agents) => {
    if (!agents || agents.length === 0) return [];

    const agentMap = {};
    agents.forEach(a => { agentMap[a.agent_id] = { ...a, children: [] }; });

    const roots = [];
    agents.forEach(a => {
      if (a.parent_id && agentMap[a.parent_id]) {
        agentMap[a.parent_id].children.push(agentMap[a.agent_id]);
      } else {
        roots.push(agentMap[a.agent_id]);
      }
    });

    return roots;
  };

  // Render SVG timeline for a request
  const renderTimeline = () => {
    if (!timelineData || !timelineData.agents) return null;

    const { agents, timeline, deliverables } = timelineData;
    const agentTree = buildAgentTree(agents);
    const svgWidth = Math.max(800, agents.length * 120);
    const trackHeight = 70;
    const padding = 60;

    // Calculate depths for vertical positioning
    const calculateDepths = (node, depth = 0) => {
      node.depth = depth;
      let maxDepth = depth;
      node.children.forEach(child => {
        maxDepth = Math.max(maxDepth, calculateDepths(child, depth + 1));
      });
      return maxDepth;
    };

    let maxDepth = 0;
    agentTree.forEach(root => {
      maxDepth = Math.max(maxDepth, calculateDepths(root, 0));
    });

    const svgHeight = (maxDepth + 1) * trackHeight + padding * 2;

    // Render agent node
    const renderNode = (agent, index) => {
      const x = calculatePosition(agent.started_at, timeline.start, timeline.end);
      const xPixel = padding + (x / 100) * (svgWidth - padding * 2);
      const y = padding + agent.depth * trackHeight;
      const isSelected = selectedAgent?.agent_id === agent.agent_id;

      return (
        <g key={agent.agent_id}>
          {/* Connection line to parent */}
          {agent.parent_id && (() => {
            const parent = agents.find(a => a.agent_id === agent.parent_id);
            if (parent) {
              const parentX = calculatePosition(parent.started_at, timeline.start, timeline.end);
              const parentXPixel = padding + (parentX / 100) * (svgWidth - padding * 2);
              const parentY = padding + (parent.depth || 0) * trackHeight;
              return (
                <path
                  d={`M ${parentXPixel} ${parentY}
                      C ${parentXPixel + 30} ${parentY},
                        ${xPixel - 30} ${y},
                        ${xPixel} ${y}`}
                  fill="none"
                  stroke="#4f5668"
                  strokeWidth="2"
                  strokeDasharray="5,3"
                />
              );
            }
          })()}

          {/* Agent node */}
          <g
            transform={`translate(${xPixel}, ${y})`}
            style={{ cursor: 'pointer' }}
            onClick={() => setSelectedAgent(agent)}
          >
            {/* Pulse animation for running agents */}
            {agent.status === 'running' && (
              <circle
                r="20"
                fill="none"
                stroke={getStatusColor(agent.status)}
                strokeWidth="2"
                opacity="0.5"
              >
                <animate
                  attributeName="r"
                  from="16"
                  to="24"
                  dur="1.5s"
                  repeatCount="indefinite"
                />
                <animate
                  attributeName="opacity"
                  from="0.6"
                  to="0"
                  dur="1.5s"
                  repeatCount="indefinite"
                />
              </circle>
            )}

            {/* Main circle */}
            <circle
              r="16"
              fill={getStatusColor(agent.status)}
              stroke={isSelected ? '#fff' : getStatusColor(agent.status)}
              strokeWidth={isSelected ? 3 : 2}
            />

            {/* Status icon */}
            <text
              textAnchor="middle"
              dominantBaseline="central"
              fontSize="12"
              fill="#fff"
            >
              {agent.status === 'running' ? '...' :
               agent.status === 'completed' ? '✓' :
               agent.status === 'failed' ? '✗' : '?'}
            </text>

            {/* Agent name label (whimsical) */}
            <text
              y="28"
              textAnchor="middle"
              fontSize="10"
              fill="#e4e6eb"
            >
              {(() => {
                const whimsicalName = generateWhimsicalName(agent.agent_id);
                return whimsicalName.length > 15
                  ? whimsicalName.substring(0, 12) + '...'
                  : whimsicalName;
              })()}
            </text>
            {/* Agent type label */}
            <text
              y="40"
              textAnchor="middle"
              fontSize="8"
              fill="#9ca3af"
            >
              {agent.agent_name.length > 18
                ? agent.agent_name.substring(0, 15) + '...'
                : agent.agent_name}
            </text>
          </g>
        </g>
      );
    };

    // Flatten tree for rendering
    const flattenTree = (nodes, result = []) => {
      nodes.forEach(node => {
        result.push(node);
        if (node.children) {
          flattenTree(node.children, result);
        }
      });
      return result;
    };

    const allNodes = flattenTree(agentTree);

    return (
      <svg
        width={svgWidth}
        height={svgHeight}
        style={{ minWidth: '100%' }}
      >
        {/* Background grid lines */}
        {[0, 25, 50, 75, 100].map(pct => (
          <line
            key={pct}
            x1={padding + (pct / 100) * (svgWidth - padding * 2)}
            y1={padding - 20}
            x2={padding + (pct / 100) * (svgWidth - padding * 2)}
            y2={svgHeight - padding + 20}
            stroke="#3a3f52"
            strokeWidth="1"
            strokeDasharray="2,4"
          />
        ))}

        {/* Main timeline axis */}
        <line
          x1={padding}
          y1={padding}
          x2={svgWidth - padding}
          y2={padding}
          stroke="#4f5668"
          strokeWidth="2"
        />

        {/* Arrow at end */}
        <polygon
          points={`${svgWidth - padding},${padding} ${svgWidth - padding - 10},${padding - 5} ${svgWidth - padding - 10},${padding + 5}`}
          fill="#4f5668"
        />

        {/* Render all agent nodes */}
        {allNodes.map((agent, i) => renderNode(agent, i))}
      </svg>
    );
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        color: '#9ca3af'
      }}>
        Loading timeline...
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      height: '100%',
      backgroundColor: '#1a1d29',
      overflow: 'hidden'
    }}>
      {/* Left sidebar - Request list */}
      <div style={{
        width: '280px',
        borderRight: '1px solid #3a3f52',
        overflowY: 'auto',
        flexShrink: 0
      }}>
        <div style={{
          padding: '12px',
          borderBottom: '1px solid #3a3f52',
          position: 'sticky',
          top: 0,
          backgroundColor: '#1a1d29',
          zIndex: 10
        }}>
          <h6 style={{ margin: 0, color: '#e4e6eb', fontSize: '14px' }}>
            Requests ({requests.length})
          </h6>
        </div>

        {requests.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>
            No requests yet
          </div>
        ) : (
          requests.map(req => (
            <div
              key={req.request_id}
              onClick={() => setSelectedRequest(req.request_id)}
              style={{
                padding: '12px',
                borderBottom: '1px solid #3a3f52',
                cursor: 'pointer',
                backgroundColor: selectedRequest === req.request_id ? '#242836' : 'transparent',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={e => {
                if (selectedRequest !== req.request_id) {
                  e.currentTarget.style.backgroundColor = '#1e2130';
                }
              }}
              onMouseLeave={e => {
                if (selectedRequest !== req.request_id) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '4px'
              }}>
                <span style={{
                  color: '#e4e6eb',
                  fontSize: '13px',
                  fontWeight: 500,
                  flex: 1
                }}>
                  {req.title || req.prompt_preview || 'Generating title...'}
                </span>
                <Badge bg={getStatusBg(req.status)} style={{ fontSize: '10px', marginLeft: '8px' }}>
                  {req.status}
                </Badge>
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>
                {new Date(req.created_at).toLocaleTimeString()}
                <span style={{ marginLeft: '8px' }}>
                  {req.request_id}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Main content - Timeline */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Timeline header */}
        {timelineData?.request && (
          <div style={{
            padding: '16px',
            borderBottom: '1px solid #3a3f52',
            backgroundColor: '#242836'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h5 style={{ margin: 0, color: '#e4e6eb', fontSize: '16px' }}>
                  {timelineData.request.title || 'Processing...'}
                </h5>
                <p style={{ margin: '4px 0 0', color: '#9ca3af', fontSize: '12px' }}>
                  {timelineData.timeline?.agent_count || 0} agents |
                  {' '}{timelineData.timeline?.file_count || 0} files |
                  {' '}{timelineData.timeline?.commit_count || 0} commits
                </p>
              </div>
              {githubInfo?.repo_url && (
                <a
                  href={githubInfo.repo_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: '#58a6ff', fontSize: '12px', textDecoration: 'none' }}
                >
                  View on GitHub
                </a>
              )}
            </div>
          </div>
        )}

        {/* Timeline visualization */}
        <div
          ref={containerRef}
          style={{
            flex: 1,
            overflowX: 'auto',
            overflowY: 'auto',
            padding: '20px'
          }}
        >
          {timelineData ? renderTimeline() : (
            <div style={{ color: '#6b7280', textAlign: 'center', paddingTop: '40px' }}>
              Select a request to view timeline
            </div>
          )}
        </div>
      </div>

      {/* Right sidebar - Agent details */}
      {selectedAgent && (
        <div style={{
          width: '350px',
          borderLeft: '1px solid #3a3f52',
          overflowY: 'auto',
          backgroundColor: '#242836',
          flexShrink: 0
        }}>
          <div style={{
            padding: '12px',
            borderBottom: '1px solid #3a3f52',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            position: 'sticky',
            top: 0,
            backgroundColor: '#242836',
            zIndex: 10
          }}>
            <h6 style={{ margin: 0, color: '#e4e6eb', fontSize: '14px' }}>
              Agent Details
            </h6>
            <Button
              variant="link"
              size="sm"
              onClick={() => setSelectedAgent(null)}
              style={{ color: '#9ca3af', padding: 0 }}
            >
              Close
            </Button>
          </div>

          <div style={{ padding: '16px' }}>
            {/* Agent info */}
            <div style={{ marginBottom: '16px' }}>
              <h6 style={{ color: '#e4e6eb', marginBottom: '8px' }}>
                {generateWhimsicalName(selectedAgent.agent_id)}
              </h6>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                <Badge bg="secondary" style={{ fontSize: '10px' }}>
                  {selectedAgent.agent_name}
                </Badge>
                <Badge bg={getStatusBg(selectedAgent.status)}>
                  {selectedAgent.status}
                </Badge>
                {selectedAgent.agent_type && (
                  <span style={{ color: '#6b7280', fontSize: '11px' }}>
                    {selectedAgent.agent_type}
                  </span>
                )}
              </div>
            </div>

            {/* Progress */}
            {selectedAgent.status === 'running' && selectedAgent.max_iterations && (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>
                  Progress: {selectedAgent.current_iteration}/{selectedAgent.max_iterations}
                </div>
                <div style={{
                  height: '4px',
                  backgroundColor: '#3a3f52',
                  borderRadius: '2px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${(selectedAgent.current_iteration / (selectedAgent.max_iterations || 1)) * 100}%`,
                    height: '100%',
                    backgroundColor: '#fbbf24',
                    transition: 'width 0.3s'
                  }} />
                </div>
              </div>
            )}

            {/* Current task */}
            {selectedAgent.current_task && (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>
                  Current Task
                </div>
                <div style={{ fontSize: '12px', color: '#e4e6eb' }}>
                  {selectedAgent.current_task}
                </div>
              </div>
            )}

            {/* Summary */}
            {selectedAgent.summary && (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>
                  Summary
                </div>
                <div style={{
                  fontSize: '12px',
                  color: '#e4e6eb',
                  backgroundColor: '#1a1d29',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #3a3f52'
                }}>
                  {selectedAgent.summary}
                </div>
              </div>
            )}

            {/* Deliverables */}
            {selectedAgent.deliverables?.length > 0 && (
              <div>
                <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '8px' }}>
                  Deliverables ({selectedAgent.deliverables.length})
                </div>
                {selectedAgent.deliverables.map((d, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '8px',
                      backgroundColor: '#1a1d29',
                      borderRadius: '4px',
                      marginBottom: '4px',
                      border: '1px solid #3a3f52',
                      fontSize: '12px',
                      color: '#e4e6eb'
                    }}
                  >
                    {d}
                  </div>
                ))}
              </div>
            )}

            {/* Timestamps */}
            <div style={{ marginTop: '16px', fontSize: '11px', color: '#6b7280' }}>
              {selectedAgent.started_at && (
                <div>Started: {new Date(selectedAgent.started_at).toLocaleString()}</div>
              )}
              {selectedAgent.completed_at && (
                <div>Completed: {new Date(selectedAgent.completed_at).toLocaleString()}</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HorizontalTimelineView;
