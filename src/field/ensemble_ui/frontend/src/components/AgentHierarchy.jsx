import React from 'react';
import { Card, Badge } from 'react-bootstrap';

const CATEGORY_COLORS = {
  leadership: '#fbbf24',   // yellow
  coordinators: '#60a5fa', // blue
  developers: '#34d399',   // green
  testers: '#a78bfa',      // purple
  designers: '#f472b6',    // pink
  support: '#f97316',      // orange
  automation: '#06b6d4'    // cyan - for bots/automation
};

const HIERARCHY_DATA = {
  name: 'Executive Director',
  category: 'leadership',
  purpose: 'Strategic coordination',
  children: [
    {
      name: 'Development Manager',
      category: 'leadership',
      purpose: 'Manages development workflow',
      children: [
        {
          name: 'System Architect',
          category: 'leadership',
          purpose: 'Designs system architecture',
          children: []
        },
        {
          name: 'Logistics Manager',
          category: 'support',
          purpose: 'Maps and explores codebases',
          children: []
        },
        {
          name: 'Knowledge Repository',
          category: 'support',
          purpose: 'Maintains project knowledge',
          children: []
        },
        {
          name: 'Drill Writer',
          category: 'support',
          purpose: 'Writes documentation',
          children: []
        },
        {
          name: 'TDD Coordinator',
          category: 'leadership',
          purpose: 'Coordinates TDD workflow',
          children: [
            { name: 'Visual Tech', category: 'support', purpose: 'Refactors code (TDD Refactor)', children: [] }
          ]
        },
        {
          name: 'Backend Coordinator',
          category: 'coordinators',
          purpose: 'Coordinates backend work',
          children: [
            {
              name: 'Backend Lead',
              category: 'developers',
              purpose: 'Leads backend dev',
              children: [
                { name: 'Backend Developer', category: 'developers', purpose: 'Writes backend code', children: [] }
              ]
            },
            {
              name: 'API Lead',
              category: 'developers',
              purpose: 'Leads API dev',
              children: [
                { name: 'API Developer', category: 'developers', purpose: 'Writes API code', children: [] }
              ]
            },
            { name: 'Database Manager', category: 'developers', purpose: 'Manages DB schemas', children: [] }
          ]
        },
        {
          name: 'Frontend Coordinator',
          category: 'coordinators',
          purpose: 'Coordinates frontend work',
          children: [
            {
              name: 'Frontend Lead',
              category: 'developers',
              purpose: 'Leads frontend dev',
              children: [
                { name: 'Frontend Developer', category: 'developers', purpose: 'Writes frontend code', children: [] }
              ]
            },
            { name: 'Style Developer', category: 'designers', purpose: 'Writes CSS/styling', children: [] }
          ]
        },
        {
          name: 'Test Coordinator',
          category: 'coordinators',
          purpose: 'Coordinates testing',
          children: [
            {
              name: 'Unit Test Lead',
              category: 'testers',
              purpose: 'Leads unit testing',
              children: [
                { name: 'Unit Test Writer', category: 'testers', purpose: 'Writes unit tests', children: [] }
              ]
            },
            {
              name: 'Integration Test Lead',
              category: 'testers',
              purpose: 'Leads integration testing',
              children: [
                { name: 'Integration Test Writer', category: 'testers', purpose: 'Writes integration tests', children: [] }
              ]
            },
            { name: 'API Test Writer', category: 'testers', purpose: 'Writes API tests', children: [] }
          ]
        }
      ]
    },
    { name: 'Question Marshal', category: 'leadership', purpose: 'Handles clarification questions', children: [] },
    {
      name: 'Code Quality Director',
      category: 'leadership',
      purpose: 'Ensures code quality',
      children: [
        { name: 'CI Agent', category: 'support', purpose: 'Automated quality gate', children: [] },
        { name: 'Code Reviewer', category: 'support', purpose: 'Reviews code changes', children: [] },
        { name: 'GitHub Commit Bot', category: 'automation', purpose: 'Commits code changes', children: [] },
        { name: 'GitHub Push Bot', category: 'automation', purpose: 'Pushes to remote repos', children: [] },
        { name: 'GitHub Sync Bot', category: 'automation', purpose: 'Syncs with upstream', children: [] },
        { name: 'Documentation Bot', category: 'automation', purpose: 'Generates documentation', children: [] }
      ]
    },
    {
      name: 'System Polish Director',
      category: 'leadership',
      purpose: 'Final polish and refinement',
      children: [
        { name: 'Agent Refactorer', category: 'support', purpose: 'Improves agent definitions', children: [] },
        { name: 'Parameter Enhancer', category: 'support', purpose: 'Enhances failed prompts', children: [] },
        { name: 'State Evolution Agent', category: 'support', purpose: 'Manages state lifecycle', children: [] }
      ]
    },
    { name: 'Bug Fix Director', category: 'leadership', purpose: 'Autonomous bug fixing', children: [] }
  ]
};

function HierarchyNode({ node, level = 0, isLast = false, parentLines = [] }) {
  const hasChildren = node.children && node.children.length > 0;
  const color = CATEGORY_COLORS[node.category] || '#6b7280';

  // Build the prefix with tree lines
  let prefix = '';
  for (let i = 0; i < level; i++) {
    if (parentLines[i]) {
      prefix += '│   ';
    } else {
      prefix += '    ';
    }
  }

  const connector = level === 0 ? '' : (isLast ? '└── ' : '├── ');

  return (
    <div style={{ fontFamily: 'monospace', fontSize: '13px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '4px 0',
          marginLeft: '8px'
        }}
      >
        <span style={{ color: '#6b7280', whiteSpace: 'pre' }}>{prefix}{connector}</span>
        <Badge
          bg="none"
          style={{
            backgroundColor: color,
            color: '#000',
            marginRight: '8px',
            fontSize: '10px',
            fontWeight: 'bold'
          }}
        >
          {node.category.charAt(0).toUpperCase()}
        </Badge>
        <span style={{ color: '#e2e8f0', fontWeight: level < 2 ? 'bold' : 'normal' }}>
          {node.name}
        </span>
        <span style={{ color: '#6b7280', marginLeft: '8px', fontSize: '11px' }}>
          - {node.purpose}
        </span>
      </div>
      {hasChildren && node.children.map((child, idx) => {
        const newParentLines = [...parentLines, !isLast];
        return (
          <HierarchyNode
            key={child.name}
            node={child}
            level={level + 1}
            isLast={idx === node.children.length - 1}
            parentLines={newParentLines}
          />
        );
      })}
    </div>
  );
}

function AgentHierarchy() {
  return (
    <Card bg="dark" text="light" style={{ height: '100%' }}>
      <Card.Header className="d-flex justify-content-between align-items-center">
        <div>
          <strong>Agent Hierarchy</strong>
          <span style={{ color: '#9ca3af', marginLeft: '12px', fontSize: '14px' }}>
            Visual representation of agent spawning relationships
          </span>
        </div>
        <div className="d-flex gap-2">
          {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
            <Badge
              key={cat}
              bg="none"
              style={{ backgroundColor: color, color: '#000', fontSize: '10px' }}
            >
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </Badge>
          ))}
        </div>
      </Card.Header>
      <Card.Body style={{ overflowY: 'auto', backgroundColor: '#1a1d29' }}>
        <HierarchyNode node={HIERARCHY_DATA} />
      </Card.Body>
    </Card>
  );
}

export default AgentHierarchy;
