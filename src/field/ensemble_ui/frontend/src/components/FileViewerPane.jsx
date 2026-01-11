import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function FileViewerPane({ agentStatus }) {
  const [selectedFile, setSelectedFile] = useState(null);

  const agents = agentStatus?.agents || {};

  // Collect all generated files from all agents
  const allFiles = [];
  Object.entries(agents).forEach(([agentId, agentInfo]) => {
    if (agentInfo.generated_files && agentInfo.generated_files.length > 0) {
      agentInfo.generated_files.forEach(file => {
        allFiles.push({
          ...file,
          agentId,
          agentType: agentInfo.type
        });
      });
    }
  });

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const isMarkdown = (filename) => {
    return filename.endsWith('.md') || filename.endsWith('.markdown');
  };

  const isCode = (filename) => {
    const codeExtensions = ['.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.css', '.html', '.json', '.yaml', '.yml'];
    return codeExtensions.some(ext => filename.endsWith(ext));
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex-shrink-0 border-b border-white/10 p-4">
        <h3 className="font-semibold text-white">Generated Files</h3>
        <p className="text-xs text-gray-400">
          {allFiles.length} file{allFiles.length !== 1 ? 's' : ''} from {Object.keys(agents).length} agent{Object.keys(agents).length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="flex-1 flex">
        {/* File List Sidebar */}
        <div className="w-64 border-r border-white/10 overflow-y-auto">
          {allFiles.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              <div className="text-3xl mb-2">📂</div>
              <p>No files generated yet</p>
            </div>
          ) : (
            <div className="divide-y divide-white/10">
              {allFiles.map((file, idx) => (
                <div
                  key={idx}
                  onClick={() => setSelectedFile(file)}
                  className={`p-3 cursor-pointer transition-colors ${
                    selectedFile === file ? 'bg-white/10' : 'hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-lg flex-shrink-0">
                      {isMarkdown(file.filename) ? '📝' :
                       isCode(file.filename) ? '💻' :
                       '📄'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {file.filename}
                      </p>
                      <p className="text-xs text-gray-400 truncate">
                        {file.agentId}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* File Content Viewer */}
        <div className="flex-1 overflow-y-auto">
          {!selectedFile ? (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <div className="text-4xl mb-2">👈</div>
                <p>Select a file to view</p>
              </div>
            </div>
          ) : (
            <div className="p-6">
              <div className="mb-4">
                <h4 className="text-lg font-semibold text-white mb-1">
                  {selectedFile.filename}
                </h4>
                <p className="text-sm text-gray-400">
                  {selectedFile.path}
                </p>
                <div className="flex gap-3 mt-2 text-xs text-gray-500">
                  <span>Size: {formatFileSize(selectedFile.size)}</span>
                  <span>•</span>
                  <span>Agent: {selectedFile.agentId}</span>
                </div>
              </div>

              <div className="border-t border-white/10 pt-4">
                {isMarkdown(selectedFile.filename) ? (
                  <div className="prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {selectedFile.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <pre className="bg-black/30 rounded-lg p-4 overflow-x-auto text-xs text-gray-200">
                    {selectedFile.content}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default FileViewerPane;
