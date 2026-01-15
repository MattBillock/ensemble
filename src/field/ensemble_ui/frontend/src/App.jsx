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
import MetricsDashboard from './components/MetricsDashboard';
import HorizontalTimelineView from './components/HorizontalTimelineView';
import SelfImprovementDashboard from './components/SelfImprovementDashboard';
import AchievementsDashboard from './components/AchievementsDashboard';
import CostTrackingDashboard from './components/CostTrackingDashboard';
import RecoveryDashboard from './components/RecoveryDashboard';

function App() {
  const [currentView, setCurrentView] = useState('main'); // 'main', 'metrics', 'timeline', 'improve', 'achievements', 'costs', or 'recovery'
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

  // Filter state
  const [hideCompleted, setHideCompleted] = useState(false);
  const [activityFilter, setActivityFilter] = useState('all'); // all, spawned, completed, tool_use, error
  const [agentTypeFilter, setAgentTypeFilter] = useState('all'); // all, leadership, coordinators, developers, testers

  // Collapse state
  const [sectionsCollapsed, setSectionsCollapsed] = useState({
    hierarchy: false,
    agents: false,
    files: false
  });

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
  const failedAgents = Object.values(agentStates).filter(s => s.status === 'failed' || s.status === 'forever_failed').length;
  const foreverFailedAgents = Object.values(agentStates).filter(s => s.status === 'forever_failed').length;

  // Filter agents based on hideCompleted
  const filteredAgentStates = Object.entries(agentStates).filter(([_, state]) => {
    if (hideCompleted && state.status === 'completed') return false;
    return true;
  });

  // Filter activities based on activity filter
  const filteredActivities = activities.filter(activity => {
    if (activityFilter === 'all') return true;
    return activity.activity_type === activityFilter;
  });

  // Toggle collapse state
  const toggleSection = (section) => {
    setSectionsCollapsed(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

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
                  {foreverFailedAgents > 0 && <Badge bg="dark" style={{ border: '1px solid #dc3545' }}>☠️ {foreverFailedAgents} Terminated</Badge>}
                </div>

                {/* View Switcher and Poll interval control */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <ButtonGroup size="sm">
                    <Button
                      variant={currentView === 'main' ? 'primary' : 'outline-secondary'}
                      onClick={() => setCurrentView('main')}
                    >
                      🎭 Activity
                    </Button>
                    <Button
                      variant={currentView === 'timeline' ? 'primary' : 'outline-secondary'}
                      onClick={() => setCurrentView('timeline')}
                    >
                      ⏱️ Timeline
                    </Button>
                    <Button
                      variant={currentView === 'metrics' ? 'primary' : 'outline-secondary'}
                      onClick={() => setCurrentView('metrics')}
                    >
                      📊 Metrics
                    </Button>
                    <Button
                      variant={currentView === 'improve' ? 'primary' : 'outline-secondary'}
                      onClick={() => setCurrentView('improve')}
                    >
                      🔄 Improve
                    </Button>
                    <Button
                      variant={currentView === 'achievements' ? 'primary' : 'outline-secondary'}
                      onClick={() => setCurrentView('achievements')}
                    >
                      🏆 Achievements
                    </Button>
                    <Button
                      variant={currentView === 'costs' ? 'primary' : 'outline-secondary'}
                      onClick={() => setCurrentView('costs')}
                    >
                      💰 Costs
                    </Button>
                    <Button
                      variant={currentView === 'recovery' ? 'primary' : 'outline-secondary'}
                      onClick={() => setCurrentView('recovery')}
                    >
                      🔧 Recovery
                    </Button>
                  </ButtonGroup>

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

      {/* Conditional rendering based on current view */}
      {currentView === 'metrics' ? (
        <MetricsDashboard />
      ) : currentView === 'timeline' ? (
        <div style={{ height: 'calc(100vh - 80px)' }}>
          <HorizontalTimelineView />
        </div>
      ) : currentView === 'improve' ? (
        <SelfImprovementDashboard />
      ) : currentView === 'achievements' ? (
        <AchievementsDashboard />
      ) : currentView === 'costs' ? (
        <CostTrackingDashboard />
      ) : currentView === 'recovery' ? (
        <RecoveryDashboard />
      ) : (
        <>
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
              <Card.Header
                style={{ cursor: 'pointer' }}
                onClick={() => toggleSection('hierarchy')}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ marginRight: '8px' }}>
                      {sectionsCollapsed.hierarchy ? '▶' : '▼'}
                    </span>
                    <span style={{ fontSize: '14px' }}>Agent Hierarchy</span>
                    <Badge bg="info" className="ms-2" style={{ fontSize: '10px' }}>
                      {Object.keys(hierarchy).length} agents
                    </Badge>
                  </div>
                </div>
              </Card.Header>
              {!sectionsCollapsed.hierarchy && (
                <Card.Body style={{ maxHeight: '400px', overflowY: 'auto', padding: '12px' }}>
                  <AgentHierarchyTree hierarchy={hierarchy} />
                </Card.Body>
              )}
            </Card>
          </Col>

          {/* Middle Column - Activity Feed */}
          <Col md={5} style={{ height: '100%', overflowY: 'auto' }}>
            <Card bg="dark" text="light" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Card.Header>
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <h6 className="mb-0">
                      Activity Feed
                      <Badge bg="info" className="ms-2" style={{ fontSize: '10px' }}>
                        {filteredActivities.length} / {activities.length} activities
                      </Badge>
                    </h6>
                    <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                      {isPaused ? '⏸ Paused' : `🔄 Updates every ${pollInterval}ms`}
                    </span>
                  </div>
                  {/* Activity Filter */}
                  <Form.Select
                    size="sm"
                    value={activityFilter}
                    onChange={(e) => setActivityFilter(e.target.value)}
                    style={{
                      backgroundColor: '#1a1d29',
                      color: '#e4e6eb',
                      border: '1px solid #3a3f52',
                      fontSize: '12px'
                    }}
                  >
                    <option value="all">All Activities</option>
                    <option value="agent_spawned">Agent Spawned</option>
                    <option value="agent_completed">Agent Completed</option>
                    <option value="tool_use">Tool Use</option>
                    <option value="iteration_started">Iteration Started</option>
                    <option value="error">Errors</option>
                  </Form.Select>
                </div>
              </Card.Header>
              <Card.Body style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
                <ActivityFeed activities={filteredActivities} />
              </Card.Body>
            </Card>
          </Col>

          {/* Right Column - Agent States & Generated Files */}
          <Col md={4} style={{ height: '100%', overflowY: 'auto' }}>
            {/* Current Agent Tasks */}
            <Card bg="dark" text="light" className="mb-3">
              <Card.Header
                style={{ cursor: 'pointer' }}
                onClick={() => toggleSection('agents')}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div>
                    <span style={{ marginRight: '8px' }}>
                      {sectionsCollapsed.agents ? '▶' : '▼'}
                    </span>
                    <span style={{ fontSize: '14px' }}>Agent Tasks</span>
                    <Badge bg="warning" text="dark" className="ms-2" style={{ fontSize: '10px' }}>
                      {runningAgents} active
                    </Badge>
                    <Badge bg="success" className="ms-1" style={{ fontSize: '10px' }}>
                      {completedAgents} done
                    </Badge>
                    {failedAgents > 0 && (
                      <Badge bg="danger" className="ms-1" style={{ fontSize: '10px' }}>
                        {failedAgents} failed
                      </Badge>
                    )}
                  </div>
                </div>
                {!sectionsCollapsed.agents && (
                  <Form.Check
                    type="switch"
                    label="Hide completed"
                    checked={hideCompleted}
                    onChange={(e) => { e.stopPropagation(); setHideCompleted(!hideCompleted); }}
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      fontSize: '12px',
                      color: '#9ca3af',
                      cursor: 'pointer'
                    }}
                  />
                )}
              </Card.Header>
              {!sectionsCollapsed.agents && (
                <Card.Body style={{ maxHeight: '400px', overflowY: 'auto', padding: '12px' }}>
                  {filteredAgentStates.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>
                      {hideCompleted && Object.keys(agentStates).length > 0 ?
                        'All agents completed (toggle filter to see them)' :
                        'No agents running. Start a task to see agent activity here.'}
                    </div>
                  ) : (
                    filteredAgentStates.map(([agentId, state]) => (
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
                            state.status === 'forever_failed' ? 'dark' :
                            state.status === 'needs_review' ? 'info' :
                            state.status === 'awaiting_user_input' ? 'info' :
                            state.status === 'stalled' ? 'warning' :
                            'secondary'
                          }
                          style={{ fontSize: '10px', ...(state.status === 'forever_failed' ? { border: '1px solid #dc3545' } : {}) }}
                        >
                          {state.status === 'forever_failed' ? '☠️ TERMINATED' : state.status}
                        </Badge>
                      </div>

                      <div style={{ fontSize: '12px', color: '#e4e6eb', marginBottom: '8px' }}>
                        {state.current_task || 'Working...'}
                      </div>

                      {state.current_iteration > 0 && state.max_iterations > 0 && (
                        <div style={{ marginBottom: '8px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>
                            <span>Progress</span>
                            <span>{state.current_iteration} / {state.max_iterations}</span>
                          </div>
                          <div style={{
                            width: '100%',
                            height: '4px',
                            backgroundColor: '#3a3f52',
                            borderRadius: '2px',
                            overflow: 'hidden'
                          }}>
                            <div style={{
                              width: `${(state.current_iteration / (state.max_iterations || 1)) * 100}%`,
                              height: '100%',
                              backgroundColor: state.status === 'completed' ? '#10b981' : '#fbbf24',
                              transition: 'width 0.3s ease'
                            }} />
                          </div>
                        </div>
                      )}

                      <div style={{ fontSize: '10px', color: '#6b7280', marginTop: '6px' }}>
                        {state.started_at && (
                          <>Started: {new Date(state.started_at).toLocaleTimeString()}</>
                        )}
                        {state.status === 'completed' && state.completed_at && (
                          <span> • Completed: {new Date(state.completed_at).toLocaleTimeString()}</span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </Card.Body>
              )}
            </Card>

            {/* Generated Files */}
            <Card bg="dark" text="light">
              <Card.Header
                style={{ cursor: 'pointer' }}
                onClick={() => toggleSection('files')}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ marginRight: '8px' }}>
                      {sectionsCollapsed.files ? '▶' : '▼'}
                    </span>
                    <span style={{ fontSize: '14px' }}>Generated Files</span>
                    <Badge bg="success" className="ms-2" style={{ fontSize: '10px' }}>
                      {generatedFiles.length} files
                    </Badge>
                  </div>
                </div>
              </Card.Header>
              {!sectionsCollapsed.files && (
                <Card.Body style={{ maxHeight: '600px', overflowY: 'auto', padding: '12px' }}>
                  <GeneratedFiles files={generatedFiles} />
                </Card.Body>
              )}
            </Card>
          </Col>
        </Row>
        </Container>
        </>
      )}
    </div>
  );
}

export default App;
