import React, { useState, useEffect } from 'react';
import { Card, Badge, Spinner, Alert } from 'react-bootstrap';
import { getAgentDefinitionHierarchy } from '../services/api';

// Default category colors - will work for any discovered category
const DEFAULT_CATEGORY_COLORS = {
  leadership: '#fbbf24',   // yellow
  coordinators: '#60a5fa', // blue
  developers: '#34d399',   // green
  testers: '#a78bfa',      // purple
  designers: '#f472b6',    // pink
  support: '#f97316',      // orange
  automation: '#06b6d4'    // cyan
};

const getCategoryColor = (category) => {
  if (DEFAULT_CATEGORY_COLORS[category]) {
    return DEFAULT_CATEGORY_COLORS[category];
  }
  // Generate consistent color for unknown categories
  let hash = 0;
  for (let i = 0; i < category.length; i++) {
    hash = category.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = hash % 360;
  return `hsl(${hue}, 60%, 60%)`;
};

function HierarchyNode({ node, level = 0, isLast = false, parentLines = [] }) {
  const hasChildren = node.children && node.children.length > 0;
  const color = getCategoryColor(node.category);

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
            key={child.path || child.name}
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

// Build tree structure from flat hierarchy data
function buildTree(hierarchy, roots) {
  const buildNode = (agentPath) => {
    const agent = hierarchy[agentPath];
    if (!agent) return null;

    return {
      name: agent.name,
      category: agent.category,
      purpose: agent.purpose || 'No description',
      path: agentPath,
      children: (agent.children || []).map(child => ({
        name: child.name,
        category: child.category,
        purpose: hierarchy[child.path]?.purpose || 'No description',
        path: child.path,
        children: buildNode(child.path)?.children || []
      }))
    };
  };

  // Build trees starting from root agents
  return roots.map(rootPath => buildNode(rootPath)).filter(Boolean);
}

function AgentHierarchy() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [trees, setTrees] = useState([]);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetchHierarchy();
  }, []);

  const fetchHierarchy = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAgentDefinitionHierarchy();
      const builtTrees = buildTree(data.agents, data.roots);
      setTrees(builtTrees);
      setCategories(data.categories || []);
    } catch (err) {
      setError('Failed to load agent hierarchy');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card bg="dark" text="light" style={{ height: '100%' }}>
        <Card.Body className="d-flex align-items-center justify-content-center">
          <Spinner animation="border" variant="primary" />
          <span className="ms-2">Loading hierarchy...</span>
        </Card.Body>
      </Card>
    );
  }

  if (error) {
    return (
      <Card bg="dark" text="light" style={{ height: '100%' }}>
        <Card.Body>
          <Alert variant="danger">{error}</Alert>
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card bg="dark" text="light" style={{ height: '100%' }}>
      <Card.Header className="d-flex justify-content-between align-items-center">
        <div>
          <strong>Agent Hierarchy</strong>
          <span style={{ color: '#9ca3af', marginLeft: '12px', fontSize: '14px' }}>
            Dynamically built from agent spawn permissions
          </span>
        </div>
        <div className="d-flex gap-2">
          {categories.map(cat => (
            <Badge
              key={cat}
              bg="none"
              style={{ backgroundColor: getCategoryColor(cat), color: '#000', fontSize: '10px' }}
            >
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </Badge>
          ))}
        </div>
      </Card.Header>
      <Card.Body style={{ overflowY: 'auto', backgroundColor: '#1a1d29' }}>
        {trees.length === 0 ? (
          <div style={{ color: '#9ca3af', textAlign: 'center', padding: '20px' }}>
            No agent hierarchy found. Check that agent definitions have spawn permissions defined.
          </div>
        ) : (
          trees.map((tree, idx) => (
            <HierarchyNode key={tree.path || idx} node={tree} />
          ))
        )}
      </Card.Body>
    </Card>
  );
}

export default AgentHierarchy;
