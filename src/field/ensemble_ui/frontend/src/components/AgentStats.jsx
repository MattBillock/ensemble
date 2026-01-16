import React, { useState, useEffect } from 'react';
import {
  Container, Row, Col, Card, Table, Spinner, Badge, ListGroup, Alert, Button
} from 'react-bootstrap';
import { getAgentStats, getAgentDetails, getRunningAgents } from '../services/api';

function AgentStats() {
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState([]);
  const [runningAgents, setRunningAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentDetails, setAgentDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
    // Poll for running agents every 10 seconds
    const pollInterval = setInterval(fetchRunningAgents, 10000);
    return () => clearInterval(pollInterval);
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, runningRes] = await Promise.all([
        getAgentStats(),
        getRunningAgents()
      ]);
      setAgents(statsRes.agents || []);
      setRunningAgents(runningRes.agents || []);
    } catch (err) {
      setError('Failed to load agent stats');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRunningAgents = async () => {
    try {
      const runningRes = await getRunningAgents();
      setRunningAgents(runningRes.agents || []);
    } catch (err) {
      console.error('Failed to fetch running agents:', err);
    }
  };

  const handleSelectAgent = async (agentClass) => {
    setSelectedAgent(agentClass);
    setLoadingDetails(true);
    setError(null);
    try {
      const details = await getAgentDetails(agentClass);
      setAgentDetails(details);
    } catch (err) {
      setError('Failed to load agent details');
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  };

  const getRarityColor = (rarity) => {
    const colors = {
      common: '#b0b0b0',
      uncommon: '#00aa00',
      rare: '#0088ff',
      epic: '#aa00ff',
      legendary: '#ffaa00'
    };
    return colors[rarity] || '#888';
  };

  const formatTimestamp = (ts) => {
    if (!ts) return '-';
    const date = new Date(ts);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3 text-light">Loading agent stats...</p>
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
          <Badge bg="success" className="me-2">
            {runningAgents.length} Running
          </Badge>
          <Badge bg="secondary">
            {agents.length} Agent Classes
          </Badge>
        </Col>
      </Row>

      {/* Running Agents Banner */}
      {runningAgents.length > 0 && (
        <Alert variant="info" className="mb-3">
          <strong>Currently Running:</strong>{' '}
          {runningAgents.map((agent, i) => (
            <Badge
              key={agent.agent_id}
              bg="primary"
              className="me-2"
              style={{ cursor: 'pointer' }}
              onClick={() => handleSelectAgent(agent.agent_class)}
            >
              {agent.name || agent.agent_class}
            </Badge>
          ))}
        </Alert>
      )}

      <Row style={{ height: 'calc(100% - 140px)' }}>
        {/* Left Pane - Agent List */}
        <Col md={4} style={{ height: '100%', overflowY: 'auto' }}>
          <Card bg="dark" text="light" style={{ height: '100%' }}>
            <Card.Header>
              <strong>Agent Classes</strong>
            </Card.Header>
            <ListGroup variant="flush" style={{ overflowY: 'auto' }}>
              {agents.map((agent) => {
                const isRunning = runningAgents.some(
                  r => r.agent_class === agent.agent_class || r.name === agent.agent_class
                );
                return (
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
                        <span className="fw-bold">{agent.agent_class}</span>
                        {isRunning && (
                          <Badge bg="success" className="ms-2" pill>
                            Running
                          </Badge>
                        )}
                      </div>
                      <div className="text-end">
                        <Badge bg="secondary" className="me-1">
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
                );
              })}
            </ListGroup>
          </Card>
        </Col>

        {/* Right Pane - Agent Details */}
        <Col md={8} style={{ height: '100%', overflowY: 'auto' }}>
          <Card bg="dark" text="light" style={{ height: '100%' }}>
            {!selectedAgent ? (
              <Card.Body className="d-flex align-items-center justify-content-center">
                <div className="text-center" style={{ color: '#9ca3af' }}>
                  <div style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>
                    Select an agent to view details
                  </div>
                  <p>Click on an agent class from the list to see their achievements and activity.</p>
                </div>
              </Card.Body>
            ) : loadingDetails ? (
              <Card.Body className="text-center">
                <Spinner animation="border" variant="primary" />
                <p className="mt-2" style={{ color: '#9ca3af' }}>Loading agent details...</p>
              </Card.Body>
            ) : agentDetails ? (
              <>
                <Card.Header>
                  <div className="d-flex justify-content-between align-items-center">
                    <div>
                      <strong className="fs-5">{selectedAgent}</strong>
                      {agentDetails.is_active && (
                        <Badge bg="success" className="ms-2">Active</Badge>
                      )}
                    </div>
                    <Badge bg="warning" text="dark">
                      {agentDetails.achievement_count} Achievements
                    </Badge>
                  </div>
                </Card.Header>
                <Card.Body style={{ overflowY: 'auto' }}>
                  {/* Running Instances */}
                  {agentDetails.running_agents?.length > 0 && (
                    <div className="mb-4">
                      <h6 className="text-warning">Currently Running</h6>
                      <Table size="sm" variant="dark" bordered>
                        <thead>
                          <tr>
                            <th>Agent ID</th>
                            <th>Status</th>
                            <th>Task</th>
                          </tr>
                        </thead>
                        <tbody>
                          {agentDetails.running_agents.map((agent) => (
                            <tr key={agent.agent_id}>
                              <td><code>{agent.agent_id?.slice(0, 12) || 'unknown'}...</code></td>
                              <td>
                                <Badge bg={agent.status === 'running' ? 'success' : 'secondary'}>
                                  {agent.status}
                                </Badge>
                              </td>
                              <td className="text-truncate" style={{ maxWidth: '300px' }}>
                                {agent.task || '-'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </div>
                  )}

                  {/* Achievements */}
                  <div className="mb-4">
                    <h6 className="text-info">Achievements ({agentDetails.achievements?.length || 0})</h6>
                    {agentDetails.achievements?.length > 0 ? (
                      <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
                        <Table size="sm" variant="dark" bordered hover>
                          <thead>
                            <tr>
                              <th style={{ width: '50px' }}></th>
                              <th>Achievement</th>
                              <th>Rarity</th>
                              <th>Earned</th>
                            </tr>
                          </thead>
                          <tbody>
                            {agentDetails.achievements.slice(0, 20).map((achievement, i) => (
                              <tr key={i}>
                                <td className="text-center" style={{ fontSize: '1.2rem' }}>
                                  {achievement.icon}
                                </td>
                                <td>
                                  <strong>{achievement.name}</strong>
                                  <br />
                                  <small style={{ color: '#9ca3af' }}>{achievement.description}</small>
                                </td>
                                <td>
                                  <Badge
                                    style={{
                                      backgroundColor: getRarityColor(achievement.rarity),
                                      color: achievement.rarity === 'legendary' ? '#000' : '#fff'
                                    }}
                                  >
                                    {achievement.rarity}
                                  </Badge>
                                </td>
                                <td>
                                  <small>{formatTimestamp(achievement.awarded_at)}</small>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                        {agentDetails.achievements.length > 20 && (
                          <p className="text-center" style={{ color: '#9ca3af' }}>
                            ... and {agentDetails.achievements.length - 20} more
                          </p>
                        )}
                      </div>
                    ) : (
                      <p style={{ color: '#9ca3af' }}>No achievements yet.</p>
                    )}
                  </div>

                  {/* Recent Activity */}
                  <div>
                    <h6 className="text-success">Recent Activity</h6>
                    {agentDetails.recent_activities?.length > 0 ? (
                      <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                        <Table size="sm" variant="dark" bordered>
                          <thead>
                            <tr>
                              <th>Type</th>
                              <th>Time</th>
                              <th>Details</th>
                            </tr>
                          </thead>
                          <tbody>
                            {agentDetails.recent_activities.map((activity, i) => (
                              <tr key={i}>
                                <td>
                                  <Badge bg="info">{activity.type}</Badge>
                                </td>
                                <td>
                                  <small>{formatTimestamp(activity.timestamp)}</small>
                                </td>
                                <td className="text-truncate" style={{ maxWidth: '300px' }}>
                                  {activity.data?.description || activity.data?.file_path || '-'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                      </div>
                    ) : (
                      <p style={{ color: '#9ca3af' }}>No recent activity recorded.</p>
                    )}
                  </div>
                </Card.Body>
              </>
            ) : (
              <Card.Body className="text-center" style={{ color: '#9ca3af' }}>
                No details available
              </Card.Body>
            )}
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default AgentStats;
