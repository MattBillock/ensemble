import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Spinner, Button, Badge, Alert, Modal, Form } from 'react-bootstrap';
import {
  getSelfImprovementStatus,
  runSelfImprovementAnalysis,
  getRecommendations,
  approveRecommendation,
  rejectRecommendation,
  getAutoApplyConfig,
  setAutoApplyConfig,
  applyAllRecommendations,
  applySingleRecommendation
} from '../services/api';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

function SelfImprovementDashboard() {
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [status, setStatus] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedRec, setSelectedRec] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [autoApplyEnabled, setAutoApplyEnabled] = useState(false);
  const [autoApplyConfig, setAutoApplyConfigState] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, recsRes, autoApplyRes] = await Promise.all([
        getSelfImprovementStatus(),
        getRecommendations(),
        getAutoApplyConfig()
      ]);
      setStatus(statusRes);
      setRecommendations(recsRes.recommendations || []);
      setAutoApplyConfigState(autoApplyRes);
      setAutoApplyEnabled(autoApplyRes?.enabled || false);
    } catch (err) {
      console.error('Failed to fetch self-improvement data:', err);
      setError('Failed to load self-improvement data. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const result = await runSelfImprovementAnalysis(30);
      setAnalysis(result);
      // Refresh recommendations after analysis
      const recsRes = await getRecommendations();
      setRecommendations(recsRes.recommendations || []);
      // Refresh status
      const statusRes = await getSelfImprovementStatus();
      setStatus(statusRes);
    } catch (err) {
      console.error('Failed to run analysis:', err);
      setError('Failed to run analysis. Check console for details.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApprove = async (recId) => {
    try {
      await approveRecommendation(recId);
      // Refresh data
      await fetchData();
    } catch (err) {
      console.error('Failed to approve recommendation:', err);
      setError('Failed to approve recommendation');
    }
  };

  const handleReject = async () => {
    if (!selectedRec) return;
    try {
      await rejectRecommendation(selectedRec.id, rejectReason);
      setShowRejectModal(false);
      setSelectedRec(null);
      setRejectReason('');
      // Refresh data
      await fetchData();
    } catch (err) {
      console.error('Failed to reject recommendation:', err);
      setError('Failed to reject recommendation');
    }
  };

  const openRejectModal = (rec) => {
    setSelectedRec(rec);
    setShowRejectModal(true);
  };

  const handleToggleAutoApply = async () => {
    try {
      const newEnabled = !autoApplyEnabled;
      await setAutoApplyConfig(newEnabled, true, 'medium');
      setAutoApplyEnabled(newEnabled);
      // Refresh config
      const configRes = await getAutoApplyConfig();
      setAutoApplyConfigState(configRes);
    } catch (err) {
      console.error('Failed to toggle auto-apply:', err);
      setError('Failed to toggle auto-apply mode');
    }
  };

  const handleApplyAll = async () => {
    setApplying(true);
    setError(null);
    try {
      const result = await applyAllRecommendations();
      setAnalysis(prev => ({
        ...prev,
        auto_apply_results: result.results
      }));
      // Refresh data
      await fetchData();
    } catch (err) {
      console.error('Failed to apply all recommendations:', err);
      setError('Failed to apply recommendations');
    } finally {
      setApplying(false);
    }
  };

  const handleApplySingle = async (recId) => {
    try {
      await applySingleRecommendation(recId);
      await fetchData();
    } catch (err) {
      console.error('Failed to apply recommendation:', err);
      setError('Failed to apply recommendation');
    }
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      critical: 'danger',
      high: 'warning',
      medium: 'info',
      low: 'secondary'
    };
    return <Badge bg={colors[priority] || 'secondary'}>{priority}</Badge>;
  };

  const getTypeBadge = (type) => {
    const labels = {
      model_upgrade: 'Model Upgrade',
      model_downgrade: 'Cost Optimization',
      definition_tweak: 'Definition Tweak',
      definition_major: 'Major Rewrite',
      iteration_increase: 'More Iterations',
      iteration_decrease: 'Fewer Iterations',
      complexity_change: 'Complexity Change',
      alert: 'Alert'
    };
    return <Badge bg="dark">{labels[type] || type}</Badge>;
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading self-improvement data...</p>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4">
      <Row className="mb-4">
        <Col>
          <h2>Self-Improvement Loop</h2>
          <p className="text-muted">
            The self-improvement loop analyzes agent performance and generates recommendations for improvement.
            Feedback is automatically injected into agent prompts to help them learn from past performance.
          </p>
        </Col>
        <Col xs="auto" className="d-flex align-items-center gap-3">
          {/* Auto-Apply Toggle */}
          <div className="d-flex align-items-center">
            <Form.Check
              type="switch"
              id="auto-apply-switch"
              label=""
              checked={autoApplyEnabled}
              onChange={handleToggleAutoApply}
              className="me-2"
              style={{ transform: 'scale(1.3)' }}
            />
            <span
              className={`fw-bold ${autoApplyEnabled ? 'text-danger' : 'text-muted'}`}
              style={{ cursor: 'pointer' }}
              onClick={handleToggleAutoApply}
            >
              {autoApplyEnabled ? 'BUMPERS OFF' : 'Bumpers On'}
            </span>
          </div>

          {/* Apply All Button */}
          {recommendations.length > 0 && (
            <Button
              variant={autoApplyEnabled ? "danger" : "warning"}
              onClick={handleApplyAll}
              disabled={applying}
            >
              {applying ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Applying...
                </>
              ) : (
                `Apply All (${recommendations.length})`
              )}
            </Button>
          )}

          <Button
            variant="primary"
            onClick={handleRunAnalysis}
            disabled={analyzing}
          >
            {analyzing ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Analyzing...
              </>
            ) : (
              'Run Analysis'
            )}
          </Button>
        </Col>
      </Row>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {autoApplyEnabled && (
        <Alert variant="danger" className="d-flex align-items-center">
          <strong className="me-2">BUMPERS OFF MODE ACTIVE</strong>
          <span>
            Recommendations will be automatically applied when you run analysis.
            Agent definitions will be modified without approval.
          </span>
        </Alert>
      )}

      {/* Status Cards */}
      <Row className="mb-4">
        <Col md={2}>
          <Card bg={autoApplyEnabled ? 'danger' : 'secondary'} text="white">
            <Card.Body className="py-2">
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.7rem', opacity: 0.8 }}>
                Auto-Apply
              </h6>
              <h4 className="mb-0">{autoApplyEnabled ? 'BUMPERS OFF' : 'Manual'}</h4>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card bg={status?.status === 'active' ? 'success' : 'secondary'} text="white">
            <Card.Body className="py-2">
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.7rem', opacity: 0.8 }}>
                Loop Status
              </h6>
              <h4 className="mb-0">{status?.status || 'Unknown'}</h4>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card bg="info" text="white">
            <Card.Body className="py-2">
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.7rem', opacity: 0.8 }}>
                Feedback
              </h6>
              <h4 className="mb-0">{status?.feedback_injection || 'N/A'}</h4>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card bg="warning" text="dark">
            <Card.Body className="py-2">
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.7rem', opacity: 0.8 }}>
                Pending
              </h6>
              <h4 className="mb-0">{status?.pending_recommendations || 0}</h4>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card bg="primary" text="white">
            <Card.Body className="py-2">
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.7rem', opacity: 0.8 }}>
                Approved
              </h6>
              <h4 className="mb-0">{status?.approved_recommendations || 0}</h4>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card bg="dark" text="white">
            <Card.Body className="py-2">
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.7rem', opacity: 0.8 }}>
                Applied
              </h6>
              <h4 className="mb-0">{analysis?.auto_apply_results?.applied || 0}</h4>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Analysis Results */}
      {analysis && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <strong>Latest Analysis Results</strong>
                <small className="text-muted ms-2">
                  {new Date(analysis.analysis_timestamp).toLocaleString()}
                </small>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={4}>
                    <h6>Summary</h6>
                    <ul className="list-unstyled">
                      <li>Period: Last {analysis.period_days} days</li>
                      <li>Recommendations: {analysis.recommendations_count}</li>
                      <li>
                        Critical Issues:{' '}
                        <Badge bg={analysis.critical_issues > 0 ? 'danger' : 'success'}>
                          {analysis.critical_issues}
                        </Badge>
                      </li>
                    </ul>
                  </Col>
                  <Col md={4}>
                    <h6>Common Issues Found</h6>
                    {Object.entries(analysis.patterns_found?.common_issues || {}).length > 0 ? (
                      <ul className="list-unstyled">
                        {Object.entries(analysis.patterns_found.common_issues)
                          .sort((a, b) => b[1] - a[1])
                          .slice(0, 5)
                          .map(([issue, count]) => (
                            <li key={issue}>
                              <code>{issue}</code>: {count} occurrences
                            </li>
                          ))}
                      </ul>
                    ) : (
                      <p className="text-muted">No patterns detected</p>
                    )}
                  </Col>
                  <Col md={4}>
                    <h6>Model Recommendations</h6>
                    {analysis.model_recommendations?.length > 0 ? (
                      <ul className="list-unstyled">
                        {analysis.model_recommendations.map((rec, idx) => (
                          <li key={idx}>
                            <strong>{rec.agent}</strong>: Use {rec.recommend_model}
                            <br />
                            <small className="text-success">{rec.improvement}</small>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-muted">No model optimizations suggested</p>
                    )}
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Pending Recommendations */}
      <Row>
        <Col>
          <Card>
            <Card.Header>
              <strong>Pending Recommendations</strong>
              <Badge bg="warning" text="dark" className="ms-2">
                {recommendations.length} pending
              </Badge>
            </Card.Header>
            <Card.Body style={{ maxHeight: '500px', overflowY: 'auto' }}>
              {recommendations.length === 0 ? (
                <div className="text-center py-4 text-muted">
                  <p>No pending recommendations.</p>
                  <p>Click "Run Analysis" to analyze agent performance and generate recommendations.</p>
                </div>
              ) : (
                <Table hover size="sm">
                  <thead>
                    <tr>
                      <th>Priority</th>
                      <th>Agent</th>
                      <th>Type</th>
                      <th>Title</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recommendations.map((rec) => (
                      <tr key={rec.id}>
                        <td>{getPriorityBadge(rec.priority)}</td>
                        <td><code>{rec.agent_name}</code></td>
                        <td>{getTypeBadge(rec.type)}</td>
                        <td>
                          <strong>{rec.title}</strong>
                          <br />
                          <small className="text-muted">{rec.description}</small>
                        </td>
                        <td>
                          <Button
                            variant="warning"
                            size="sm"
                            className="me-1"
                            onClick={() => handleApplySingle(rec.id)}
                            title="Approve AND apply changes to agent definition"
                          >
                            Apply
                          </Button>
                          <Button
                            variant="outline-success"
                            size="sm"
                            className="me-1"
                            onClick={() => handleApprove(rec.id)}
                            title="Approve without applying"
                          >
                            Approve
                          </Button>
                          <Button
                            variant="outline-danger"
                            size="sm"
                            onClick={() => openRejectModal(rec)}
                          >
                            Reject
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
      </Row>

      {/* How It Works */}
      <Row className="mt-4 mb-4">
        <Col>
          <Card bg={autoApplyEnabled ? 'danger' : 'light'} text={autoApplyEnabled ? 'white' : 'dark'}>
            <Card.Body>
              <h6>How the Self-Improvement Loop Works {autoApplyEnabled && '(BUMPERS OFF)'}</h6>
              <ol className="mb-0" style={{ fontSize: '0.875rem' }}>
                <li><strong>Collection:</strong> Every agent execution records metrics (success rate, duration, errors, self-analysis)</li>
                <li><strong>Analysis:</strong> The system periodically analyzes metrics to identify underperforming agents</li>
                <li><strong>Recommendations:</strong> Specific improvement suggestions are generated (model changes, definition tweaks)</li>
                {autoApplyEnabled ? (
                  <li><strong>Auto-Apply:</strong> <Badge bg="warning" text="dark">AUTOMATIC</Badge> Changes are immediately applied to agent definitions without human review</li>
                ) : (
                  <li><strong>Human Review:</strong> You approve or reject recommendations before they're applied</li>
                )}
                <li><strong>Feedback Injection:</strong> Insights are automatically included in agent prompts</li>
                <li><strong>Continuous Learning:</strong> The loop repeats, tracking whether changes improve performance</li>
              </ol>
              {autoApplyEnabled && (
                <div className="mt-3 p-2 bg-dark rounded">
                  <strong>Warning:</strong> In Bumpers Off mode, agent definitions (.md files) will be automatically modified.
                  Backups are created before changes. Toggle off to restore human-in-the-loop approval.
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Reject Modal */}
      <Modal show={showRejectModal} onHide={() => setShowRejectModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Reject Recommendation</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedRec && (
            <>
              <p><strong>Agent:</strong> {selectedRec.agent_name}</p>
              <p><strong>Title:</strong> {selectedRec.title}</p>
              <Form.Group>
                <Form.Label>Reason for rejection (optional)</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Why is this recommendation being rejected?"
                />
              </Form.Group>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowRejectModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleReject}>
            Reject Recommendation
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default SelfImprovementDashboard;
