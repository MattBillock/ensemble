import React from 'react';

function AgentSummaryPane({ agentStatus }) {
  const agents = agentStatus?.agents || {};
  const agentEntries = Object.entries(agents);

  const runningAgents = agentEntries.filter(([_, info]) => info.status === 'running');
  const completedAgents = agentEntries.filter(([_, info]) => info.status === 'completed');
  const errorAgents = agentEntries.filter(([_, info]) => info.status === 'error');

  return (
    <div className="h-full flex flex-col">
      <div className="flex-shrink-0 border-b border-white/10 p-4">
        <h3 className="font-semibold text-white">Agent Summary</h3>
        <p className="text-xs text-gray-400">Active tasks and execution status</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Stats Overview */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-blue-500/20 rounded-lg p-3 border border-blue-400/30">
            <div className="text-2xl font-bold text-blue-200">{runningAgents.length}</div>
            <div className="text-xs text-blue-300">Running</div>
          </div>
          <div className="bg-green-500/20 rounded-lg p-3 border border-green-400/30">
            <div className="text-2xl font-bold text-green-200">{completedAgents.length}</div>
            <div className="text-xs text-green-300">Completed</div>
          </div>
          <div className="bg-red-500/20 rounded-lg p-3 border border-red-400/30">
            <div className="text-2xl font-bold text-red-200">{errorAgents.length}</div>
            <div className="text-xs text-red-300">Errors</div>
          </div>
        </div>

        {/* Agent List */}
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-400 uppercase">All Agents</p>
          {agentEntries.length === 0 ? (
            <p className="text-sm text-gray-500 italic">No agents yet</p>
          ) : (
            agentEntries.map(([agentId, agentInfo]) => (
              <div
                key={agentId}
                className="bg-white/5 rounded-lg p-3 border border-white/10 hover:bg-white/10 transition-colors cursor-pointer"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white">{agentId}</span>
                    {agentInfo.status === 'running' && (
                      <div className="flex gap-1">
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse"></div>
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                      </div>
                    )}
                  </div>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                    agentInfo.status === 'completed' ? 'bg-green-500/30 text-green-200' :
                    agentInfo.status === 'error' ? 'bg-red-500/30 text-red-200' :
                    agentInfo.status === 'running' ? 'bg-blue-500/30 text-blue-200' :
                    'bg-yellow-500/30 text-yellow-200'
                  }`}>
                    {agentInfo.status === 'running' && '⚙️'}
                    {agentInfo.status === 'completed' && '✅'}
                    {agentInfo.status === 'error' && '❌'}
                  </span>
                </div>
                <div className="text-xs text-gray-400">
                  {agentInfo.type} • {agentInfo.budget_tier}
                </div>
                {agentInfo.problem && (
                  <div className="text-xs text-gray-300 mt-1 line-clamp-2">
                    {agentInfo.problem}
                  </div>
                )}
                {agentInfo.generated_files && agentInfo.generated_files.length > 0 && (
                  <div className="text-xs text-purple-300 mt-1">
                    📁 {agentInfo.generated_files.length} file(s) generated
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default AgentSummaryPane;
