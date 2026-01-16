import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Spinner, Button, Badge, Alert, ListGroup, ButtonGroup } from 'react-bootstrap';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  getPendingReviews,
  getPendingReviewContent,
  approvePendingReview,
  rejectPendingReview,
  scanForPendingReviews,
  approveAllPendingReviews
} from '../services/api';

function PendingReviewDashboard() {
  const [loading, setLoading] = useState(true);
  const [reviews, setReviews] = useState([]);
  const [inProgressReviews, setInProgressReviews] = useState([]);
  const [statusFilter, setStatusFilter] = useState('pending'); // 'pending' or 'in_progress'
  const [selectedReview, setSelectedReview] = useState(null);
  const [selectedContent, setSelectedContent] = useState(null);
  const [loadingContent, setLoadingContent] = useState(false);
  const [approving, setApproving] = useState(false);
  const [approvingAll, setApprovingAll] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    fetchReviews();
    // Poll for in_progress updates every 10 seconds
    const pollInterval = setInterval(fetchInProgressReviews, 10000);
    return () => clearInterval(pollInterval);
  }, []);

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const [pendingResult, inProgressResult] = await Promise.all([
        getPendingReviews('pending'),
        getPendingReviews('in_progress')
      ]);
      setReviews(pendingResult.reviews || []);
      setInProgressReviews(inProgressResult.reviews || []);
    } catch (err) {
      setError('Failed to load pending reviews');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchInProgressReviews = async () => {
    try {
      const result = await getPendingReviews('in_progress');
      setInProgressReviews(result.reviews || []);
    } catch (err) {
      console.error('Failed to fetch in-progress reviews:', err);
    }
  };

  const handleSelectReview = async (review) => {
    setSelectedReview(review);
    setLoadingContent(true);
    setError(null);
    try {
      const content = await getPendingReviewContent(review.id);
      setSelectedContent(content);
    } catch (err) {
      setError('Failed to load file content');
      console.error(err);
    } finally {
      setLoadingContent(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedReview) return;
    setApproving(true);
    setError(null);
    try {
      const result = await approvePendingReview(selectedReview.id);
      setSuccessMessage(`Approved! Agent ${result.result?.agent_id || ''} spawned.`);
      await fetchReviews();
      setSelectedReview(null);
      setSelectedContent(null);
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError('Failed to approve review');
      console.error(err);
    } finally {
      setApproving(false);
    }
  };

  const handleReject = async () => {
    if (!selectedReview) return;
    setError(null);
    try {
      await rejectPendingReview(selectedReview.id);
      setSuccessMessage('Review rejected.');
      await fetchReviews();
      setSelectedReview(null);
      setSelectedContent(null);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to reject review');
      console.error(err);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    setError(null);
    try {
      const result = await scanForPendingReviews();
      if (result.new_reviews > 0) {
        setSuccessMessage(`Found ${result.new_reviews} new reviewable file(s).`);
      } else {
        setSuccessMessage('No new reviewable files found.');
      }
      await fetchReviews();
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to scan for reviews');
      console.error(err);
    } finally {
      setScanning(false);
    }
  };

  const handleApproveAll = async () => {
    if (reviews.length === 0) return;
    setApprovingAll(true);
    setError(null);
    try {
      const result = await approveAllPendingReviews();
      setSuccessMessage(result.message || `Approved ${result.approved} reviews.`);
      await fetchReviews();
      setSelectedReview(null);
      setSelectedContent(null);
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError('Failed to approve all reviews');
      console.error(err);
    } finally {
      setApprovingAll(false);
    }
  };

  const getTypeBadge = (reviewType) => {
    const colors = {
      requirements: 'primary',
      architecture: 'info',
      milestone: 'success',
      plan: 'secondary',
      tasks: 'warning',
      test_plan: 'danger',
      general: 'dark'
    };
    return <Badge bg={colors[reviewType] || 'secondary'}>{reviewType || 'unknown'}</Badge>;
  };

  const getDetectionBadge = (method) => {
    return (
      <Badge bg={method === 'explicit' ? 'success' : 'warning'} text="dark">
        {method === 'explicit' ? 'Reported' : 'Auto-detected'}
      </Badge>
    );
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3 text-light">Loading pending reviews...</p>
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
          <h2 className="text-light">Pending Reviews</h2>
          <p style={{ color: '#9ca3af' }}>
            Review and approve generated documents before implementation.
          </p>
        </Col>
        <Col xs="auto" className="d-flex gap-2 align-items-center">
          <ButtonGroup size="sm">
            <Button
              variant={statusFilter === 'pending' ? 'primary' : 'outline-secondary'}
              onClick={() => setStatusFilter('pending')}
            >
              Pending ({reviews.length})
            </Button>
            <Button
              variant={statusFilter === 'in_progress' ? 'success' : 'outline-secondary'}
              onClick={() => setStatusFilter('in_progress')}
            >
              In Progress ({inProgressReviews.length})
            </Button>
          </ButtonGroup>
          <Button
            variant="outline-primary"
            onClick={handleScan}
            disabled={scanning}
          >
            {scanning ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Scanning...
              </>
            ) : (
              'Scan for New Files'
            )}
          </Button>
          <Button
            variant="success"
            onClick={handleApproveAll}
            disabled={approvingAll || reviews.length === 0}
            className="ms-2"
          >
            {approvingAll ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Approving All...
              </>
            ) : (
              `Approve All (${reviews.length})`
            )}
          </Button>
        </Col>
      </Row>

      <Row style={{ height: 'calc(100% - 80px)' }}>
        {/* Left Pane - Review List */}
        <Col md={4} style={{ height: '100%', overflowY: 'auto' }}>
          <Card bg="dark" text="light" style={{ height: '100%' }}>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <strong>{statusFilter === 'pending' ? 'Pending Items' : 'In Progress'}</strong>
              <Badge bg={statusFilter === 'pending' ? 'warning' : 'success'} text="dark">
                {statusFilter === 'pending' ? reviews.length : inProgressReviews.length}
              </Badge>
            </Card.Header>
            <ListGroup variant="flush" style={{ overflowY: 'auto' }}>
              {(statusFilter === 'pending' ? reviews : inProgressReviews).length === 0 ? (
                <ListGroup.Item variant="dark" className="text-center" style={{ color: '#9ca3af' }}>
                  {statusFilter === 'pending'
                    ? 'No pending reviews. Click "Scan for New Files" to check.'
                    : 'No in-progress reviews.'}
                </ListGroup.Item>
              ) : (
                (statusFilter === 'pending' ? reviews : inProgressReviews).map((review) => {
                  const agentId = review.execution_result?.agent_id;
                  return (
                    <ListGroup.Item
                      key={review.id}
                      variant="dark"
                      action
                      active={selectedReview?.id === review.id}
                      onClick={() => handleSelectReview(review)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="d-flex justify-content-between align-items-start">
                        <div style={{ maxWidth: '60%' }}>
                          <div className="fw-bold text-truncate" style={{ fontSize: '0.9rem' }}>
                            {review.file_path?.split('/').pop() || 'Unknown file'}
                          </div>
                          <small className="text-muted d-block text-truncate">
                            {review.agent_name || 'Unknown agent'}
                          </small>
                          <small className="text-muted">
                            {formatDate(review.created_at)}
                          </small>
                          {statusFilter === 'in_progress' && agentId && (
                            <div className="mt-1">
                              <Badge bg="info" style={{ fontSize: '0.7rem' }}>
                                Agent: {agentId.slice(0, 12)}...
                              </Badge>
                            </div>
                          )}
                        </div>
                        <div className="text-end">
                          {statusFilter === 'in_progress' ? (
                            <Badge bg="success">Running</Badge>
                          ) : (
                            getTypeBadge(review.review_type)
                          )}
                          <br />
                          <small>{getDetectionBadge(review.detection_method)}</small>
                        </div>
                      </div>
                    </ListGroup.Item>
                  );
                })
              )}
            </ListGroup>
          </Card>
        </Col>

        {/* Right Pane - Content Viewer */}
        <Col md={8} style={{ height: '100%', overflowY: 'auto' }}>
          <Card bg="dark" text="light" style={{ height: '100%' }}>
            {!selectedReview ? (
              <Card.Body className="d-flex align-items-center justify-content-center">
                <div className="text-center" style={{ color: '#9ca3af' }}>
                  <div style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>
                    Select a review to view its content
                  </div>
                  <p>
                    Click on an item from the list on the left to see the document
                    and approve or reject it.
                  </p>
                </div>
              </Card.Body>
            ) : (
              <>
                <Card.Header>
                  <div className="d-flex justify-content-between align-items-center flex-wrap">
                    <div style={{ maxWidth: '60%' }}>
                      <strong className="d-block text-truncate">{selectedReview.file_path}</strong>
                      <small className="text-muted">
                        Action: <code>{selectedReview.action || 'start_implementation'}</code>
                      </small>
                    </div>
                    <div className="mt-2 mt-md-0">
                      <Button
                        variant="success"
                        className="me-2"
                        onClick={handleApprove}
                        disabled={approving}
                      >
                        {approving ? (
                          <>
                            <Spinner animation="border" size="sm" className="me-2" />
                            Approving...
                          </>
                        ) : (
                          'Approve & Execute'
                        )}
                      </Button>
                      <Button variant="outline-danger" onClick={handleReject}>
                        Reject
                      </Button>
                    </div>
                  </div>
                </Card.Header>
                <Card.Body style={{ overflowY: 'auto' }}>
                  {loadingContent ? (
                    <div className="text-center py-4">
                      <Spinner animation="border" variant="primary" />
                      <p className="mt-2" style={{ color: '#9ca3af' }}>Loading content...</p>
                    </div>
                  ) : selectedContent ? (
                    <div className="markdown-content" style={{ color: '#e4e6eb' }}>
                      {selectedContent.frontmatter && Object.keys(selectedContent.frontmatter).length > 0 && (
                        <Alert variant="info" className="mb-3">
                          <strong>Frontmatter:</strong>
                          <pre className="mb-0 mt-2" style={{ fontSize: '0.85rem' }}>
                            {JSON.stringify(selectedContent.frontmatter, null, 2)}
                          </pre>
                        </Alert>
                      )}
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {selectedContent.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-center" style={{ color: '#9ca3af' }}>No content available</p>
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

export default PendingReviewDashboard;
