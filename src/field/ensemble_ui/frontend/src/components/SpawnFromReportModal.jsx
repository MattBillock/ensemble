import React, { useState } from 'react';
import { Modal, Button, Form, Alert, Spinner } from 'react-bootstrap';
import { spawnTaskFromReport } from '../services/api';

/**
 * SpawnFromReportModal - Modal for spawning a new task from a completed report
 *
 * Allows users to:
 * - Enter a problem description for the follow-up task
 * - Select budget tier
 * - Configure auto-continue settings
 */
function SpawnFromReportModal({ show, onHide, report, onSpawnComplete }) {
  const [problemDescription, setProblemDescription] = useState('');
  const [budgetTier, setBudgetTier] = useState('balanced');
  const [autoContinue, setAutoContinue] = useState(true);
  const [fullyAutonomous, setFullyAutonomous] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!problemDescription.trim()) {
      setError('Please enter a problem description');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await spawnTaskFromReport(report.id, {
        problemDescription: problemDescription.trim(),
        budgetTier,
        autoContinue,
        fullyAutonomous
      });

      setSuccess(`Task started with ID: ${result.request_id}`);

      // Call completion handler
      if (onSpawnComplete) {
        onSpawnComplete(result);
      }

      // Reset form after short delay
      setTimeout(() => {
        setProblemDescription('');
        setSuccess(null);
        onHide();
      }, 2000);

    } catch (err) {
      setError(err.message || 'Failed to start task');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setProblemDescription('');
      setError(null);
      setSuccess(null);
      onHide();
    }
  };

  return (
    <Modal show={show} onHide={handleClose} size="lg" centered>
      <Modal.Header
        closeButton
        style={{ backgroundColor: '#242836', borderColor: '#3a3f52' }}
      >
        <Modal.Title style={{ color: '#e4e6eb' }}>
          Start New Task From Report
        </Modal.Title>
      </Modal.Header>

      <Modal.Body style={{ backgroundColor: '#1a1d29' }}>
        {report && (
          <div
            style={{
              padding: '12px',
              backgroundColor: '#242836',
              borderRadius: '4px',
              marginBottom: '16px',
              border: '1px solid #3a3f52'
            }}
          >
            <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>
              Source Report
            </div>
            <div style={{ fontSize: '14px', color: '#e4e6eb', fontWeight: 500 }}>
              {report.title || report.file_name}
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>
              The new task will have access to this report's content as context.
            </div>
          </div>
        )}

        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label style={{ color: '#e4e6eb', fontSize: '13px' }}>
              What do you want to do next?
            </Form.Label>
            <Form.Control
              as="textarea"
              rows={4}
              value={problemDescription}
              onChange={(e) => setProblemDescription(e.target.value)}
              placeholder="Describe the follow-up task you want the agent to work on..."
              disabled={isSubmitting}
              style={{
                backgroundColor: '#242836',
                color: '#e4e6eb',
                border: '1px solid #3a3f52',
                fontSize: '13px'
              }}
            />
            <Form.Text style={{ color: '#6b7280' }}>
              Be specific about what you want to accomplish. The agent will have context from the source report.
            </Form.Text>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label style={{ color: '#e4e6eb', fontSize: '13px' }}>
              Budget Tier
            </Form.Label>
            <Form.Select
              value={budgetTier}
              onChange={(e) => setBudgetTier(e.target.value)}
              disabled={isSubmitting}
              style={{
                backgroundColor: '#242836',
                color: '#e4e6eb',
                border: '1px solid #3a3f52',
                fontSize: '13px'
              }}
            >
              <option value="economical">Economical (Haiku) - Fast & cheap</option>
              <option value="balanced">Balanced (Sonnet) - Good balance</option>
              <option value="full_firepower">Full Power (Opus) - Most capable</option>
            </Form.Select>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Check
              type="switch"
              id="auto-continue"
              label="Auto-continue through milestones"
              checked={autoContinue}
              onChange={(e) => setAutoContinue(e.target.checked)}
              disabled={isSubmitting}
              style={{ color: '#e4e6eb', fontSize: '13px' }}
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Check
              type="switch"
              id="fully-autonomous"
              label="Fully autonomous (skip all reviews)"
              checked={fullyAutonomous}
              onChange={(e) => setFullyAutonomous(e.target.checked)}
              disabled={isSubmitting}
              style={{ color: '#e4e6eb', fontSize: '13px' }}
            />
            {fullyAutonomous && (
              <Form.Text style={{ color: '#f59e0b' }}>
                Warning: The agent will make all decisions without human review.
              </Form.Text>
            )}
          </Form.Group>

          {error && (
            <Alert variant="danger" className="mb-3">
              {error}
            </Alert>
          )}

          {success && (
            <Alert variant="success" className="mb-3">
              {success}
            </Alert>
          )}
        </Form>
      </Modal.Body>

      <Modal.Footer style={{ backgroundColor: '#242836', borderColor: '#3a3f52' }}>
        <Button variant="secondary" onClick={handleClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSubmit} disabled={isSubmitting || !problemDescription.trim()}>
          {isSubmitting ? (
            <>
              <Spinner animation="border" size="sm" className="me-2" />
              Starting...
            </>
          ) : (
            'Start Task'
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

export default SpawnFromReportModal;
