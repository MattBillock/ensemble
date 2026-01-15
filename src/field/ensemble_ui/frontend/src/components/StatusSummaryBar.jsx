import React from 'react';
import { Badge } from 'react-bootstrap';

const STAGE_ICONS = {
  'requirements': '📋',
  'architecture': '🏗️',
  'planning': '📝',
  'implementation': '💻',
  'testing': '🧪',
  'complete': '✅',
  'unknown': '❓'
};

const StatusSummaryBar = ({ agentStatus = {}, projectsSummary = null }) => {
  // Handle both structures: { agents: {...} } or direct agents object
  const agents = agentStatus?.agents || agentStatus || {};
  const agentEntries = Object.entries(agents);

  // Calculate status counts
  const statusCounts = agentEntries.reduce((acc, [_, info]) => {
    const status = info.status || 'unknown';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});

  // Get projects data from summary API or calculate from agents
  const projects = projectsSummary?.projects || [];
  const activeProjects = projects.filter(p =>
    (p.active_agents || 0) > 0 || statusCounts.running > 0
  ).length || (statusCounts.running > 0 ? 1 : 0);
  const totalProjects = projects.length || (agentEntries.length > 0 ? 1 : 0);

  // Calculate stage distribution
  const stageCounts = projectsSummary?.summary?.stage_distribution || {};
  const activeStages = Object.entries(stageCounts).filter(([_, count]) => count > 0);

  return (
    <div style={{
      backgroundColor: '#1a1d29',
      borderRadius: '8px',
      border: '1px solid #3a3f52',
      padding: '12px 16px',
      marginBottom: '16px',
      display: 'flex',
      alignItems: 'center',
      gap: '24px',
      flexWrap: 'wrap'
    }}>
      {/* Projects Summary */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '20px' }}>📁</span>
        <div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff' }}>
            {activeProjects} / {totalProjects}
          </div>
          <div style={{ fontSize: '10px', color: '#9ca3af' }}>
            active projects
          </div>
        </div>
      </div>

      {/* Divider */}
      <div style={{ width: '1px', height: '40px', backgroundColor: '#3a3f52' }} />

      {/* Status Summary */}
      <div style={{ display: 'flex', gap: '12px' }}>
        {statusCounts.running > 0 && (
          <div style={{ textAlign: 'center' }}>
            <Badge bg="warning" style={{ fontSize: '14px', padding: '6px 12px' }}>
              {statusCounts.running}
            </Badge>
            <div style={{ fontSize: '9px', color: '#9ca3af', marginTop: '2px' }}>running</div>
          </div>
        )}
        {statusCounts.completed > 0 && (
          <div style={{ textAlign: 'center' }}>
            <Badge bg="success" style={{ fontSize: '14px', padding: '6px 12px' }}>
              {statusCounts.completed}
            </Badge>
            <div style={{ fontSize: '9px', color: '#9ca3af', marginTop: '2px' }}>completed</div>
          </div>
        )}
        {(statusCounts.error > 0 || statusCounts.forever_failed > 0) && (
          <div style={{ textAlign: 'center' }}>
            <Badge bg="danger" style={{ fontSize: '14px', padding: '6px 12px' }}>
              {(statusCounts.error || 0) + (statusCounts.forever_failed || 0)}
            </Badge>
            <div style={{ fontSize: '9px', color: '#9ca3af', marginTop: '2px' }}>failed</div>
          </div>
        )}
        {statusCounts.awaiting_user_input > 0 && (
          <div style={{ textAlign: 'center' }}>
            <Badge bg="info" style={{ fontSize: '14px', padding: '6px 12px' }}>
              {statusCounts.awaiting_user_input}
            </Badge>
            <div style={{ fontSize: '9px', color: '#9ca3af', marginTop: '2px' }}>waiting</div>
          </div>
        )}
      </div>

      {/* Divider */}
      {activeStages.length > 0 && (
        <div style={{ width: '1px', height: '40px', backgroundColor: '#3a3f52' }} />
      )}

      {/* Stage Indicators */}
      {activeStages.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '11px', color: '#9ca3af' }}>Stages:</span>
          {activeStages.map(([stage, count]) => (
            <div key={stage} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ fontSize: '16px' }}>{STAGE_ICONS[stage] || STAGE_ICONS.unknown}</span>
              <span style={{ fontSize: '12px', color: '#d1d5db' }}>{stage}</span>
              <Badge bg="secondary" pill style={{ fontSize: '10px' }}>{count}</Badge>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {agentEntries.length === 0 && (
        <div style={{ color: '#9ca3af', fontSize: '13px' }}>
          No active agents. Start a task to see status here.
        </div>
      )}
    </div>
  );
};

export default StatusSummaryBar;
