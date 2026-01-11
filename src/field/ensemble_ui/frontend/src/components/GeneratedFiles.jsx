import React, { useState } from 'react';
import { Card, Badge, Collapse, Button } from 'react-bootstrap';

const GeneratedFiles = ({ files }) => {
  const [expandedFiles, setExpandedFiles] = useState(new Set());

  if (!files || files.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af', fontSize: '12px' }}>
        No files generated yet. Files created by agents will appear here.
      </div>
    );
  }

  const toggleFile = (filePath) => {
    const newExpanded = new Set(expandedFiles);
    if (newExpanded.has(filePath)) {
      newExpanded.delete(filePath);
    } else {
      newExpanded.add(filePath);
    }
    setExpandedFiles(newExpanded);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (fileType) => {
    const icons = {
      'markdown': '📝',
      'python': '🐍',
      'javascript': '📜',
      'typescript': '📘',
      'typescript-react': '⚛️',
      'json': '📋',
      'yaml': '⚙️',
      'text': '📄',
      'unknown': '📄'
    };
    return icons[fileType] || '📄';
  };

  const getFileTypeColor = (fileType) => {
    const colors = {
      'markdown': 'primary',
      'python': 'success',
      'javascript': 'warning',
      'typescript': 'info',
      'typescript-react': 'info',
      'json': 'secondary',
      'yaml': 'secondary',
      'text': 'secondary',
      'unknown': 'secondary'
    };
    return colors[fileType] || 'secondary';
  };

  return (
    <div>
      {files.map((file, index) => {
        const isExpanded = expandedFiles.has(file.file_path);
        const fileName = file.file_path.split('/').pop();
        const filePath = file.file_path.split('/').slice(0, -1).join('/');

        return (
          <div
            key={`${file.file_path}-${index}`}
            style={{
              marginBottom: '8px',
              backgroundColor: '#1a1d29',
              borderRadius: '4px',
              border: '1px solid #3a3f52',
              overflow: 'hidden'
            }}
          >
            {/* File Header */}
            <div
              onClick={() => toggleFile(file.file_path)}
              style={{
                padding: '10px 12px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#242836'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}>
                <span style={{ fontSize: '16px' }}>{getFileIcon(file.file_type)}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '12px', fontWeight: '500', color: '#e4e6eb', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {fileName}
                  </div>
                  <div style={{ fontSize: '10px', color: '#6b7280', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {filePath}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                <Badge bg={getFileTypeColor(file.file_type)} style={{ fontSize: '9px' }}>
                  {file.file_type}
                </Badge>
                <span style={{ fontSize: '10px', color: '#9ca3af' }}>
                  {formatFileSize(file.file_size)}
                </span>
                <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                  {isExpanded ? '▼' : '▶'}
                </span>
              </div>
            </div>

            {/* File Preview */}
            <Collapse in={isExpanded}>
              <div>
                <div style={{
                  borderTop: '1px solid #3a3f52',
                  padding: '12px',
                  backgroundColor: '#0d1117'
                }}>
                  {/* Metadata */}
                  <div style={{ marginBottom: '8px', paddingBottom: '8px', borderBottom: '1px solid #3a3f52' }}>
                    <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '4px' }}>
                      <strong>Agent:</strong> {file.agent_name} ({file.agent_id})
                    </div>
                    <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '4px' }}>
                      <strong>Created:</strong> {new Date(file.timestamp).toLocaleString()}
                    </div>
                    <div style={{ fontSize: '10px', color: '#9ca3af' }}>
                      <strong>Request ID:</strong> {file.request_id}
                    </div>
                  </div>

                  {/* Preview */}
                  {file.preview && (
                    <div>
                      <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '6px' }}>
                        <strong>Preview:</strong>
                      </div>
                      <pre style={{
                        fontSize: '11px',
                        color: '#e4e6eb',
                        backgroundColor: '#161b22',
                        padding: '10px',
                        borderRadius: '4px',
                        border: '1px solid #30363d',
                        maxHeight: '300px',
                        overflowY: 'auto',
                        margin: 0,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word'
                      }}>
                        {file.preview}
                      </pre>
                      {file.preview.length >= 500 && (
                        <div style={{ fontSize: '9px', color: '#6b7280', marginTop: '4px', fontStyle: 'italic' }}>
                          ... preview truncated at 500 characters
                        </div>
                      )}
                    </div>
                  )}

                  {/* Full path for copying */}
                  <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #3a3f52' }}>
                    <div style={{ fontSize: '9px', color: '#6b7280', fontFamily: 'monospace' }}>
                      {file.file_path}
                    </div>
                  </div>
                </div>
              </div>
            </Collapse>
          </div>
        );
      })}
    </div>
  );
};

export default GeneratedFiles;
