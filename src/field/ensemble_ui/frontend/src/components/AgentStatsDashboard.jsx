import React, { useState, useEffect, useCallback } from 'react';
import {
  Container, Row, Col, Card, Spinner, Badge, ListGroup, Alert, Button
} from 'react-bootstrap';
import { getAgentStats, getAgentDetails } from '../services/api';

function AgentStatsDashboard() {
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentDetails, setAgentDetails] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAgentStats();
    // Poll for updates
    const interval = setInterval(fetchAgentStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchAgentStats = async () => {
    try {
      const data = await getAgentStats();
      // Sort by total runs descending
      const sortedAgents = (data.agents || []).sort((a, b) => b.total_runs - a.total_runs);
      setAgents(sortedAgents);
      setLoading(false);
    } catch (err) {
      setError('Failed to load agent stats');
      console.error(err);
      setLoading(false);
    }
  };

  const handleSelectAgent = async (agentClass) => {
    setSelectedAgent(agentClass);
    setDetailsLoading(true);
    setAgentDetails(null);
    try {
      const details = await getAgentDetails(agentClass);
      setAgentDetails(details);
    } catch (err) {
      console.error('Failed to load agent details:', err);
      setAgentDetails({ error: 'Failed to load details' });
    } finally {
      setDetailsLoading(false);
    }
  };

  // Get running agents count
  const runningCount = agents.filter(a => a.status === 'running' || a.is_active).length;
  const totalAgentClasses = agents.length;

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3 text-light">Loading agent statistics...</p>
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

      <Row className="mb-3">
        <Col>
          <h2 className="text-light">Agent Stats</h2>
          <p style={{ color: '#9ca3af' }}>
            View agent activity, achievements, and performance metrics.
          </p>
        </Col>
        <Col xs="auto">
          <Badge bg="warning" className="me-2">
            {runningCount} Running
          </Badge>
          <Badge bg="info">
            {totalAgentClasses} Agent Classes
          </Badge>
        </Col>
      </Row>

      <Row style={{ height: 'calc(100% - 100px)' }}>
        {/* Left Panel - Agent List */}
        <Col md={5} style={{ height: '100%', overflowY: 'auto' }}>
          <Card bg="dark" text="light" style={{ height: '100%' }}>
            <Card.Header>
              <strong>Agent Classes</strong>
            </Card.Header>
            <ListGroup variant="flush" style={{ overflowY: 'auto' }}>
              {agents.length === 0 ? (
                <ListGroup.Item variant="dark" className="text-center" style={{ color: '#9ca3af' }}>
                  No agent activity recorded yet
                </ListGroup.Item>
              ) : (
                agents.map((agent) => (
                  <ListGroup.Item
                    key={agent.agent_class}
                    variant="dark"
                    action
                    active={selectedAgent === agent.agent_class}
                    onClick={() => handleSelectAgent(agent.agent_class)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <code style={{ fontSize: '0.9rem', color: selectedAgent === agent.agent_class ? '#fff' : '#f472b6' }}>
                          {agent.agent_class}
                        </code>
                      </div>
                      <div className="d-flex gap-2 align-items-center">
                        <Badge bg="secondary" style={{ minWidth: '60px' }}>
                          {agent.total_runs} runs
                        </Badge>
                        {agent.achievement_count > 0 && (
                          <Badge bg="warning" text="dark">
                            {agent.achievement_count} achievements
                          </Badge>
                        )}
                      </div>
                    </div>
                  </ListGroup.Item>
                ))
              )}
            </ListGroup>
          </Card>
        </Col>

        {/* Right Panel - Agent Details */}
        <Col md={7} style={{ height: '100%', overflowY: 'auto' }}>
          <Card bg="dark" text="light" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {!selectedAgent ? (
              <Card.Body className="d-flex align-items-center justify-content-center">
                <div className="text-center" style={{ color: '#9ca3af' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>
                    📊
                  </div>
                  <h5>Select an Agent Class</h5>
                  <p>Click on an agent from the list to view achievements and activity.</p>
                </div>
              </Card.Body>
            ) : (
              <>
                <Card.Header className="d-flex justify-content-between align-items-center">
                  <strong className="fs-5">{selectedAgent}</strong>
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    onClick={() => handleSelectAgent(selectedAgent)}
                    title="Refresh"
                  >
                    🔄
                  </Button>
                </Card.Header>
                <Card.Body style={{ flex: 1, overflowY: 'auto' }}>
                  {detailsLoading ? (
                    <div className="text-center py-4">
                      <Spinner animation="border" variant="primary" size="sm" />
                      <p className="mt-2" style={{ color: '#9ca3af' }}>Loading details...</p>
                    </div>
                  ) : agentDetails?.error ? (
                    <Alert variant="warning">{agentDetails.error}</Alert>
                  ) : agentDetails ? (
                    <>
                      {/* Achievements Section */}
                      <h6 style={{ color: '#fbbf24' }}>
                        Achievements ({agentDetails.achievement_count || 0})
                      </h6>
                      {agentDetails.achievements && agentDetails.achievements.length > 0 ? (
                        <div className="mb-4" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                          {agentDetails.achievements.map((achievement, idx) => (
                            <div
                              key={idx}
                              style={{
                                padding: '8px 12px',
                                marginBottom: '8px',
                                backgroundColor: '#1a1d29',
                                borderRadius: '4px',
                                border: '1px solid #3a3f52'
                              }}
                            >
                              <div className="d-flex justify-content-between align-items-start">
                                <div>
                                  <span style={{ marginRight: '8px' }}>🏆</span>
                                  <strong>{achievement.title || achievement.name || 'Achievement'}</strong>
                                </div>
                                {achievement.rarity && (
                                  <Badge bg={
                                    achievement.rarity === 'legendary' ? 'warning' :
                                    achievement.rarity === 'rare' ? 'info' :
                                    achievement.rarity === 'uncommon' ? 'success' : 'secondary'
                                  }>
                                    {achievement.rarity}
                                  </Badge>
                                )}
                              </div>
                              {achievement.description && (
                                <small style={{ color: '#9ca3af' }}>{achievement.description}</small>
                              )}
                              {achievement.earned_at && (
                                <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '4px' }}>
                                  Earned: {new Date(achievement.earned_at).toLocaleDateString()}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p style={{ color: '#9ca3af' }}>No achievements yet.</p>
                      )}

                      {/* Recent Activity Section */}
                      <h6 style={{ color: '#10b981', marginTop: '24px' }}>Recent Activity</h6>
                      {agentDetails.recent_activities && agentDetails.recent_activities.length > 0 ? (
                        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                          {agentDetails.recent_activities.map((activity, idx) => (
                            <div
                              key={idx}
                              style={{
                                padding: '8px 12px',
                                marginBottom: '6px',
                                backgroundColor: '#1a1d29',
                                borderRadius: '4px',
                                fontSize: '0.85rem'
                              }}
                            >
                              <div className="d-flex justify-content-between">
                                <span>
                                  <Badge bg="secondary" className="me-2">
                                    {activity.type}
                                  </Badge>
                                  {activity.data?.task || activity.data?.tool_name || ''}
                                </span>
                                {activity.timestamp && (
                                  <small style={{ color: '#6b7280' }}>
                                    {new Date(activity.timestamp).toLocaleTimeString()}
                                  </small>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p style={{ color: '#9ca3af' }}>No recent activity recorded.</p>
                      )}

                      {/* Running Agents Section */}
                      {agentDetails.running_agents && agentDetails.running_agents.length > 0 && (
                        <>
                          <h6 style={{ color: '#f59e0b', marginTop: '24px' }}>
                            Currently Running ({agentDetails.running_agents.length})
                          </h6>
                          {agentDetails.running_agents.map((agent, idx) => (
                            <div
                              key={idx}
                              style={{
                                padding: '8px 12px',
                                marginBottom: '6px',
                                backgroundColor: '#1a1d29',
                                borderRadius: '4px',
                                border: '1px solid #f59e0b33'
                              }}
                            >
                              <div className="d-flex justify-content-between align-items-center">
                                <code style={{ fontSize: '0.8rem' }}>
                                  {agent.agent_id.substring(0, 12)}...
                                </code>
                                <Badge bg="warning" text="dark">Running</Badge>
                              </div>
                              {agent.task && (
                                <small style={{ color: '#9ca3af' }}>{agent.task}</small>
                              )}
                            </div>
                          ))}
                        </>
                      )}
                    </>
                  ) : null}
                </Card.Body>
              </>
            )}
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default AgentStatsDashboard;
