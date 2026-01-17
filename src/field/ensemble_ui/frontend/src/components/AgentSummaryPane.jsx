import React from 'react';
import { generateWhimsicalName, getAgentEmoji } from '../utils/whimsicalNames';
import {
  formatDuration,
  formatCost,
  getCostColorClass,
  formatModelName,
  getModelColorClass,
  formatTokens
} from '../utils/metricFormatters';

function AgentSummaryPane({ agentStatus }) {
  const agents = agentStatus?.agents || {};
  const agentEntries = Object.entries(agents);

  const runningAgents = agentEntries.filter(([_, info]) => info.status === 'running');
  const completedAgents = agentEntries.filter(([_, info]) => info.status === 'completed');
  const errorAgents = agentEntries.filter(([_, info]) => info.status === 'error');

  // Calculate total cost across all agents
  const totalCost = agentEntries.reduce((sum, [_, info]) => {
    return sum + (info.cost_estimate || 0);
  }, 0);

  // Calculate total tokens
  const totalTokens = agentEntries.reduce((sum, [_, info]) => {
    return sum + (info.input_tokens || 0) + (info.output_tokens || 0);
  }, 0);

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

        {/* Cost Summary */}
        {(totalCost > 0 || totalTokens > 0) && (
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-yellow-500/20 rounded-lg p-3 border border-yellow-400/30">
              <div className={`text-xl font-bold ${getCostColorClass(totalCost)}`}>{formatCost(totalCost)}</div>
              <div className="text-xs text-yellow-300">Total Cost</div>
            </div>
            <div className="bg-purple-500/20 rounded-lg p-3 border border-purple-400/30">
              <div className="text-xl font-bold text-purple-200">{formatTokens(totalTokens)}</div>
              <div className="text-xs text-purple-300">Total Tokens</div>
            </div>
          </div>
        )}

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
                    <span className="text-lg">{getAgentEmoji(agentInfo.type)}</span>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-white">{generateWhimsicalName(agentId)}</span>
                      <span className="text-xs text-gray-500">{agentId}</span>
                    </div>
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
                    agentInfo.status === 'awaiting_user_input' ? 'bg-yellow-500/30 text-yellow-200' :
                    agentInfo.status === 'superseded' ? 'bg-gray-500/30 text-gray-300' :
                    agentInfo.status === 'forever_failed' ? 'bg-red-700/30 text-red-300' :
                    'bg-yellow-500/30 text-yellow-200'
                  }`}>
                    {agentInfo.status === 'running' && '⚙️ running'}
                    {agentInfo.status === 'completed' && '✅ completed'}
                    {agentInfo.status === 'error' && '❌ error'}
                    {agentInfo.status === 'awaiting_user_input' && '❓ waiting'}
                    {agentInfo.status === 'superseded' && '➡️ superseded'}
                    {agentInfo.status === 'forever_failed' && '☠️ failed'}
                    {!['running', 'completed', 'error', 'awaiting_user_input', 'superseded', 'forever_failed'].includes(agentInfo.status) && agentInfo.status}
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
                {agentInfo.status === 'completed' && agentInfo.summary && (
                  <div className="text-xs text-green-300 mt-2 border-l-2 border-green-500/50 pl-2">
                    <span className="font-semibold">Summary: </span>
                    {agentInfo.summary.length > 200
                      ? `${agentInfo.summary.substring(0, 200)}...`
                      : agentInfo.summary}
                  </div>
                )}
                {agentInfo.status === 'completed' && agentInfo.deliverables && agentInfo.deliverables.length > 0 && (
                  <div className="text-xs text-blue-300 mt-1">
                    📦 {agentInfo.deliverables.length} deliverable(s)
                  </div>
                )}
                {agentInfo.generated_files && agentInfo.generated_files.length > 0 && (
                  <div className="text-xs text-purple-300 mt-1">
                    📁 {agentInfo.generated_files.length} file(s) generated
                  </div>
                )}
                {/* Execution Metrics */}
                {(agentInfo.duration_ms || agentInfo.cost_estimate || agentInfo.model_used) && (
                  <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t border-white/10">
                    {agentInfo.duration_ms && (
                      <span className="px-2 py-0.5 rounded text-xs bg-gray-500/30 text-gray-200">
                        ⏱️ {formatDuration(agentInfo.duration_ms)}
                      </span>
                    )}
                    {agentInfo.model_used && (
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getModelColorClass(agentInfo.model_used)}`}>
                        {formatModelName(agentInfo.model_used)}
                      </span>
                    )}
                    {agentInfo.cost_estimate !== undefined && agentInfo.cost_estimate !== null && (
                      <span className={`px-2 py-0.5 rounded text-xs bg-gray-500/30 ${getCostColorClass(agentInfo.cost_estimate)}`}>
                        💰 {formatCost(agentInfo.cost_estimate)}
                      </span>
                    )}
                    {(agentInfo.input_tokens || agentInfo.output_tokens) && (
                      <span className="px-2 py-0.5 rounded text-xs bg-gray-500/30 text-gray-300">
                        📊 {formatTokens((agentInfo.input_tokens || 0) + (agentInfo.output_tokens || 0))} tokens
                      </span>
                    )}
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
