import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Card, Form, Button, Badge, Spinner, Alert, ButtonGroup } from 'react-bootstrap';
import {
  generateSolution,
  getApplicationStatus,
  getRecentActivities,
  getAgentHierarchy,
  getAllAgentStates,
  getPendingQuestions,
  answerQuestion,
  getGeneratedFiles
} from './services/api';
import ActivityFeed from './components/ActivityFeed';
import AgentHierarchyTree from './components/AgentHierarchyTree';
import PendingQuestions from './components/PendingQuestions';
import GeneratedFiles from './components/GeneratedFiles';

function App() {
  const [problemInput, setProblemInput] = useState('');
  const [budgetTier, setBudgetTier] = useState('balanced');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Activity state
  const [activities, setActivities] = useState([]);
  const [hierarchy, setHierarchy] = useState({});
  const [agentStates, setAgentStates] = useState({});
  const [questions, setQuestions] = useState({});
  const [generatedFiles, setGeneratedFiles] = useState([]);
  const [appStatus, setAppStatus] = useState({ status: 'connecting', active_agents: 0 });

  // Polling configuration
  const [pollInterval, setPollInterval] = useState(1000); // 1 second default
  const [isPaused, setIsPaused] = useState(false);

  const pollTimerRef = useRef(null);

  // Fetch all activity data
  const fetchActivityData = async () => {
    if (isPaused) return;

    try {
      const [activitiesRes, hierarchyRes, statesRes, questionsRes, filesRes, statusRes] = await Promise.all([
        getRecentActivities({ limit: 200 }),
        getAgentHierarchy(),
        getAllAgentStates(),
        getPendingQuestions(),
        getGeneratedFiles({ limit: 100 }),
        getApplicationStatus()
      ]);

      setActivities(activitiesRes.activities || []);
      setHierarchy(hierarchyRes.hierarchy || {});
      setAgentStates(statesRes.agent_states || {});
      setQuestions(questionsRes.questions || {});
      setGeneratedFiles(filesRes.files || []);
      setAppStatus(statusRes);
    } catch (err) {
      console.error('Failed to fetch activity data:', err);
    }
  };

  // Set up polling
  useEffect(() => {
    // Initial fetch
    fetchActivityData();

    // Set up polling
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
    }

    pollTimerRef.current = setInterval(fetchActivityData, pollInterval);

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, [pollInterval, isPaused]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await generateSolution(problemInput, budgetTier);
      console.log('Solution generation started:', response);
    } catch (err) {
      setError('Failed to start solution generation');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAnswerQuestion = async (questionId, answer) => {
    await answerQuestion(questionId, answer);
    // Refresh questions immediately
    const questionsRes = await getPendingQuestions();
    setQuestions(questionsRes.questions || {});
  };

  const runningAgents = Object.values(agentStates).filter(s => s.status === 'running').length;
  const completedAgents = Object.values(agentStates).filter(s => s.status === 'completed').length;
  const failedAgents = Object.values(agentStates).filter(s => s.status === 'failed').length;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#1a1d29' }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#242836',
        borderBottom: '1px solid #3a3f52',
        padding: '12px 0'
      }}>
        <Container fluid>
          <Row>
            <Col>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <h4 style={{ margin: 0, color: '#e4e6eb' }}>🎭 Ensemble AI</h4>
                  <Badge bg={appStatus.status === 'running' ? 'success' : 'secondary'}>
                    {appStatus.status === 'running' ? 'Online' : 'Connecting...'}
                  </Badge>
                  <Badge bg="warning" text="dark">{runningAgents} Running</Badge>
                  <Badge bg="success">{completedAgents} Completed</Badge>
                  {failedAgents > 0 && <Badge bg="danger">{failedAgents} Failed</Badge>}
                </div>

                {/* Poll interval control */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '12px', color: '#9ca3af' }}>Update Interval:</span>
                  <ButtonGroup size="sm">
                    <Button
                      variant={pollInterval === 500 ? 'primary' : 'outline-secondary'}
                      onClick={() => setPollInterval(500)}
                    >
                      500ms
                    </Button>
                    <Button
                      variant={pollInterval === 1000 ? 'primary' : 'outline-secondary'}
                      onClick={() => setPollInterval(1000)}
                    >
                      1s
                    </Button>
                    <Button
                      variant={pollInterval === 2000 ? 'primary' : 'outline-secondary'}
                      onClick={() => setPollInterval(2000)}
                    >
                      2s
                    </Button>
                  </ButtonGroup>
                  <Button
                    variant={isPaused ? 'warning' : 'outline-secondary'}
                    size="sm"
                    onClick={() => setIsPaused(!isPaused)}
                  >
                    {isPaused ? '▶ Resume' : '⏸ Pause'}
                  </Button>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </div>

      <Container fluid style={{ padding: '16px' }}>
        <Row style={{ height: 'calc(100vh - 80px)' }}>
          {/* Left Column - Input & Questions */}
          <Col md={3} style={{ height: '100%', overflowY: 'auto' }}>
            {/* Input Form */}
            <Card bg="dark" text="light" className="mb-3">
              <Card.Header>
                <h6 className="mb-0">New Task</h6>
              </Card.Header>
              <Card.Body>
                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-3">
                    <Form.Label style={{ fontSize: '13px' }}>Problem Description</Form.Label>
                    <Form.Control
                      as="textarea"
                      rows={4}
                      value={problemInput}
                      onChange={(e) => setProblemInput(e.target.value)}
                      placeholder="Describe what you want to build..."
                      style={{
                        backgroundColor: '#1a1d29',
                        color: '#e4e6eb',
                        border: '1px solid #3a3f52',
                        fontSize: '13px'
                      }}
                    />
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label style={{ fontSize: '13px' }}>Budget Tier</Form.Label>
                    <Form.Select
                      value={budgetTier}
                      onChange={(e) => setBudgetTier(e.target.value)}
                      style={{
                        backgroundColor: '#1a1d29',
                        color: '#e4e6eb',
                        border: '1px solid #3a3f52',
                        fontSize: '13px'
                      }}
                    >
                      <option value="economical">Economical (Haiku)</option>
                      <option value="balanced">Balanced (Sonnet)</option>
                      <option value="full_firepower">Full Power (Opus)</option>
                    </Form.Select>
                  </Form.Group>

                  <Button
                    variant="primary"
                    type="submit"
                    disabled={isSubmitting || !problemInput}
                    style={{ width: '100%' }}
                  >
                    {isSubmitting ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Starting...
                      </>
                    ) : (
                      '🚀 Start Task'
                    )}
                  </Button>

                  {error && (
                    <Alert variant="danger" className="mt-3 mb-0" style={{ fontSize: '12px' }}>
                      {error}
                    </Alert>
                  )}
                </Form>
              </Card.Body>
            </Card>

            {/* Pending Questions */}
            <PendingQuestions questions={questions} onAnswer={handleAnswerQuestion} />

            {/* Agent Hierarchy */}
            <Card bg="dark" text="light">
              <Card.Header>
                <h6 className="mb-0">
                  Agent Hierarchy
                  <Badge bg="info" className="ms-2" style={{ fontSize: '10px' }}>
                    {Object.keys(hierarchy).length} agents
                  </Badge>
                </h6>
              </Card.Header>
              <Card.Body style={{ maxHeight: '400px', overflowY: 'auto', padding: '12px' }}>
                <AgentHierarchyTree hierarchy={hierarchy} />
              </Card.Body>
            </Card>
          </Col>

          {/* Middle Column - Activity Feed */}
          <Col md={5} style={{ height: '100%', overflowY: 'auto' }}>
            <Card bg="dark" text="light" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Card.Header>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h6 className="mb-0">
                    Activity Feed
                    <Badge bg="info" className="ms-2" style={{ fontSize: '10px' }}>
                      {activities.length} activities
                    </Badge>
                  </h6>
                  <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                    {isPaused ? '⏸ Paused' : `🔄 Updates every ${pollInterval}ms`}
                  </span>
                </div>
              </Card.Header>
              <Card.Body style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
                <ActivityFeed activities={activities} />
              </Card.Body>
            </Card>
          </Col>

          {/* Right Column - Agent States & Generated Files */}
          <Col md={4} style={{ height: '100%', overflowY: 'auto' }}>
            {/* Current Agent Tasks */}
            <Card bg="dark" text="light" className="mb-3">
              <Card.Header>
                <h6 className="mb-0">
                  Current Agent Tasks
                  <Badge bg="warning" text="dark" className="ms-2" style={{ fontSize: '10px' }}>
                    {runningAgents} active
                  </Badge>
                </h6>
              </Card.Header>
              <Card.Body style={{ maxHeight: '400px', overflowY: 'auto', padding: '12px' }}>
                {Object.keys(agentStates).length === 0 ? (
                  <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>
                    No agents running. Start a task to see agent activity here.
                  </div>
                ) : (
                  Object.entries(agentStates).map(([agentId, state]) => (
                    <div
                      key={agentId}
                      style={{
                        marginBottom: '12px',
                        padding: '12px',
                        backgroundColor: '#1a1d29',
                        borderRadius: '4px',
                        border: '1px solid #3a3f52'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <strong style={{ fontSize: '13px' }}>{agentId}</strong>
                        <Badge
                          bg={
                            state.status === 'running' ? 'warning' :
                            state.status === 'completed' ? 'success' :
                            state.status === 'failed' ? 'danger' :
                            state.status === 'awaiting_user_input' ? 'info' :
                            'secondary'
                          }
                          style={{ fontSize: '10px' }}
                        >
                          {state.status}
                        </Badge>
                      </div>

                      <div style={{ fontSize: '12px', color: '#e4e6eb', marginBottom: '6px' }}>
                        {state.current_task}
                      </div>

                      {state.current_iteration > 0 && (
                        <div style={{ fontSize: '11px', color: '#9ca3af' }}>
                          Iteration: {state.current_iteration}
                          {state.max_iterations && ` / ${state.max_iterations}`}
                        </div>
                      )}

                      <div style={{ fontSize: '10px', color: '#6b7280', marginTop: '6px' }}>
                        Started: {new Date(state.started_at).toLocaleTimeString()}
                      </div>
                    </div>
                  ))
                )}
              </Card.Body>
            </Card>

            {/* Generated Files */}
            <Card bg="dark" text="light">
              <Card.Header>
                <h6 className="mb-0">
                  Generated Files
                  <Badge bg="success" className="ms-2" style={{ fontSize: '10px' }}>
                    {generatedFiles.length} files
                  </Badge>
                </h6>
              </Card.Header>
              <Card.Body style={{ maxHeight: '600px', overflowY: 'auto', padding: '12px' }}>
                <GeneratedFiles files={generatedFiles} />
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default App;
