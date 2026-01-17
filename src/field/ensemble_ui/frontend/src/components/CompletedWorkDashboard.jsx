import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Badge, Spinner, ListGroup, Form } from 'react-bootstrap';
import ReactMarkdown from 'react-markdown';
import { getCompletedReports, getCompletedReportContent, getSpawnedTasksForReport } from '../services/api';
import SpawnFromReportModal from './SpawnFromReportModal';

/**
 * CompletedWorkDashboard - Browse and interact with completed reports/deliverables
 *
 * Features:
 * - List all completed reports from output/completed/
 * - View full content with markdown rendering
 * - Spawn new tasks from completed work
 * - Track lineage between tasks
 */
function CompletedWorkDashboard() {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportContent, setReportContent] = useState(null);
  const [spawnedTasks, setSpawnedTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showSpawnModal, setShowSpawnModal] = useState(false);
  const [error, setError] = useState(null);

  // Fetch reports on mount
  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const result = await getCompletedReports(100);
      setReports(result.reports || []);
      setError(null);
    } catch (err) {
      setError('Failed to load reports');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectReport = async (report) => {
    setSelectedReport(report);
    setContentLoading(true);
    try {
      const [contentResult, tasksResult] = await Promise.all([
        getCompletedReportContent(report.id),
        getSpawnedTasksForReport(report.id)
      ]);
      setReportContent(contentResult);
      setSpawnedTasks(tasksResult.spawned_tasks || []);
    } catch (err) {
      console.error('Failed to load report content:', err);
    } finally {
      setContentLoading(false);
    }
  };

  const handleSpawnComplete = (result) => {
    // Refresh spawned tasks for current report
    if (selectedReport) {
      getSpawnedTasksForReport(selectedReport.id).then(tasksResult => {
        setSpawnedTasks(tasksResult.spawned_tasks || []);
      });
    }
  };

  const filteredReports = reports.filter(report =>
    report.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    report.file_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (isoDate) => {
    return new Date(isoDate).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Container fluid className="py-4" style={{ backgroundColor: '#1a1d29', minHeight: 'calc(100vh - 80px)' }}>
      <Row className="mb-3">
        <Col>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h4 style={{ color: '#e4e6eb', margin: 0 }}>Completed Work</h4>
            <Button variant="outline-light" size="sm" onClick={fetchReports}>
              Refresh
            </Button>
          </div>
        </Col>
      </Row>

      {error && (
        <Row className="mb-3">
          <Col>
            <div style={{ padding: '12px', backgroundColor: '#ef4444', color: 'white', borderRadius: '4px' }}>
              {error}
            </div>
          </Col>
        </Row>
      )}

      <Row style={{ height: 'calc(100vh - 180px)' }}>
        {/* Left: Report List */}
        <Col md={4} style={{ height: '100%', overflowY: 'auto' }}>
          <Card bg="dark" text="light" style={{ height: '100%' }}>
            <Card.Header>
              <Form.Control
                type="text"
                placeholder="Search reports..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  backgroundColor: '#1a1d29',
                  color: '#e4e6eb',
                  border: '1px solid #3a3f52',
                  fontSize: '13px'
                }}
              />
            </Card.Header>
            <Card.Body style={{ padding: 0, overflowY: 'auto' }}>
              {loading ? (
                <div style={{ padding: '40px', textAlign: 'center' }}>
                  <Spinner animation="border" variant="light" />
                </div>
              ) : filteredReports.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>
                  {searchTerm ? 'No reports match your search' : 'No completed reports found'}
                </div>
              ) : (
                <ListGroup variant="flush">
                  {filteredReports.map(report => (
                    <ListGroup.Item
                      key={report.id}
                      action
                      active={selectedReport?.id === report.id}
                      onClick={() => handleSelectReport(report)}
                      style={{
                        backgroundColor: selectedReport?.id === report.id ? '#3a3f52' : '#242836',
                        borderColor: '#3a3f52',
                        color: '#e4e6eb',
                        cursor: 'pointer'
                      }}
                    >
                      <div style={{ fontWeight: 500, fontSize: '14px', marginBottom: '4px' }}>
                        {report.title || report.file_name}
                      </div>
                      <div style={{ fontSize: '11px', color: '#9ca3af', display: 'flex', gap: '12px' }}>
                        <span>{formatDate(report.created_at)}</span>
                        <span>{formatFileSize(report.size_bytes)}</span>
                      </div>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              )}
            </Card.Body>
            <Card.Footer style={{ fontSize: '12px', color: '#9ca3af' }}>
              {filteredReports.length} report{filteredReports.length !== 1 ? 's' : ''}
            </Card.Footer>
          </Card>
        </Col>

        {/* Right: Content Viewer */}
        <Col md={8} style={{ height: '100%', overflowY: 'auto' }}>
          <Card bg="dark" text="light" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {selectedReport ? (
              <>
                <Card.Header>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h6 style={{ margin: 0, marginBottom: '4px' }}>{selectedReport.title || selectedReport.file_name}</h6>
                      <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                        {formatDate(selectedReport.created_at)} | {selectedReport.file_path}
                      </span>
                    </div>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setShowSpawnModal(true)}
                      disabled={contentLoading}
                    >
                      Start New Task From This
                    </Button>
                  </div>
                </Card.Header>

                {/* Spawned Tasks Badge */}
                {spawnedTasks.length > 0 && (
                  <div style={{ padding: '8px 16px', backgroundColor: '#1a1d29', borderBottom: '1px solid #3a3f52' }}>
                    <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                      Follow-up tasks spawned from this report:
                    </span>
                    <div style={{ marginTop: '6px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {spawnedTasks.map(task => (
                        <Badge
                          key={task.request_id}
                          bg={task.status === 'completed' ? 'success' : task.status === 'running' ? 'warning' : 'secondary'}
                          style={{ fontSize: '11px' }}
                        >
                          {task.title || task.prompt_preview?.substring(0, 30) + '...'} ({task.status})
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <Card.Body style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
                  {contentLoading ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                      <Spinner animation="border" variant="light" />
                    </div>
                  ) : reportContent?.content ? (
                    <div className="markdown-content" style={{
                      fontSize: '14px',
                      lineHeight: '1.6',
                      color: '#e4e6eb'
                    }}>
                      <ReactMarkdown
                        components={{
                          h1: ({ children }) => <h1 style={{ color: '#e4e6eb', borderBottom: '1px solid #3a3f52', paddingBottom: '8px' }}>{children}</h1>,
                          h2: ({ children }) => <h2 style={{ color: '#e4e6eb', marginTop: '24px' }}>{children}</h2>,
                          h3: ({ children }) => <h3 style={{ color: '#e4e6eb', marginTop: '20px' }}>{children}</h3>,
                          // Handle pre elements (code blocks) separately
                          pre: ({ children }) => (
                            <pre style={{ backgroundColor: '#1a1d29', padding: '12px', borderRadius: '4px', overflow: 'auto', border: '1px solid #3a3f52', margin: '12px 0' }}>{children}</pre>
                          ),
                          // Only handle inline code styles - pre wraps code blocks
                          code: ({ inline, className, children }) => (
                            <code style={{
                              backgroundColor: inline ? '#3a3f52' : 'transparent',
                              padding: inline ? '2px 6px' : 0,
                              borderRadius: inline ? '4px' : 0,
                              fontSize: '13px'
                            }}>{children}</code>
                          ),
                          // Prevent p tags from wrapping pre elements
                          p: ({ children }) => {
                            // Check if children contains a pre element (code block)
                            const hasPreChild = React.Children.toArray(children).some(
                              child => child?.type?.name === 'pre' || child?.type === 'pre'
                            );
                            return hasPreChild ? <>{children}</> : <p style={{ marginBottom: '12px' }}>{children}</p>;
                          },
                          ul: ({ children }) => <ul style={{ marginLeft: '20px' }}>{children}</ul>,
                          ol: ({ children }) => <ol style={{ marginLeft: '20px' }}>{children}</ol>,
                          li: ({ children }) => <li style={{ marginBottom: '4px' }}>{children}</li>,
                          blockquote: ({ children }) => <blockquote style={{ borderLeft: '3px solid #3b82f6', paddingLeft: '12px', marginLeft: 0, color: '#9ca3af' }}>{children}</blockquote>,
                          a: ({ href, children }) => <a href={href} style={{ color: '#60a5fa' }} target="_blank" rel="noopener noreferrer">{children}</a>,
                          table: ({ children }) => <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '16px' }}>{children}</table>,
                          th: ({ children }) => <th style={{ border: '1px solid #3a3f52', padding: '8px', backgroundColor: '#1a1d29' }}>{children}</th>,
                          td: ({ children }) => <td style={{ border: '1px solid #3a3f52', padding: '8px' }}>{children}</td>,
                        }}
                      >
                        {reportContent.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', color: '#9ca3af', padding: '40px' }}>
                      Failed to load report content
                    </div>
                  )}
                </Card.Body>
              </>
            ) : (
              <Card.Body style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center', color: '#9ca3af' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>📄</div>
                  <div>Select a report from the list to view its content</div>
                </div>
              </Card.Body>
            )}
          </Card>
        </Col>
      </Row>

      {/* Spawn Modal */}
      <SpawnFromReportModal
        show={showSpawnModal}
        onHide={() => setShowSpawnModal(false)}
        report={selectedReport}
        onSpawnComplete={handleSpawnComplete}
      />
    </Container>
  );
}

export default CompletedWorkDashboard;
