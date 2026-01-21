import React, { useState } from 'react';
import { Badge } from 'react-bootstrap';
import { generateWhimsicalName, getAgentEmoji } from '../utils/whimsicalNames';

const STAGE_ICONS = {
  'requirements': '📋',
  'architecture': '🏗️',
  'planning': '📝',
  'implementation': '💻',
  'testing': '🧪',
  'complete': '✅',
  'running': '⚙️',
  'unknown': '❓'
};

const STAGE_COLORS = {
  'requirements': { bg: 'rgba(168, 85, 247, 0.3)', color: '#c4b5fd' },
  'architecture': { bg: 'rgba(59, 130, 246, 0.3)', color: '#93c5fd' },
  'planning': { bg: 'rgba(234, 179, 8, 0.3)', color: '#fde047' },
  'implementation': { bg: 'rgba(249, 115, 22, 0.3)', color: '#fdba74' },
  'testing': { bg: 'rgba(6, 182, 212, 0.3)', color: '#67e8f9' },
  'complete': { bg: 'rgba(34, 197, 94, 0.3)', color: '#86efac' },
  'running': { bg: 'rgba(234, 179, 8, 0.3)', color: '#fde047' },
  'unknown': { bg: 'rgba(107, 114, 128, 0.3)', color: '#d1d5db' }
};

// Agent category colors for type badges
const CATEGORY_COLORS = {
  'leadership': { bg: 'rgba(251, 191, 36, 0.3)', color: '#fbbf24', border: '#fbbf24' },
  'coordinators': { bg: 'rgba(96, 165, 250, 0.3)', color: '#60a5fa', border: '#60a5fa' },
  'developers': { bg: 'rgba(52, 211, 153, 0.3)', color: '#34d399', border: '#34d399' },
  'testers': { bg: 'rgba(167, 139, 250, 0.3)', color: '#a78bfa', border: '#a78bfa' },
  'designers': { bg: 'rgba(244, 114, 182, 0.3)', color: '#f472b6', border: '#f472b6' },
  'support': { bg: 'rgba(249, 115, 22, 0.3)', color: '#f97316', border: '#f97316' },
  'automation': { bg: 'rgba(6, 182, 212, 0.3)', color: '#06b6d4', border: '#06b6d4' }
};

// Get category from agent_type path (e.g., "leadership/executive_director" -> "leadership")
const getAgentCategory = (agentType) => {
  if (!agentType) return 'support';
  const category = agentType.split('/')[0].toLowerCase();
  return CATEGORY_COLORS[category] ? category : 'support';
};

