import React, { useState, useEffect, useCallback } from 'react';
import {
  Container, Row, Col, Card, Spinner, Badge, ListGroup, Alert, Button,
  Form, ButtonGroup, Accordion
} from 'react-bootstrap';
import {
  getAgentDefinitions,
  getAgentDefinition,
  updateAgentDefinition,
  restoreAgentDefinition,
  getAgentTemplate,
  getAgentCategories
} from '../services/api';

// Default category metadata - will be merged with dynamically discovered categories
const DEFAULT_CATEGORY_META = {
  leadership: { icon: '👑', color: 'warning', description: 'Strategic agents that coordinate the overall development process' },
  coordinators: { icon: '🎭', color: 'info', description: 'Agents that break down tasks and delegate to developers/testers' },
  developers: { icon: '💻', color: 'success', description: 'Agents that write code - frontend, backend, and API' },
  testers: { icon: '🧪', color: 'primary', description: 'Agents that write tests - unit, integration, and API' },
  designers: { icon: '🎨', color: 'secondary', description: 'Agents that handle styling and design' },
  support: { icon: '🛠️', color: 'danger', description: 'Cross-cutting agents for code review, documentation, and refactoring' },
  automation: { icon: '🤖', color: 'light', description: 'GitHub integration bots for commits, pushes, and syncing' }
};

// Generate default metadata for unknown categories
const getDefaultCategoryMeta = (category) => {
  if (DEFAULT_CATEGORY_META[category]) {
    return DEFAULT_CATEGORY_META[category];
  }
  // Generate fallback for unknown categories
  return {
    icon: '📁',
    color: 'secondary',
    description: `Agents in the ${category} category`
  };
};

// Helper functions to get category metadata dynamically
const getCategoryIcon = (category) => getDefaultCategoryMeta(category).icon;
const getCategoryColor = (category) => getDefaultCategoryMeta(category).color;
const getCategoryDescription = (category) => getDefaultCategoryMeta(category).description;

