import React, { useState } from 'react';
import { Card, Form, Button, Badge, Alert } from 'react-bootstrap';

const PendingQuestions = ({ questions = {}, onAnswer }) => {
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(new Set());

  const handleAnswer = async (questionId) => {
    const answer = answers[questionId];
    if (!answer) return;

    setSubmitting(new Set(submitting).add(questionId));

    try {
      await onAnswer(questionId, answer);
      // Clear answer after successful submission
      const newAnswers = { ...answers };
      delete newAnswers[questionId];
      setAnswers(newAnswers);
    } catch (error) {
      console.error('Failed to submit answer:', error);
    } finally {
      const newSubmitting = new Set(submitting);
      newSubmitting.delete(questionId);
      setSubmitting(newSubmitting);
    }
  };

  const questionEntries = Object.entries(questions);

  if (questionEntries.length === 0) {
    return null;
  }

  return (
    <Card bg="dark" text="light" className="mb-3" style={{ border: '2px solid #f59e0b' }}>
      <Card.Header style={{ backgroundColor: '#f59e0b', color: '#000' }}>
        <h5 className="mb-0">
          ❓ Agent Questions
          <Badge bg="light" text="dark" className="ms-2">
            {questionEntries.length} pending
          </Badge>
        </h5>
      </Card.Header>
      <Card.Body>
        <Alert variant="warning" className="mb-3">
          <strong>Action Required:</strong> Agents are waiting for your response to continue.
        </Alert>

        {questionEntries.map(([questionId, questionData]) => (
          <div
            key={questionId}
            style={{
              marginBottom: '16px',
              padding: '12px',
              backgroundColor: '#1a1d29',
              borderRadius: '4px',
              border: '1px solid #f59e0b'
            }}
          >
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Badge bg="info">{questionData.agent_name}</Badge>
                <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                  Asked at {new Date(questionData.asked_at).toLocaleTimeString()}
                </span>
              </div>
              <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                {questionData.question}
              </div>
            </div>

            {questionData.options && questionData.options.length > 0 ? (
              <Form.Group>
                <Form.Select
                  value={answers[questionId] || ''}
                  onChange={(e) => setAnswers({ ...answers, [questionId]: e.target.value })}
                  style={{
                    backgroundColor: '#242836',
                    color: '#e4e6eb',
                    border: '1px solid #3a3f52',
                    marginBottom: '8px'
                  }}
                >
                  <option value="">-- Select an option --</option>
                  {questionData.options.map((option, idx) => (
                    <option key={idx} value={option}>
                      {option}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            ) : (
              <Form.Group>
                <Form.Control
                  as="textarea"
                  rows={2}
                  value={answers[questionId] || ''}
                  onChange={(e) => setAnswers({ ...answers, [questionId]: e.target.value })}
                  placeholder="Type your answer..."
                  style={{
                    backgroundColor: '#242836',
                    color: '#e4e6eb',
                    border: '1px solid #3a3f52',
                    marginBottom: '8px'
                  }}
                />
              </Form.Group>
            )}

            <Button
              variant="warning"
              size="sm"
              onClick={() => handleAnswer(questionId)}
              disabled={!answers[questionId] || submitting.has(questionId)}
            >
              {submitting.has(questionId) ? 'Submitting...' : 'Submit Answer'}
            </Button>
          </div>
        ))}
      </Card.Body>
    </Card>
  );
};

export default PendingQuestions;
