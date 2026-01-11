import React, { useState } from 'react';

function FileDisplay({ files = [] }) {
  const [expandedFiles, setExpandedFiles] = useState({});

  if (!files || files.length === 0) {
    return null;
  }

  const toggleFile = (index) => {
    setExpandedFiles(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="mt-3 p-3 bg-purple-500/20 border-l-4 border-purple-500 rounded backdrop-blur-sm">
      <p className="font-semibold text-purple-200 mb-2">📁 Generated Files ({files.length})</p>
      <div className="space-y-2">
        {files.map((file, idx) => (
          <div key={idx} className="bg-white/5 rounded border border-white/10">
            <div
              className="flex items-center justify-between p-2 cursor-pointer hover:bg-white/10 transition-colors"
              onClick={() => toggleFile(idx)}
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">{expandedFiles[idx] ? '📂' : '📄'}</span>
                <div>
                  <p className="text-sm font-mono text-purple-100">{file.filename}</p>
                  <p className="text-xs text-purple-300">{file.path}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-purple-300">{formatFileSize(file.size)}</span>
                <span className="text-purple-300">{expandedFiles[idx] ? '▼' : '▶'}</span>
              </div>
            </div>

            {expandedFiles[idx] && (
              <div className="border-t border-white/10 p-3">
                <pre className="text-xs text-purple-100 overflow-x-auto max-h-96 bg-black/30 p-3 rounded">
                  {file.content}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default FileDisplay;
