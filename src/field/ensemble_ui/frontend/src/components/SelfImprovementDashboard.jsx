import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Spinner, Button, Badge, Alert, Modal, Form } from 'react-bootstrap';
import {
  getSelfImprovementStatus,
  runSelfImprovementAnalysis,
  getRecommendations,
  approveRecommendation,
  rejectRecommendation
} from '../services/api';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

function SelfImprovementDashboard() {
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [status, setStatus] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedRec, setSelectedRec] = useState(null);
  const [rejectReason, setRejectReason] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, recsRes] = await Promise.all([
        getSelfImprovementStatus(),
        getRecommendations()
      ]);
      setStatus(statusRes);
      setRecommendations(recsRes.recommendations || []);
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
        <Col xs="auto">
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

      {/* Status Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card bg={status?.status === 'active' ? 'success' : 'secondary'} text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Loop Status
              </h6>
              <h3 className="mb-0">{status?.status || 'Unknown'}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="info" text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Feedback Injection
              </h6>
              <h3 className="mb-0">{status?.feedback_injection || 'N/A'}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="warning" text="dark">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Pending Recommendations
              </h6>
              <h3 className="mb-0">{status?.pending_recommendations || 0}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="primary" text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Total Processed
              </h6>
              <h3 className="mb-0">
                {(status?.approved_recommendations || 0) + (status?.rejected_recommendations || 0)}
              </h3>
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
                            variant="success"
                            size="sm"
                            className="me-1"
                            onClick={() => handleApprove(rec.id)}
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
          <Card bg="light">
            <Card.Body>
              <h6>How the Self-Improvement Loop Works</h6>
              <ol className="mb-0" style={{ fontSize: '0.875rem' }}>
                <li><strong>Collection:</strong> Every agent execution records metrics (success rate, duration, errors, self-analysis)</li>
                <li><strong>Analysis:</strong> The system periodically analyzes metrics to identify underperforming agents</li>
                <li><strong>Recommendations:</strong> Specific improvement suggestions are generated (model changes, definition tweaks)</li>
                <li><strong>Human Review:</strong> You approve or reject recommendations before they're applied</li>
                <li><strong>Feedback Injection:</strong> Approved insights are automatically included in agent prompts</li>
                <li><strong>Continuous Learning:</strong> The loop repeats, tracking whether changes improve performance</li>
              </ol>
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
