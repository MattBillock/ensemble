import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ChatInterface from './ChatInterface';

function AgentStatusPane({ agentStatus }) {
  const agents = agentStatus?.agents || {};
  const agentEntries = Object.entries(agents);

  // Get the most recent active/running agent, or the first one
  const primaryAgent = agentEntries.find(([_, info]) => info.status === 'running') || agentEntries[0];

  if (!primaryAgent) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="text-4xl mb-2">💬</div>
          <p>No active agents</p>
          <p className="text-xs mt-1">Submit a task below to get started</p>
        </div>
      </div>
    );
  }

  const [agentId, agentInfo] = primaryAgent;

  const formatResult = (result) => {
    if (!result) return null;

    // If it's a conversational response
    if (result.response_type === 'conversational') {
      return (
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {result.message || ''}
          </ReactMarkdown>
        </div>
      );
    }

    // If it's a structured response with a message
    if (result.message) {
      return (
        <div className="space-y-3">
          {result.summary && (
            <div>
              <p className="text-xs font-semibold text-blue-300">Summary</p>
              <p className="text-sm text-gray-200">{result.summary}</p>
            </div>
          )}
          <div>
            <p className="text-xs font-semibold text-blue-300">Response</p>
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {result.message}
              </ReactMarkdown>
            </div>
          </div>
          {result.user_question && (
            <div className="mt-3 p-3 bg-yellow-500/20 border-l-4 border-yellow-500 rounded">
              <p className="text-xs font-semibold text-yellow-300">Agent Question</p>
              <div className="prose prose-invert prose-sm max-w-none mt-1">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {result.user_question}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      );
    }

    // Fallback to JSON display
    return (
      <pre className="text-xs overflow-auto">
        {JSON.stringify(result, null, 2)}
      </pre>
    );
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex-shrink-0 border-b border-white/10 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-white">{agentId}</h3>
            <p className="text-xs text-gray-400">{agentInfo.type}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1 ${
            agentInfo.status === 'completed' ? 'bg-green-500/30 text-green-200 border border-green-400/50' :
            agentInfo.status === 'error' ? 'bg-red-500/30 text-red-200 border border-red-400/50' :
            agentInfo.status === 'running' ? 'bg-blue-500/30 text-blue-200 border border-blue-400/50' :
            'bg-yellow-500/30 text-yellow-200 border border-yellow-400/50'
          }`}>
            {agentInfo.status === 'running' && '⚙️'}
            {agentInfo.status === 'completed' && '✅'}
            {agentInfo.status === 'error' && '❌'}
            {agentInfo.status}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {agentInfo.problem && (
          <div>
            <p className="text-xs font-semibold text-blue-300 mb-1">Task</p>
            <p className="text-sm text-gray-200">{agentInfo.problem}</p>
          </div>
        )}

        {agentInfo.result && (
          <div>
            <p className="text-xs font-semibold text-blue-300 mb-2">Result</p>
            {formatResult(agentInfo.result)}
          </div>
        )}

        {agentInfo.error && (
          <div className="p-3 bg-red-500/20 border-l-4 border-red-500 rounded">
            <p className="font-semibold text-red-200">Error</p>
            <p className="text-red-300 text-sm mt-1">{agentInfo.error}</p>
          </div>
        )}

        {agentInfo.logs && agentInfo.logs.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-blue-300 mb-2">Activity Log</p>
            <div className="space-y-1">
              {agentInfo.logs.slice(-5).map((log, idx) => (
                <div key={idx} className="text-xs text-gray-300 font-mono">
                  {log}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {(agentInfo.status === 'running' || agentInfo.status === 'completed') && (
        <div className="flex-shrink-0 border-t border-white/10">
          <ChatInterface
            agentId={agentId}
            messages={agentInfo.messages || []}
          />
        </div>
      )}
    </div>
  );
}

export default AgentStatusPane;