function AgentStats() {
  const [loading, setLoading] = useState(true);
  const [definitions, setDefinitions] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentContent, setAgentContent] = useState(null);
  const [editedContent, setEditedContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [activeCategory, setActiveCategory] = useState('leadership');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchDefinitions();
  }, []);

  const fetchDefinitions = async () => {
    setLoading(true);
    try {
      const data = await getAgentDefinitions();
      setDefinitions(data);
      // Set activeCategory to first available if current doesn't exist
      const categories = data?.categories ? Object.keys(data.categories) : [];
      if (categories.length > 0 && !categories.includes(activeCategory)) {
        setActiveCategory(categories[0]);
      }
    } catch (err) {
      setError('Failed to load agent definitions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAgent = async (category, filename) => {
    try {
      setError(null);
      const data = await getAgentDefinition(category, filename);
      setAgentContent(data);
      setSelectedAgent({ category, filename });
      setEditedContent(data.content);
      setIsEditing(false);
    } catch (err) {
      setError('Failed to load agent definition');
      console.error(err);
    }
  };

  const handleSave = async () => {
    if (!selectedAgent) return;
    setSaving(true);
    setError(null);
    try {
      await updateAgentDefinition(
        selectedAgent.category,
        selectedAgent.filename,
        editedContent
      );
      setSuccessMessage('Agent definition saved successfully!');
      setIsEditing(false);
      // Refresh content
      const data = await getAgentDefinition(selectedAgent.category, selectedAgent.filename);
      setAgentContent(data);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to save agent definition');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleRestore = async () => {
    if (!selectedAgent) return;
    if (!window.confirm('Restore this agent definition from backup? Current changes will be lost.')) {
      return;
    }
    try {
      await restoreAgentDefinition(selectedAgent.category, selectedAgent.filename);
      setSuccessMessage('Agent definition restored from backup!');
      // Refresh content
      const data = await getAgentDefinition(selectedAgent.category, selectedAgent.filename);
      setAgentContent(data);
      setEditedContent(data.content);
      setIsEditing(false);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to restore - no backup found');
      console.error(err);
    }
  };

  const handleCancel = () => {
    setEditedContent(agentContent?.content || '');
    setIsEditing(false);
  };

  const filteredAgents = useCallback((category) => {
    if (!definitions?.categories?.[category]) return [];
    if (!searchTerm) return definitions.categories[category];
    const term = searchTerm.toLowerCase();
    return definitions.categories[category].filter(agent =>
      agent.name.toLowerCase().includes(term) ||
      agent.purpose.toLowerCase().includes(term)
    );
  }, [definitions, searchTerm]);

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3 text-light">Loading agent definitions...</p>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4" style={{ height: 'calc(100vh - 120px)' }}>
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {successMessage && (
        <Alert variant="success" dismissible onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      <Row className="mb-3">
        <Col>
          <h2 className="text-light">Agent Definitions</h2>
          <p style={{ color: '#9ca3af' }}>
            View and edit agent definition files. Each agent's behavior is defined by a markdown file.
          </p>
        </Col>
        <Col xs="auto">
          <Badge bg="info" className="me-2">
            {definitions?.total_agents || 0} Agents
          </Badge>
          {Object.entries(definitions?.category_counts || {}).map(([cat, count]) => (
            <Badge key={cat} bg={getCategoryColor(cat)} className="me-1">
              {getCategoryIcon(cat)} {count}
            </Badge>
          ))}
        </Col>
      </Row>

      {/* Search Bar */}
      <Row className="mb-3">
        <Col md={4}>
          <Form.Control
            type="search"
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              backgroundColor: '#1a1d29',
              color: '#e4e6eb',
              border: '1px solid #3a3f52'
            }}
          />
        </Col>
        <Col md={8}>
          <ButtonGroup>
            {(definitions?.categories ? Object.keys(definitions.categories) : []).map(cat => (
              <Button
                key={cat}
                variant={activeCategory === cat ? getCategoryColor(cat) : `outline-${getCategoryColor(cat)}`}
                onClick={() => setActiveCategory(cat)}
                size="sm"
              >
                {getCategoryIcon(cat)} {cat.charAt(0).toUpperCase() + cat.slice(1)}
                <Badge bg="dark" className="ms-1">
                  {filteredAgents(cat).length}
                </Badge>
              </Button>
            ))}
          </ButtonGroup>
        </Col>
      </Row>

      <Row style={{ height: 'calc(100% - 180px)' }}>
        {/* Left Pane - Agent List */}
        <Col md={4} style={{ height: '100%', overflowY: 'auto' }}>
          <Card bg="dark" text="light" style={{ height: '100%' }}>
            <Card.Header>
              <div className="d-flex justify-content-between align-items-center">
                <strong>{getCategoryIcon(activeCategory]} {activeCategory.charAt(0).toUpperCase() + activeCategory.slice(1)}</strong>
              </div>
              <small style={{ color: '#9ca3af' }}>
                {getCategoryDescription(activeCategory)}
              </small>
            </Card.Header>
            <ListGroup variant="flush" style={{ overflowY: 'auto' }}>
              {filteredAgents(activeCategory).length === 0 ? (
                <ListGroup.Item variant="dark" className="text-center" style={{ color: '#9ca3af' }}>
                  {searchTerm ? 'No agents match your search' : 'No agents in this category'}
                </ListGroup.Item>
              ) : (
                filteredAgents(activeCategory).map((agent, idx) => (
                  <ListGroup.Item
                    key={agent.filename}
                    variant="dark"
                    action
                    active={selectedAgent?.filename === agent.filename && selectedAgent?.category === activeCategory}
                    onClick={() => handleSelectAgent(activeCategory, agent.filename)}
                    style={{
                      cursor: 'pointer',
                      borderLeft: selectedAgent?.filename === agent.filename && selectedAgent?.category === activeCategory
                        ? `3px solid var(--bs-${getCategoryColor(activeCategory]})`
                        : '3px solid transparent',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div className="d-flex align-items-center gap-2 mb-1">
                      <Badge
                        bg={selectedAgent?.filename === agent.filename ? 'light' : getCategoryColor(activeCategory]}
                        text={selectedAgent?.filename === agent.filename ? 'dark' : 'light'}
                        style={{ fontSize: '10px', padding: '2px 6px' }}
                      >
                        #{idx + 1}
                      </Badge>
                      <div className="fw-bold" style={{ color: '#f7fafc' }}>{agent.name}</div>
                    </div>
                    <div style={{ paddingLeft: '28px' }}>
                      <small style={{ color: '#9ca3af', display: 'block', marginBottom: '4px' }}>
                        {agent.purpose || 'No description'}
                      </small>
                      <small style={{ color: '#6b7280', fontSize: '10px' }}>
                        📄 {agent.filename} • {Math.round(agent.size_bytes / 1024)}KB
                      </small>
                    </div>
                  </ListGroup.Item>
                ))
              )}
            </ListGroup>
          </Card>
        </Col>

        {/* Right Pane - Agent Definition Editor */}
        <Col md={8} style={{ height: '100%', overflowY: 'auto' }}>
          <Card bg="dark" text="light" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {!selectedAgent ? (
              <Card.Body className="d-flex align-items-center justify-content-center">
                <div className="text-center" style={{ color: '#9ca3af' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>
                    {getCategoryIcon(activeCategory]}
                  </div>
                  <h5>Select an Agent</h5>
                  <p>Click on an agent from the list to view and edit its definition.</p>
                  <p className="mt-3">
                    <strong>Agent definitions control:</strong>
                  </p>
                  <ul className="text-start" style={{ maxWidth: '400px', margin: '0 auto' }}>
                    <li>Agent purpose and responsibilities</li>
                    <li>Input/output formats</li>
                    <li>Available tools and permissions</li>
                    <li>Completion protocols</li>
                    <li>Instantiation conditions</li>
                  </ul>
                </div>
              </Card.Body>
            ) : (
              <>
                <Card.Header>
                  <div className="d-flex justify-content-between align-items-center">
                    <div>
                      <Badge bg={getCategoryColor(selectedAgent.category]} className="me-2">
                        {getCategoryIcon(selectedAgent.category]} {selectedAgent.category}
                      </Badge>
                      <strong className="fs-5">
                        {agentContent?.content?.split('\n')[0]?.replace(/^#\s*/, '') || selectedAgent.filename}
                      </strong>
                    </div>
                    <div>
                      {isEditing ? (
                        <>
                          <Button
                            variant="outline-secondary"
                            size="sm"
                            className="me-2"
                            onClick={handleCancel}
                          >
                            Cancel
                          </Button>
                          <Button
                            variant="success"
                            size="sm"
                            onClick={handleSave}
                            disabled={saving}
                          >
                            {saving ? (
                              <>
                                <Spinner animation="border" size="sm" className="me-1" />
                                Saving...
                              </>
                            ) : (
                              'Save Changes'
                            )}
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            variant="outline-warning"
                            size="sm"
                            className="me-2"
                            onClick={handleRestore}
                            title="Restore from backup"
                          >
                            Restore
                          </Button>
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => setIsEditing(true)}
                          >
                            Edit
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                  <small style={{ color: '#9ca3af' }}>
                    {agentContent?.path} • Modified: {new Date(agentContent?.modified_at).toLocaleString()}
                  </small>
                </Card.Header>
                <Card.Body style={{ flex: 1, overflowY: 'auto', padding: isEditing ? '0' : '1rem' }}>
                  {isEditing ? (
                    <Form.Control
                      as="textarea"
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      style={{
                        height: '100%',
                        resize: 'none',
                        fontFamily: 'monospace',
                        fontSize: '13px',
                        backgroundColor: '#0f1117',
                        color: '#e4e6eb',
                        border: 'none',
                        borderRadius: 0
                      }}
                    />
                  ) : (
                    <div style={{ fontFamily: 'monospace', fontSize: '13px' }}>
                      {/* Render sections */}
                      {agentContent?.sections && Object.keys(agentContent.sections).length > 0 ? (
                        <Accordion defaultActiveKey={Object.keys(agentContent.sections).map((_, i) => i.toString())} alwaysOpen>
                          {Object.entries(agentContent.sections).map(([sectionName, content], idx) => {
                            const displayName = sectionName
                              .replace(/_/g, ' ')
                              .replace(/\b\w/g, l => l.toUpperCase());
                            const sectionIcons = {
                              'Purpose': '🎯',
                              'Inputs': '📥',
                              'Outputs': '📤',
                              'Tools': '🔧',
                              'Permissions': '🔐',
                              'Workflow': '📋',
                              'Completion': '✅',
                              'Rules': '📜',
                              'Examples': '💡',
                              'Default': '📄'
                            };
                            const icon = Object.entries(sectionIcons).find(([key]) =>
                              displayName.toLowerCase().includes(key.toLowerCase())
                            )?.[1] || '📄';

                            return (
                              <Accordion.Item
                                key={sectionName}
                                eventKey={idx.toString()}
                                style={{
                                  backgroundColor: '#1a1d29',
                                  border: '1px solid #3a3f52',
                                  marginBottom: '8px',
                                  borderRadius: '6px',
                                  overflow: 'hidden'
                                }}
                              >
                                <Accordion.Header
                                  style={{
                                    backgroundColor: '#242836'
                                  }}
                                >
                                  <span style={{ marginRight: '8px' }}>{icon}</span>
                                  <strong style={{ color: '#e2e8f0' }}>{displayName}</strong>
                                </Accordion.Header>
                                <Accordion.Body
                                  style={{
                                    backgroundColor: '#1a1d29',
                                    padding: '12px',
                                    borderTop: '1px solid #3a3f52'
                                  }}
                                >
                                  <pre style={{
                                    whiteSpace: 'pre-wrap',
                                    wordWrap: 'break-word',
                                    color: '#9ca3af',
                                    margin: 0,
                                    fontSize: '12px',
                                    lineHeight: '1.6'
                                  }}>
                                    {content}
                                  </pre>
                                </Accordion.Body>
                              </Accordion.Item>
                            );
                          })}
                        </Accordion>
                      ) : (
                        <pre style={{
                          whiteSpace: 'pre-wrap',
                          wordWrap: 'break-word',
                          color: '#e2e8f0'
                        }}>
                          {agentContent?.content}
                        </pre>
                      )}
                    </div>
                  )}
                </Card.Body>
              </>
            )}
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default AgentStats;
