import React, { useState } from 'react';
import { Badge } from 'react-bootstrap';

const AgentHierarchyTree = ({ hierarchy = {} }) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());

  const toggleNode = (agentId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId);
    } else {
      newExpanded.add(agentId);
    }
    setExpandedNodes(newExpanded);
  };

  const getStatusBadge = (status) => {
    const variants = {
      'running': 'warning',
      'completed': 'success',
      'failed': 'danger',
      'awaiting_user_input': 'info'
    };
    return variants[status] || 'secondary';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'running': '⏳',
      'completed': '✅',
      'failed': '❌',
      'awaiting_user_input': '❓'
    };
    return icons[status] || '•';
  };

  const renderNode = (agentId, level = 0) => {
    const node = hierarchy[agentId];
    if (!node) return null;

    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = expandedNodes.has(agentId);
    const indentation = level * 20;

    return (
      <div key={agentId}>
        <div
          onClick={() => hasChildren && toggleNode(agentId)}
          style={{
            padding: '8px 12px',
            paddingLeft: `${indentation + 12}px`,
            marginBottom: '4px',
            backgroundColor: '#1a1d29',
            borderRadius: '4px',
            border: '1px solid #3a3f52',
            cursor: hasChildren ? 'pointer' : 'default',
            transition: 'background-color 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
          onMouseEnter={(e) => hasChildren && (e.currentTarget.style.backgroundColor = '#242836')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#1a1d29')}
        >
          {hasChildren && (
            <span style={{ fontSize: '12px', color: '#6b7280', width: '12px' }}>
              {isExpanded ? '▼' : '▶'}
            </span>
          )}
          {!hasChildren && <span style={{ width: '12px' }} />}

          <span style={{ fontSize: '16px' }}>
            {getStatusIcon(node.status)}
          </span>

          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <strong style={{ fontSize: '13px' }}>{node.agent_name}</strong>
              <Badge bg={getStatusBadge(node.status)} style={{ fontSize: '10px' }}>
                {node.status}
              </Badge>
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                {node.agent_type}
              </span>
            </div>
            <div style={{ fontSize: '10px', color: '#6b7280' }}>
              {node.agent_id}
            </div>
          </div>

          {hasChildren && (
            <Badge bg="info" pill style={{ fontSize: '10px' }}>
              {node.children.length}
            </Badge>
          )}
        </div>

        {hasChildren && isExpanded && (
          <div style={{ marginLeft: '10px' }}>
            {node.children.map(childId => renderNode(childId, level + 1))}
          </div>
        )}
      </div>
    );
  };

  // Find root nodes (no parent or parent not in hierarchy)
  const rootNodes = Object.keys(hierarchy).filter(agentId => {
    const node = hierarchy[agentId];
    return !node.parent_agent_id || !hierarchy[node.parent_agent_id];
  });

  return (
    <div>
      {rootNodes.length === 0 ? (
        <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>
          No agents running. Start a task to see the agent hierarchy here.
        </div>
      ) : (
        rootNodes.map(agentId => renderNode(agentId))
      )}
    </div>
  );
};

export default AgentHierarchyTree;