const AgentHierarchyTree = ({ hierarchy = {} }) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [expandedProjects, setExpandedProjects] = useState(new Set());

  const toggleNode = (agentId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId);
    } else {
      newExpanded.add(agentId);
    }
    setExpandedNodes(newExpanded);
  };

  const toggleProject = (projectId) => {
    const newExpanded = new Set(expandedProjects);
    if (newExpanded.has(projectId)) {
      newExpanded.delete(projectId);
    } else {
      newExpanded.add(projectId);
    }
    setExpandedProjects(newExpanded);
  };

  const getStatusBadge = (status) => {
    const variants = {
      'running': 'warning',
      'completed': 'success',
      'failed': 'danger',
      'awaiting_user_input': 'info',
      'stalled': 'warning',
      'recovered': 'primary',
      'forever_failed': 'danger',
      'error': 'danger'
    };
    return variants[status] || 'secondary';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'running': '⏳',
      'completed': '✅',
      'failed': '❌',
      'awaiting_user_input': '❓',
      'stalled': '⚠️',
      'recovered': '🔁',
      'forever_failed': '💀',
      'error': '🔴'
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
            {getAgentEmoji(node.agent_type)}
          </span>

          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <strong style={{ fontSize: '13px' }} title={`${node.agent_name} (${agentId})`}>
                {generateWhimsicalName(agentId)}
              </strong>
              <Badge bg={getStatusBadge(node.status)} style={{ fontSize: '10px' }}>
                {getStatusIcon(node.status)} {node.status}
              </Badge>
              {/* Agent type badge with category color */}
              {node.agent_name && (() => {
                const category = getAgentCategory(node.agent_type);
                const categoryStyle = CATEGORY_COLORS[category] || CATEGORY_COLORS.support;
                return (
                  <span style={{
                    padding: '1px 6px',
                    borderRadius: '3px',
                    fontSize: '9px',
                    fontWeight: '500',
                    backgroundColor: categoryStyle.bg,
                    color: categoryStyle.color,
                    border: `1px solid ${categoryStyle.border}`,
                    whiteSpace: 'nowrap'
                  }}>
                    {node.agent_name}
                  </span>
                );
              })()}
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

  // Group agents by project
  const projectGroups = {};
  rootNodes.forEach(agentId => {
    const node = hierarchy[agentId];
    const projectId = node.project_id || node.request_id || 'default';
    if (!projectGroups[projectId]) {
      projectGroups[projectId] = {
        projectId,
        projectName: node.problem || node.agent_name || 'Unknown Project',
        stage: node.current_stage || 'unknown',
        agents: [],
        stats: { running: 0, completed: 0, failed: 0, awaiting: 0, stalled: 0, recovered: 0 }
      };
    }
    projectGroups[projectId].agents.push(agentId);
    // Count status across all agents in project (including children)
    const countStats = (aid) => {
      const n = hierarchy[aid];
      if (!n) return;
      const status = n.status;
      if (status === 'running') projectGroups[projectId].stats.running++;
      else if (status === 'completed') projectGroups[projectId].stats.completed++;
      else if (status === 'failed' || status === 'error' || status === 'forever_failed') projectGroups[projectId].stats.failed++;
      else if (status === 'awaiting_user_input') projectGroups[projectId].stats.awaiting++;
      else if (status === 'stalled') projectGroups[projectId].stats.stalled++;
      else if (status === 'recovered') projectGroups[projectId].stats.recovered++;
      (n.children || []).forEach(countStats);
    };
    countStats(agentId);
  });

  const renderProjectGroup = (project) => {
    const isExpanded = expandedProjects.has(project.projectId);
    const stageIcon = STAGE_ICONS[project.stage] || STAGE_ICONS.unknown;
    const stageStyle = STAGE_COLORS[project.stage] || STAGE_COLORS.unknown;
    const totalAgents = project.stats.running + project.stats.completed + project.stats.failed + project.stats.awaiting + project.stats.stalled + project.stats.recovered;

    return (
      <div key={project.projectId} style={{ marginBottom: '12px' }}>
        {/* Project Header */}
        <div
          onClick={() => toggleProject(project.projectId)}
          style={{
            padding: '10px 14px',
            backgroundColor: '#242836',
            borderRadius: '6px',
            border: '2px solid #3a3f52',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.borderColor = '#5a5f72'}
          onMouseLeave={(e) => e.currentTarget.style.borderColor = '#3a3f52'}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '12px', color: '#9ca3af', width: '16px', userSelect: 'none' }}>
              {isExpanded ? '▼' : '▶'}
            </span>
            <span style={{ fontSize: '18px' }}>📁</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <strong style={{ fontSize: '14px', color: '#f7fafc' }}>
                  {project.projectName.length > 50 ? project.projectName.slice(0, 50) + '...' : project.projectName}
                </strong>
                <span style={{
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: '500',
                  backgroundColor: stageStyle.bg,
                  color: stageStyle.color
                }}>
                  {stageIcon} {project.stage}
                </span>
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>
                Project ID: {project.projectId}
              </div>
            </div>
            {/* Stats badges */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {project.stats.running > 0 && (
                <Badge bg="warning" pill style={{ fontSize: '10px' }}>
                  {project.stats.running} running
                </Badge>
              )}
              {project.stats.stalled > 0 && (
                <Badge bg="warning" pill style={{ fontSize: '10px' }}>
                  ⚠️ {project.stats.stalled} stalled
                </Badge>
              )}
              {project.stats.recovered > 0 && (
                <Badge bg="primary" pill style={{ fontSize: '10px' }}>
                  🔁 {project.stats.recovered} recovered
                </Badge>
              )}
              {project.stats.completed > 0 && (
                <Badge bg="success" pill style={{ fontSize: '10px' }}>
                  {project.stats.completed} done
                </Badge>
              )}
              {project.stats.failed > 0 && (
                <Badge bg="danger" pill style={{ fontSize: '10px' }}>
                  {project.stats.failed} failed
                </Badge>
              )}
              {project.stats.awaiting > 0 && (
                <Badge bg="info" pill style={{ fontSize: '10px' }}>
                  {project.stats.awaiting} waiting
                </Badge>
              )}
              <Badge bg="secondary" pill style={{ fontSize: '10px' }}>
                {totalAgents} total
              </Badge>
            </div>
          </div>
        </div>

        {/* Expanded agent list */}
        {isExpanded && (
          <div style={{ marginTop: '8px', marginLeft: '20px' }}>
            {project.agents.map(agentId => renderNode(agentId))}
          </div>
        )}
      </div>
    );
  };

  const projects = Object.values(projectGroups);

  return (
    <div>
      {projects.length === 0 ? (
        <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>
          No agents running. Start a task to see the agent hierarchy here.
        </div>
      ) : (
        projects.map(project => renderProjectGroup(project))
      )}
    </div>
  );
};

export default AgentHierarchyTree;
