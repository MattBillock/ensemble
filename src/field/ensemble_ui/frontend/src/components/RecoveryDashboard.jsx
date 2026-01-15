import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Spinner, Button, Badge, Alert, Form, Modal } from 'react-bootstrap';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

function RecoveryDashboard() {
  const [loading, setLoading] = useState(true);
  const [stalledAgents, setStalledAgents] = useState([]);
  const [recoveryQueue, setRecoveryQueue] = useState(null);
  const [recoveryHistory, setRecoveryHistory] = useState([]);
  const [scanResult, setScanResult] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [showRecoveryModal, setShowRecoveryModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedStrategy, setSelectedStrategy] = useState('retry');
  const [actionInProgress, setActionInProgress] = useState(null);

  useEffect(() => {
    fetchRecoveryData();
    const interval = setInterval(fetchRecoveryData, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchRecoveryData = async () => {
    try {
      const [stalledRes, queueRes, historyRes] = await Promise.all([
        fetch(`${API_BASE}/api/recovery/stalled`),
        fetch(`${API_BASE}/api/recovery/queue`),
        fetch(`${API_BASE}/api/recovery/history?limit=50`)
      ]);

      // Check all responses
      if (!stalledRes.ok || !queueRes.ok || !historyRes.ok) {
        throw new Error('One or more API calls failed');
      }

      const stalledData = await stalledRes.json();
      const queueData = await queueRes.json();
      const historyData = await historyRes.json();

      setStalledAgents(stalledData.stalled_agents || []);
      setRecoveryQueue(queueData);
      setRecoveryHistory(historyData.history || []);
    } catch (error) {
      console.error('Failed to fetch recovery data:', error);
      // Set safe defaults on error
      setStalledAgents([]);
      setRecoveryQueue({ pending_tasks: [] });
      setRecoveryHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const response = await fetch(`${API_BASE}/api/recovery/scan`, { method: 'POST' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      setScanResult(result);
      await fetchRecoveryData(); // Refresh data
    } catch (error) {
      console.error('Scan failed:', error);
      setScanResult({ error: 'Scan failed' });
    } finally {
      setScanning(false);
    }
  };

  const handleTriggerRecovery = async () => {
    if (!selectedAgent) return;

    setActionInProgress(selectedAgent);
    try {
      const response = await fetch(
        `${API_BASE}/api/recovery/trigger/${selectedAgent}?strategy=${selectedStrategy}`,
        { method: 'POST' }
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      if (result.success) {
        await fetchRecoveryData();
      }
    } catch (error) {
      console.error('Recovery trigger failed:', error);
    } finally {
      setActionInProgress(null);
      setShowRecoveryModal(false);
      setSelectedAgent(null);
    }
  };

  const openRecoveryModal = (agentId) => {
    setSelectedAgent(agentId);
    setSelectedStrategy('retry');
    setShowRecoveryModal(true);
  };

  const getStrategyBadge = (strategy) => {
    const colors = {
      'retry': 'primary',
      'retry_backoff': 'info',
      'enhance_prompt': 'warning',
      'refactor_agent': 'secondary',
      'escalate_model': 'danger',
      'manual': 'dark',
      'abort': 'danger'
    };
    return <Badge bg={colors[strategy] || 'secondary'}>{strategy}</Badge>;
  };

  const getStatusBadge = (status) => {
    const colors = {
      'pending': 'warning',
      'in_progress': 'primary',
      'completed': 'success',
      'failed': 'danger',
      'needs_review': 'info',
      'aborted': 'dark',
      'forever_failed': 'danger',
      'permanently_failed': 'danger'
    };
    // Show custom text for forever_failed
    const displayText = status === 'forever_failed' || status === 'permanently_failed'
      ? '☠️ ' + status.replace('_', ' ').toUpperCase()
      : status;
    return <Badge bg={colors[status] || 'secondary'}>{displayText}</Badge>;
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  const formatDuration = (ms) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms/1000).toFixed(1)}s`;
    return `${(ms/60000).toFixed(1)}m`;
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" variant="warning" />
        <p className="mt-3" style={{ color: '#e4e6eb' }}>Loading recovery data...</p>
      </Container>
    );
  }

  const activeRecoveries = recoveryQueue?.active_recoveries || [];
  const pendingTasks = recoveryQueue?.pending_tasks || [];

  return (
    <Container fluid className="mt-4" style={{ color: '#e4e6eb' }}>
      <Row className="mb-4">
        <Col>
          <h2>Recovery Dashboard</h2>
        </Col>
        <Col xs="auto">
          <Button
            variant="warning"
            onClick={handleScan}
            disabled={scanning}
          >
            {scanning ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Scanning...
              </>
            ) : (
              'Scan for Stalled Agents'
            )}
          </Button>
        </Col>
      </Row>

      {scanResult && (
        <Row className="mb-4">
          <Col>
            <Alert variant={scanResult.error ? 'danger' : 'info'} dismissible onClose={() => setScanResult(null)}>
              {scanResult.error ? (
                scanResult.error
              ) : (
                <>
                  <strong>Scan Complete:</strong> Found {scanResult.stalled_count} stalled agent(s),
                  queued {scanResult.queued_for_recovery} for recovery.
                </>
              )}
            </Alert>
          </Col>
        </Row>
      )}

      {/* Status Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card style={{ background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', color: 'white' }}>
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Stalled Agents
              </h6>
              <h3 className="mb-0">{stalledAgents.length}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', color: 'white' }}>
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                In Recovery Queue
              </h6>
              <h3 className="mb-0">{pendingTasks.length}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)', color: 'white' }}>
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Active Recoveries
              </h6>
              <h3 className="mb-0">{activeRecoveries.length}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card style={{ background: recoveryQueue?.is_running ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)', color: 'white' }}>
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                System Status
              </h6>
              <h3 className="mb-0">{recoveryQueue?.is_running ? 'Active' : 'Stopped'}</h3>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Active Recoveries */}
      {activeRecoveries.length > 0 && (
        <Row className="mb-4">
          <Col>
            <Card bg="dark" text="light">
              <Card.Header>
                <strong>Active Recoveries</strong>
                <Badge bg="primary" className="ms-2">{activeRecoveries.length}</Badge>
              </Card.Header>
              <Card.Body>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  {activeRecoveries.map((agentId, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: '#2563eb',
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                    >
                      <Spinner animation="border" size="sm" />
                      <code>{agentId}</code>
                    </div>
                  ))}
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Stalled Agents */}
      <Row className="mb-4">
        <Col md={6}>
          <Card bg="dark" text="light">
            <Card.Header>
              <strong>Stalled Agents</strong>
              <Badge bg="danger" className="ms-2">{stalledAgents.length}</Badge>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {stalledAgents.length === 0 ? (
                <div className="text-center py-4" style={{ color: '#9ca3af' }}>
                  No stalled agents detected
                </div>
              ) : (
                <Table hover size="sm" variant="dark">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Reason</th>
                      <th>Duration</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stalledAgents.map((agent, idx) => (
                      <tr key={idx}>
                        <td>
                          <code style={{ fontSize: '0.85rem' }}>{agent.agent_name || agent.agent_id}</code>
                          <br />
                          <small style={{ color: '#9ca3af' }}>{agent.agent_type}</small>
                        </td>
                        <td>
                          <Badge bg="warning" text="dark">{agent.stall_reason || 'unknown'}</Badge>
                        </td>
                        <td>
                          {agent.stall_duration_ms ? formatDuration(agent.stall_duration_ms) : 'N/A'}
                        </td>
                        <td>
                          <Button
                            size="sm"
                            variant="outline-warning"
                            onClick={() => openRecoveryModal(agent.agent_id)}
                            disabled={actionInProgress === agent.agent_id}
                          >
                            {actionInProgress === agent.agent_id ? (
                              <Spinner animation="border" size="sm" />
                            ) : (
                              'Recover'
                            )}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Recovery Queue */}
        <Col md={6}>
          <Card bg="dark" text="light">
            <Card.Header>
              <strong>Recovery Queue</strong>
              <Badge bg="warning" className="ms-2">{pendingTasks.length}</Badge>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {pendingTasks.length === 0 ? (
                <div className="text-center py-4" style={{ color: '#9ca3af' }}>
                  Recovery queue is empty
                </div>
              ) : (
                <Table hover size="sm" variant="dark">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Strategy</th>
                      <th>Reason</th>
                      <th>Attempts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingTasks.map((task, idx) => (
                      <tr key={idx}>
                        <td>
                          <code style={{ fontSize: '0.85rem' }}>{task.agent_name || task.agent_id}</code>
                        </td>
                        <td>{getStrategyBadge(task.strategy)}</td>
                        <td style={{ fontSize: '0.85rem' }}>{task.reason}</td>
                        <td>
                          <Badge bg="secondary">{task.attempts || 0}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Recovery History */}
      <Row className="mb-4">
        <Col>
          <Card bg="dark" text="light">
            <Card.Header>
              <strong>Recovery History</strong>
              <Badge bg="info" className="ms-2">{recoveryHistory.length}</Badge>
            </Card.Header>
            <Card.Body style={{ maxHeight: '500px', overflowY: 'auto' }}>
              {recoveryHistory.length === 0 ? (
                <div className="text-center py-4" style={{ color: '#9ca3af' }}>
                  No recovery history available
                </div>
              ) : (
                <Table hover size="sm" variant="dark">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Type</th>
                      <th>Strategy</th>
                      <th>Status</th>
                      <th>Reason</th>
                      <th>Attempts</th>
                      <th>Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recoveryHistory.map((record, idx) => (
                      <tr key={idx}>
                        <td>
                          <code style={{ fontSize: '0.85rem' }}>{record.agent_name || record.agent_id}</code>
                        </td>
                        <td style={{ fontSize: '0.85rem' }}>{record.agent_type}</td>
                        <td>{getStrategyBadge(record.recovery_strategy)}</td>
                        <td>{getStatusBadge(record.status)}</td>
                        <td style={{ fontSize: '0.85rem', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {record.recovery_reason}
                        </td>
                        <td>
                          <Badge bg="secondary">{record.attempts || 0}/{record.max_attempts || 5}</Badge>
                        </td>
                        <td style={{ fontSize: '0.8rem' }}>
                          {formatTimestamp(record.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Recovery Strategies Reference */}
      <Row className="mb-4">
        <Col>
          <Card bg="dark" text="light">
            <Card.Header>
              <strong>Recovery Strategies Reference</strong>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={6}>
                  <ul className="mb-0" style={{ fontSize: '0.9rem' }}>
                    <li><strong>retry:</strong> Simple retry with same parameters</li>
                    <li><strong>retry_backoff:</strong> Retry with exponential backoff delay</li>
                    <li><strong>enhance_prompt:</strong> Improve prompt clarity before retrying</li>
                  </ul>
                </Col>
                <Col md={6}>
                  <ul className="mb-0" style={{ fontSize: '0.9rem' }}>
                    <li><strong>refactor_agent:</strong> Update agent definition with guardrails</li>
                    <li><strong>escalate_model:</strong> Retry with more powerful model (Haiku-&gt;Sonnet-&gt;Opus)</li>
                    <li><strong>manual:</strong> Flag for human review and intervention</li>
                  </ul>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Recovery Modal */}
      <Modal show={showRecoveryModal} onHide={() => setShowRecoveryModal(false)} centered>
        <Modal.Header closeButton style={{ backgroundColor: '#242836', color: '#e4e6eb', borderColor: '#3a3f52' }}>
          <Modal.Title>Trigger Recovery</Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ backgroundColor: '#1a1d29', color: '#e4e6eb' }}>
          <p>Agent: <code>{selectedAgent}</code></p>
          <Form.Group>
            <Form.Label>Recovery Strategy</Form.Label>
            <Form.Select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              style={{
                backgroundColor: '#242836',
                color: '#e4e6eb',
                borderColor: '#3a3f52'
              }}
            >
              <option value="retry">Retry (simple retry)</option>
              <option value="retry_backoff">Retry with Backoff</option>
              <option value="enhance_prompt">Enhance Prompt</option>
              <option value="refactor_agent">Refactor Agent</option>
              <option value="escalate_model">Escalate Model</option>
              <option value="manual">Manual Intervention</option>
            </Form.Select>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer style={{ backgroundColor: '#242836', borderColor: '#3a3f52' }}>
          <Button variant="secondary" onClick={() => setShowRecoveryModal(false)}>
            Cancel
          </Button>
          <Button variant="warning" onClick={handleTriggerRecovery}>
            Start Recovery
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default RecoveryDashboard;
