import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Spinner, Form, Badge, ProgressBar } from 'react-bootstrap';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

function MetricsDashboard() {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);
  const [summary, setSummary] = useState(null);
  const [agentMetrics, setAgentMetrics] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [complexityMetrics, setComplexityMetrics] = useState(null);
  const [errorAnalysis, setErrorAnalysis] = useState(null);

  useEffect(() => {
    fetchMetrics();
  }, [timeRange]);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const [summaryRes, agentRes, modelRes, complexityRes, errorRes] = await Promise.all([
        fetch(`${API_BASE}/api/metrics/summary?days=${timeRange}`),
        fetch(`${API_BASE}/api/metrics/agents?days=${timeRange}`),
        fetch(`${API_BASE}/api/metrics/models?days=${timeRange}`),
        fetch(`${API_BASE}/api/metrics/complexity?days=${timeRange}`),
        fetch(`${API_BASE}/api/metrics/errors?days=${timeRange}`)
      ]);

      setSummary(await summaryRes.json());
      setAgentMetrics(await agentRes.json());
      setModelMetrics(await modelRes.json());
      setComplexityMetrics(await complexityRes.json());
      setErrorAnalysis(await errorRes.json());
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3">Loading metrics...</p>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4">
      <Row className="mb-4">
        <Col>
          <h2>📊 Metrics Dashboard</h2>
        </Col>
        <Col xs="auto">
          <Form.Select
            value={timeRange}
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
            style={{ width: '150px' }}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </Form.Select>
        </Col>
      </Row>

      {/* Summary Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card bg="primary" text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Total Executions
              </h6>
              <h3 className="mb-0">{summary?.overall?.total_executions || 0}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="success" text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Success Rate
              </h6>
              <h3 className="mb-0">{summary?.overall?.success_rate || 0}%</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="info" text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Unique Agents
              </h6>
              <h3 className="mb-0">{summary?.overall?.unique_agents || 0}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="warning" text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Avg Duration
              </h6>
              <h3 className="mb-0">
                {summary?.overall?.avg_duration_ms
                  ? `${(summary.overall.avg_duration_ms / 1000).toFixed(1)}s`
                  : 'N/A'}
              </h3>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col md={6}>
          {/* Most Active Agents */}
          <Card>
            <Card.Header>
              <strong>🔥 Most Active Agents</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '300px', overflowY: 'auto' }}>
              <Table hover size="sm" className="mb-0">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th className="text-end">Executions</th>
                  </tr>
                </thead>
                <tbody>
                  {summary?.most_active_agents?.map((agent, idx) => (
                    <tr key={idx}>
                      <td>
                        <code style={{ fontSize: '0.85rem' }}>
                          {agent.agent_name || <span style={{ color: '#6b7280', fontStyle: 'italic' }}>(unknown)</span>}
                        </code>
                      </td>
                      <td className="text-end">
                        <Badge bg="primary">{agent.executions}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          {/* Best Performing Agents */}
          <Card>
            <Card.Header>
              <strong>⭐ Best Performing Agents</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '300px', overflowY: 'auto' }}>
              <Table hover size="sm" className="mb-0">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th className="text-end">Success Rate</th>
                    <th className="text-end">Runs</th>
                  </tr>
                </thead>
                <tbody>
                  {summary?.best_performing_agents?.map((agent, idx) => (
                    <tr key={idx}>
                      <td>
                        <code style={{ fontSize: '0.85rem' }}>
                          {agent.agent_name || <span style={{ color: '#6b7280', fontStyle: 'italic' }}>(unknown)</span>}
                        </code>
                      </td>
                      <td className="text-end">
                        <Badge
                          bg={agent.success_rate >= 90 ? 'success' : agent.success_rate >= 70 ? 'warning' : 'danger'}
                        >
                          {agent.success_rate}%
                        </Badge>
                      </td>
                      <td className="text-end">{agent.executions}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Agent Performance */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header>
              <strong>🤖 Agent Performance</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Table hover size="sm">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th className="text-end">Total</th>
                    <th className="text-end">Success</th>
                    <th className="text-end">Failed</th>
                    <th className="text-end">Success Rate</th>
                    <th className="text-end">Avg Duration</th>
                    <th className="text-end">Avg Iterations</th>
                  </tr>
                </thead>
                <tbody>
                  {agentMetrics?.agents?.map((agent, idx) => (
                    <tr key={idx}>
                      <td>
                        <code style={{ fontSize: '0.85rem' }}>
                          {agent.agent_name || <span style={{ color: '#6b7280', fontStyle: 'italic' }}>(unknown)</span>}
                        </code>
                      </td>
                      <td className="text-end">{agent.total_executions}</td>
                      <td className="text-end">
                        <span style={{ color: '#10b981' }}>{agent.successful}</span>
                      </td>
                      <td className="text-end">
                        <span style={{ color: '#ef4444' }}>{agent.failed}</span>
                      </td>
                      <td className="text-end">
                        <div style={{ width: '100px', display: 'inline-block' }}>
                          <ProgressBar
                            now={agent.success_rate || 0}
                            min={0}
                            max={100}
                            variant={(agent.success_rate || 0) >= 90 ? 'success' : (agent.success_rate || 0) >= 70 ? 'warning' : 'danger'}
                            style={{ height: '20px' }}
                            label={`${agent.success_rate || 0}%`}
                          />
                        </div>
                      </td>
                      <td className="text-end">
                        {agent.avg_duration_ms ? `${(agent.avg_duration_ms / 1000).toFixed(1)}s` : 'N/A'}
                      </td>
                      <td className="text-end">{agent.avg_iterations}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col md={6}>
          {/* Model Performance */}
          <Card>
            <Card.Header>
              <strong>🧠 Model Performance</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Table hover size="sm">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th className="text-end">Runs</th>
                    <th className="text-end">Success Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {modelMetrics?.models?.map((model, idx) => {
                    const modelName = model.model_used.includes('sonnet') ? 'Sonnet 4.5' :
                                    model.model_used.includes('opus') ? 'Opus 4.5' :
                                    model.model_used.includes('haiku') ? 'Haiku 3.5' : model.model_used;
                    return (
                      <tr key={idx}>
                        <td>
                          <Badge bg="secondary">{modelName}</Badge>
                        </td>
                        <td className="text-end">{model.total_executions}</td>
                        <td className="text-end">
                          <div style={{ width: '100px', display: 'inline-block' }}>
                            <ProgressBar
                              now={model.success_rate || 0}
                              min={0}
                              max={100}
                              variant={(model.success_rate || 0) >= 90 ? 'success' : 'warning'}
                              style={{ height: '20px' }}
                              label={`${model.success_rate || 0}%`}
                            />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          {/* Complexity Performance */}
          <Card>
            <Card.Header>
              <strong>📈 Performance by Complexity</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Table hover size="sm">
                <thead>
                  <tr>
                    <th>Complexity</th>
                    <th className="text-end">Runs</th>
                    <th className="text-end">Success Rate</th>
                    <th className="text-end">Avg Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {complexityMetrics?.complexities?.map((item, idx) => (
                    <tr key={idx}>
                      <td>
                        <Badge
                          bg={item.task_complexity === 'simple' ? 'success' :
                              item.task_complexity === 'creative' ? 'warning' : 'danger'}
                        >
                          {item.task_complexity || 'unknown'}
                        </Badge>
                      </td>
                      <td className="text-end">{item.total_executions}</td>
                      <td className="text-end">
                        <div style={{ width: '100px', display: 'inline-block' }}>
                          <ProgressBar
                            now={item.success_rate || 0}
                            min={0}
                            max={100}
                            variant="info"
                            style={{ height: '20px' }}
                            label={`${item.success_rate || 0}%`}
                          />
                        </div>
                      </td>
                      <td className="text-end">
                        {item.avg_duration_ms ? `${(item.avg_duration_ms / 1000).toFixed(1)}s` : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Error Analysis */}
      {errorAnalysis?.errors && errorAnalysis.errors.length > 0 && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <strong>⚠️ Error Analysis</strong>
              </Card.Header>
              <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
                <Table hover size="sm">
                  <thead>
                    <tr>
                      <th>Error Type</th>
                      <th>Agent</th>
                      <th className="text-end">Occurrences</th>
                      <th className="text-end">Avg Time Before Failure</th>
                    </tr>
                  </thead>
                  <tbody>
                    {errorAnalysis.errors.map((error, idx) => (
                      <tr key={idx}>
                        <td>
                          <code style={{ fontSize: '0.85rem', color: '#ef4444' }}>
                            {error.error_type}
                          </code>
                        </td>
                        <td>
                          <code style={{ fontSize: '0.85rem' }}>
                            {error.agent_name || <span style={{ color: '#6b7280', fontStyle: 'italic' }}>(unknown)</span>}
                          </code>
                        </td>
                        <td className="text-end">
                          <Badge bg="danger">{error.occurrences}</Badge>
                        </td>
                        <td className="text-end">
                          {error.avg_duration_before_failure
                            ? `${(error.avg_duration_before_failure / 1000).toFixed(1)}s`
                            : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      <Row className="mb-4">
        <Col>
          <Card bg="light">
            <Card.Body>
              <p className="mb-0 text-muted" style={{ fontSize: '0.875rem' }}>
                <strong>Note:</strong> Metrics are calculated based on agent executions in the last {timeRange} days.
                Use the dropdown above to change the time range.
              </p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default MetricsDashboard;
