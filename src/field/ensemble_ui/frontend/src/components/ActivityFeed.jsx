import React, { useState } from 'react';
import { Card, Badge, Button, Collapse } from 'react-bootstrap';
import ReactMarkdown from 'react-markdown';

const ActivityFeed = ({ activities = [] }) => {
  const [expandedActivities, setExpandedActivities] = useState(new Set());

  const toggleActivity = (index) => {
    const newExpanded = new Set(expandedActivities);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedActivities(newExpanded);
  };

  const getActivityIcon = (type) => {
    const icons = {
      'agent_started': '🚀',
      'agent_completed': '✅',
      'agent_failed': '❌',
      'iteration_started': '🔄',
      'iteration_completed': '✓',
      'tool_use_started': '🔧',
      'tool_use_completed': '✓',
      'tool_use_failed': '❌',
      'agent_spawned': '👶',
      'thinking': '💭',
      'message': '💬',
      'question': '❓',
      'answer': '💡',
      'task_update': '📝',
      'status_change': '🔄'
    };
    return icons[type] || '•';
  };

  const getActivityColor = (type) => {
    if (type.includes('failed') || type.includes('error')) return 'danger';
    if (type.includes('completed')) return 'success';
    if (type.includes('started')) return 'info';
    if (type === 'question') return 'warning';
    return 'secondary';
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 1
    });
  };

  const renderActivityDetails = (activity) => {
    const { activity_type, data } = activity;

    switch (activity_type) {
      case 'agent_started':
        return (
          <div>
            <div><strong>Agent Type:</strong> {data.agent_type}</div>
            <div><strong>Model:</strong> {data.model}</div>
            {data.input_data && (
              <details className="mt-2">
                <summary style={{ cursor: 'pointer' }}>Input Data</summary>
                <pre style={{ fontSize: '11px', marginTop: '8px' }}>
                  {JSON.stringify(data.input_data, null, 2)}
                </pre>
              </details>
            )}
          </div>
        );

      case 'iteration_started':
        return (
          <div>
            <div><strong>Iteration:</strong> {data.iteration} / {data.max_iterations}</div>
            {data.prompt && (
              <div className="mt-2" style={{ fontSize: '12px', color: '#9ca3af' }}>
                {data.prompt}
              </div>
            )}
          </div>
        );

      case 'tool_use_started':
      case 'tool_use_completed':
      case 'tool_use_failed':
        return (
          <div>
            <div><strong>Tool:</strong> {data.tool_name}</div>
            <div><strong>Status:</strong> {data.status}</div>
            {data.tool_inputs && (
              <details className="mt-2">
                <summary style={{ cursor: 'pointer' }}>Tool Inputs</summary>
                <pre style={{ fontSize: '11px', marginTop: '8px' }}>
                  {JSON.stringify(data.tool_inputs, null, 2)}
                </pre>
              </details>
            )}
          </div>
        );

      case 'agent_spawned':
        return (
          <div>
            <div><strong>Spawned Agent:</strong> {data.spawned_agent_name}</div>
            <div><strong>Agent ID:</strong> {data.spawned_agent_id}</div>
          </div>
        );

      case 'message':
        return (
          <div>
            <Badge bg={data.message_type === 'error' ? 'danger' : 'info'} className="mb-2">
              {data.message_type}
            </Badge>
            <div>{data.message}</div>
          </div>
        );

      case 'question':
        return (
          <div>
            <div><strong>Question:</strong> {data.question}</div>
            {data.options && data.options.length > 0 && (
              <div className="mt-2">
                <strong>Options:</strong>
                <ul className="mb-0">
                  {data.options.map((opt, idx) => (
                    <li key={idx}>{opt}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );

      case 'agent_completed':
        return (
          <div>
            {data.result && data.result.summary && (
              <div style={{
                marginBottom: '8px',
                paddingLeft: '8px',
                borderLeft: '2px solid #10b981',
                color: '#a7f3d0'
              }}>
                <strong>Summary:</strong> {data.result.summary}
              </div>
            )}
            {data.result && data.result.deliverables && data.result.deliverables.length > 0 && (
              <div style={{ marginBottom: '8px', color: '#93c5fd' }}>
                📦 <strong>{data.result.deliverables.length} deliverable(s)</strong>
              </div>
            )}
            {data.result && (
              <details className="mt-2">
                <summary style={{ cursor: 'pointer' }}>Full Result</summary>
                <pre style={{ fontSize: '11px', marginTop: '8px' }}>
                  {JSON.stringify(data.result, null, 2)}
                </pre>
              </details>
            )}
          </div>
        );

      case 'agent_failed':
        return (
          <div>
            <div><strong>Error:</strong> {data.error}</div>
            {data.traceback && (
              <details className="mt-2">
                <summary style={{ cursor: 'pointer' }}>Traceback</summary>
                <pre style={{ fontSize: '10px', marginTop: '8px', color: '#ef4444' }}>
                  {data.traceback}
                </pre>
              </details>
            )}
          </div>
        );

      default:
        return (
          <pre style={{ fontSize: '11px' }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        );
    }
  };

  return (
    <div>
      {activities.length === 0 ? (
        <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>
          No activities yet. Start a task to see agent activity here.
        </div>
      ) : (
        activities.map((activity, index) => {
          const isExpanded = expandedActivities.has(index);
          const icon = getActivityIcon(activity.activity_type);
          const color = getActivityColor(activity.activity_type);

          return (
            <div
              key={index}
              style={{
                marginBottom: '8px',
                backgroundColor: '#1a1d29',
                borderRadius: '4px',
                border: '1px solid #3a3f52',
                overflow: 'hidden'
              }}
            >
              <div
                onClick={() => toggleActivity(index)}
                style={{
                  padding: '10px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#242836'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <span style={{ fontSize: '18px' }}>{icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <strong style={{ fontSize: '13px' }}>{activity.agent_name}</strong>
                    <Badge bg={color} style={{ fontSize: '10px' }}>
                      {activity.activity_type.replace(/_/g, ' ')}
                    </Badge>
                    {activity.iteration && (
                      <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                        iter {activity.iteration}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '11px', color: '#9ca3af' }}>
                    {formatTimestamp(activity.timestamp)}
                  </div>
                </div>
                <span style={{ fontSize: '12px', color: '#6b7280' }}>
                  {isExpanded ? '▼' : '▶'}
                </span>
              </div>

              <Collapse in={isExpanded}>
                <div style={{
                  padding: '12px',
                  borderTop: '1px solid #3a3f52',
                  backgroundColor: '#0f1117',
                  fontSize: '12px'
                }}>
                  {renderActivityDetails(activity)}
                </div>
              </Collapse>
            </div>
          );
        })
      )}
    </div>
  );
};

export default ActivityFeed;
