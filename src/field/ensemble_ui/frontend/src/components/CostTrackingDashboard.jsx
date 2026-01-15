import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Spinner, Form, Badge, ProgressBar } from 'react-bootstrap';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';

function CostTrackingDashboard() {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);
  const [costSummary, setCostSummary] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [agentMetrics, setAgentMetrics] = useState(null);

  useEffect(() => {
    fetchCostData();
  }, [timeRange]);

  const fetchCostData = async () => {
    setLoading(true);
    try {
      const [costRes, modelRes, agentRes] = await Promise.all([
        fetch(`${API_BASE}/api/costs/summary?days=${timeRange}`),
        fetch(`${API_BASE}/api/metrics/models?days=${timeRange}`),
        fetch(`${API_BASE}/api/metrics/agents?days=${timeRange}`)
      ]);

      setCostSummary(await costRes.json());
      setModelMetrics(await modelRes.json());
      setAgentMetrics(await agentRes.json());
    } catch (error) {
      console.error('Failed to fetch cost data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0.00';
    return `$${value.toFixed(4)}`;
  };

  const formatNumber = (value) => {
    if (value === null || value === undefined) return '0';
    return value.toLocaleString();
  };

  // Calculate cost estimates based on model usage
  const MODEL_COSTS = {
    'haiku': { input: 0.00025, output: 0.00125 },     // per 1K tokens
    'sonnet': { input: 0.003, output: 0.015 },        // per 1K tokens
    'opus': { input: 0.015, output: 0.075 }           // per 1K tokens
  };

  const getModelCostTier = (modelName) => {
    if (modelName?.includes('haiku')) return 'haiku';
    if (modelName?.includes('opus')) return 'opus';
    return 'sonnet'; // default
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" variant="success" />
        <p className="mt-3">Loading cost data...</p>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4">
      <Row className="mb-4">
        <Col>
          <h2>Cost Tracking Dashboard</h2>
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

      {/* Cost Summary Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: 'white' }}>
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Total Cost (Est.)
              </h6>
              <h3 className="mb-0">{formatCurrency(costSummary?.estimated_costs?.total_cost_usd)}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)', color: 'white' }}>
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Input Tokens
              </h6>
              <h3 className="mb-0">{formatNumber(costSummary?.token_usage?.total_input_tokens)}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card style={{ background: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)', color: 'white' }}>
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Output Tokens
              </h6>
              <h3 className="mb-0">{formatNumber(costSummary?.token_usage?.total_output_tokens)}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', color: 'white' }}>
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Total Executions
              </h6>
              <h3 className="mb-0">{formatNumber(costSummary?.execution_stats?.total_executions)}</h3>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Cost Breakdown by Input/Output */}
      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Header>
              <strong>Cost Breakdown</strong>
            </Card.Header>
            <Card.Body>
              <Table hover size="sm" className="mb-0">
                <tbody>
                  <tr>
                    <td>Input Token Cost</td>
                    <td className="text-end">
                      <Badge bg="primary">{formatCurrency(costSummary?.estimated_costs?.input_cost_usd)}</Badge>
                    </td>
                  </tr>
                  <tr>
                    <td>Output Token Cost</td>
                    <td className="text-end">
                      <Badge bg="info">{formatCurrency(costSummary?.estimated_costs?.output_cost_usd)}</Badge>
                    </td>
                  </tr>
                  <tr className="table-active">
                    <td><strong>Total Estimated Cost</strong></td>
                    <td className="text-end">
                      <Badge bg="success">{formatCurrency(costSummary?.estimated_costs?.total_cost_usd)}</Badge>
                    </td>
                  </tr>
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          <Card>
            <Card.Header>
              <strong>Execution Statistics</strong>
            </Card.Header>
            <Card.Body>
              <Table hover size="sm" className="mb-0">
                <tbody>
                  <tr>
                    <td>Successful Executions</td>
                    <td className="text-end">
                      <Badge bg="success">{formatNumber(costSummary?.execution_stats?.successful_executions)}</Badge>
                    </td>
                  </tr>
                  <tr>
                    <td>Failed Executions</td>
                    <td className="text-end">
                      <Badge bg="danger">{formatNumber(costSummary?.execution_stats?.failed_executions)}</Badge>
                    </td>
                  </tr>
                  <tr className="table-active">
                    <td><strong>Total Executions</strong></td>
                    <td className="text-end">
                      <Badge bg="primary">{formatNumber(costSummary?.execution_stats?.total_executions)}</Badge>
                    </td>
                  </tr>
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Cost by Model */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header>
              <strong>Cost by Model</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Table hover size="sm">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th className="text-end">Executions</th>
                    <th className="text-end">Input Cost Rate</th>
                    <th className="text-end">Output Cost Rate</th>
                    <th className="text-end">Success Rate</th>
                    <th className="text-end">Cost Efficiency</th>
                  </tr>
                </thead>
                <tbody>
                  {modelMetrics?.models?.map((model, idx) => {
                    const tier = getModelCostTier(model.model_used);
                    const costs = MODEL_COSTS[tier];
                    const modelName = model.model_used.includes('sonnet') ? 'Sonnet 4.5' :
                                    model.model_used.includes('opus') ? 'Opus 4.5' :
                                    model.model_used.includes('haiku') ? 'Haiku 3.5' : model.model_used;

                    // Cost efficiency = success rate / relative cost
                    const relativeCost = tier === 'haiku' ? 1 : tier === 'sonnet' ? 12 : 60;
                    const efficiency = ((model.success_rate || 0) / relativeCost * 10).toFixed(1);

                    return (
                      <tr key={idx}>
                        <td>
                          <Badge bg={tier === 'haiku' ? 'success' : tier === 'sonnet' ? 'primary' : 'warning'}>
                            {modelName}
                          </Badge>
                        </td>
                        <td className="text-end">{formatNumber(model.total_executions)}</td>
                        <td className="text-end">
                          <code style={{ fontSize: '0.8rem' }}>${costs.input}/1K</code>
                        </td>
                        <td className="text-end">
                          <code style={{ fontSize: '0.8rem' }}>${costs.output}/1K</code>
                        </td>
                        <td className="text-end">
                          <div style={{ width: '80px', display: 'inline-block' }}>
                            <ProgressBar
                              now={model.success_rate || 0}
                              min={0}
                              max={100}
                              variant={(model.success_rate || 0) >= 90 ? 'success' : 'warning'}
                              style={{ height: '18px' }}
                              label={`${model.success_rate || 0}%`}
                            />
                          </div>
                        </td>
                        <td className="text-end">
                          <Badge bg={efficiency >= 5 ? 'success' : efficiency >= 2 ? 'warning' : 'danger'}>
                            {efficiency}x
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Top Token Consumers */}
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header>
              <strong>Agent Resource Usage</strong>
            </Card.Header>
            <Card.Body style={{ maxHeight: '400px', overflowY: 'auto' }}>
              <Table hover size="sm">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th className="text-end">Executions</th>
                    <th className="text-end">Success Rate</th>
                    <th className="text-end">Avg Duration</th>
                    <th className="text-end">Avg Iterations</th>
                    <th className="text-end">Est. Cost/Run</th>
                  </tr>
                </thead>
                <tbody>
                  {agentMetrics?.agents?.map((agent, idx) => {
                    // Rough cost estimate based on iterations and typical token usage
                    const estTokensPerIteration = 2000; // rough estimate
                    const estCostPerRun = ((agent.avg_iterations || 1) * estTokensPerIteration * 0.003 / 1000).toFixed(4);

                    return (
                      <tr key={idx}>
                        <td>
                          <code style={{ fontSize: '0.85rem' }}>{agent.agent_name}</code>
                        </td>
                        <td className="text-end">{formatNumber(agent.total_executions)}</td>
                        <td className="text-end">
                          <Badge
                            bg={(agent.success_rate || 0) >= 90 ? 'success' : (agent.success_rate || 0) >= 70 ? 'warning' : 'danger'}
                          >
                            {agent.success_rate || 0}%
                          </Badge>
                        </td>
                        <td className="text-end">
                          {agent.avg_duration_ms ? `${(agent.avg_duration_ms / 1000).toFixed(1)}s` : 'N/A'}
                        </td>
                        <td className="text-end">{agent.avg_iterations || 0}</td>
                        <td className="text-end">
                          <code style={{ fontSize: '0.8rem', color: '#10b981' }}>~${estCostPerRun}</code>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Cost Optimization Tips */}
      <Row className="mb-4">
        <Col>
          <Card bg="light">
            <Card.Header>
              <strong>Cost Optimization Tips</strong>
            </Card.Header>
            <Card.Body>
              <ul className="mb-0" style={{ fontSize: '0.9rem' }}>
                <li><strong>Use Haiku for simple tasks:</strong> 60x cheaper than Opus for routine work.</li>
                <li><strong>Reduce iterations:</strong> Each iteration adds ~$0.006 (Sonnet) or more in token costs.</li>
                <li><strong>Monitor failed executions:</strong> Failed runs still consume tokens without delivering value.</li>
                <li><strong>Optimize prompts:</strong> Shorter, clearer prompts reduce input token costs.</li>
                <li><strong>Use model routing:</strong> Let the system automatically select the cheapest appropriate model.</li>
              </ul>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mb-4">
        <Col>
          <Card bg="light">
            <Card.Body>
              <p className="mb-0 text-muted" style={{ fontSize: '0.875rem' }}>
                <strong>Note:</strong> Cost estimates are based on Anthropic's published pricing.
                Actual costs may vary based on your specific API agreement.
                Data shown is for the last {timeRange} days.
              </p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default CostTrackingDashboard;
