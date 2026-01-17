import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Badge, ProgressBar, Button, Spinner, Table } from 'react-bootstrap';

const API_BASE_URL = 'http://localhost:8001';

/**
 * Projects Dashboard - View and manage projects across the ensemble system
 */
function ProjectsDashboard() {
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(null);

  useEffect(() => {
    fetchProjects();
    const interval = setInterval(fetchProjects, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/summary`);
      const data = await response.json();
      setProjects(data.projects || []);
      setSummary(data.summary || {});
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      setLoading(false);
    }
  };

  const getStatusBadge = (project) => {
    if (project.active_agents > 0) {
      return <Badge bg="primary">Active</Badge>;
    }
    if (project.failed_agents > 0 && project.completed_agents === 0) {
      return <Badge bg="danger">Failed</Badge>;
    }
    if (project.awaiting_input > 0) {
      return <Badge bg="warning">Awaiting Input</Badge>;
    }
    if (project.completed_agents > 0) {
      return <Badge bg="success">Completed</Badge>;
    }
    return <Badge bg="secondary">Unknown</Badge>;
  };

  const getStageBadge = (stage) => {
    const stageColors = {
      requirements: 'info',
      architecture: 'primary',
      planning: 'secondary',
      implementation: 'warning',
      testing: 'info',
      complete: 'success',
      unknown: 'secondary'
    };
    return (
      <Badge bg={stageColors[stage] || 'secondary'}>
        {stage.charAt(0).toUpperCase() + stage.slice(1)}
      </Badge>
    );
  };

  const getCompletionPercentage = (project) => {
    const total = project.total_agents || 1;
    const completed = project.completed_agents || 0;
    return Math.round((completed / total) * 100);
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" variant="primary" />
        <p className="mt-3 text-light">Loading projects...</p>
      </Container>
    );
  }

  return (
    <Container fluid className="mt-4">
      <Row className="mb-4">
        <Col>
          <h2>📁 Projects Dashboard</h2>
          <p style={{ color: '#9ca3af' }}>
            View and manage all projects in the ensemble system
          </p>
        </Col>
      </Row>

      {/* Summary Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card bg="primary" text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Total Projects
              </h6>
              <h3 className="mb-0">{summary?.total_projects || 0}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card bg="success" text="white">
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                Active Projects
              </h6>
              <h3 className="mb-0">{summary?.active_projects || 0}</h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Body>
              <h6 className="text-uppercase mb-1" style={{ fontSize: '0.75rem', opacity: 0.6 }}>
                Stage Distribution
              </h6>
              <div className="d-flex gap-2 flex-wrap">
                {Object.entries(summary?.stage_distribution || {}).map(([stage, count]) => (
                  <span key={stage}>
                    {getStageBadge(stage)} <span className="ms-1">{count}</span>
                  </span>
                ))}
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Projects List */}
      <Row>
        <Col md={selectedProject ? 5 : 12}>
          <Card>
            <Card.Header>
              <strong>📋 All Projects</strong>
              <span className="ms-2 text-muted">({projects.length} total)</span>
            </Card.Header>
            <Card.Body style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {projects.length === 0 ? (
                <p className="text-muted text-center py-4">
                  No projects found. Start a new task to create a project!
                </p>
              ) : (
                <Table hover size="sm" className="mb-0">
                  <thead>
                    <tr>
                      <th>Project</th>
                      <th>Status</th>
                      <th>Stage</th>
                      <th>Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projects.map((project) => (
                      <tr
                        key={project.project_id}
                        onClick={() => setSelectedProject(project)}
                        style={{ cursor: 'pointer' }}
                        className={selectedProject?.project_id === project.project_id ? 'table-active' : ''}
                      >
                        <td>
                          <div>
                            <strong>{project.project_name || 'Unnamed Project'}</strong>
                            <br />
                            <small className="text-muted">
                              <code>{project.project_id?.slice(0, 12)}...</code>
                            </small>
                          </div>
                        </td>
                        <td>{getStatusBadge(project)}</td>
                        <td>{getStageBadge(project.current_stage)}</td>
                        <td style={{ width: '150px' }}>
                          <ProgressBar
                            now={getCompletionPercentage(project)}
                            variant={project.failed_agents > 0 ? 'danger' : 'success'}
                            style={{ height: '8px' }}
                          />
                          <small className="text-muted">
                            {project.completed_agents}/{project.total_agents} agents
                          </small>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* Project Details Panel */}
        {selectedProject && (
          <Col md={7}>
            <Card>
              <Card.Header className="d-flex justify-content-between align-items-center">
                <strong>📊 Project Details</strong>
                <Button
                  variant="outline-secondary"
                  size="sm"
                  onClick={() => setSelectedProject(null)}
                >
                  ✕
                </Button>
              </Card.Header>
              <Card.Body>
                <h5>{selectedProject.project_name || 'Unnamed Project'}</h5>
                <p className="text-muted">
                  <code>{selectedProject.project_id}</code>
                </p>

                <hr />

                <Row className="mb-3">
                  <Col sm={6}>
                    <strong>Status:</strong> {getStatusBadge(selectedProject)}
                  </Col>
                  <Col sm={6}>
                    <strong>Stage:</strong> {getStageBadge(selectedProject.current_stage)}
                  </Col>
                </Row>

                <Row className="mb-3">
                  <Col>
                    <strong>Agent Summary:</strong>
                    <div className="d-flex gap-3 mt-2">
                      <span>
                        <Badge bg="success">{selectedProject.completed_agents}</Badge> Completed
                      </span>
                      <span>
                        <Badge bg="primary">{selectedProject.active_agents}</Badge> Running
                      </span>
                      <span>
                        <Badge bg="warning">{selectedProject.awaiting_input}</Badge> Awaiting Input
                      </span>
                      <span>
                        <Badge bg="danger">{selectedProject.failed_agents}</Badge> Failed
                      </span>
                    </div>
                  </Col>
                </Row>

                <Row className="mb-3">
                  <Col>
                    <strong>Overall Progress:</strong>
                    <ProgressBar className="mt-2">
                      <ProgressBar
                        variant="success"
                        now={(selectedProject.completed_agents / selectedProject.total_agents) * 100}
                        key={1}
                      />
                      <ProgressBar
                        variant="primary"
                        now={(selectedProject.active_agents / selectedProject.total_agents) * 100}
                        key={2}
                      />
                      <ProgressBar
                        variant="warning"
                        now={(selectedProject.awaiting_input / selectedProject.total_agents) * 100}
                        key={3}
                      />
                      <ProgressBar
                        variant="danger"
                        now={(selectedProject.failed_agents / selectedProject.total_agents) * 100}
                        key={4}
                      />
                    </ProgressBar>
                  </Col>
                </Row>

                {selectedProject.created_at && (
                  <Row className="mb-3">
                    <Col>
                      <strong>Created:</strong>{' '}
                      {new Date(selectedProject.created_at).toLocaleString()}
                    </Col>
                  </Row>
                )}

                <hr />

                <div className="d-flex gap-2">
                  <Button
                    variant="primary"
                    size="sm"
                    disabled={selectedProject.active_agents > 0}
                  >
                    ▶️ Continue Project
                  </Button>
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    href={`#timeline?request_id=${selectedProject.project_id}`}
                  >
                    📊 View Timeline
                  </Button>
                </div>
              </Card.Body>
            </Card>
          </Col>
        )}
      </Row>
    </Container>
  );
}

export default ProjectsDashboard;
