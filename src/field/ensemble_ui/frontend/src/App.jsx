import React, { useState, useEffect, useRef } from 'react';
import ProblemInputForm from './components/ProblemInputForm';
import ChatInterface from './components/ChatInterface';
import FileDisplay from './components/FileDisplay';
import { generateSolution, connectWebSocket, getApplicationStatus } from './services/api';

function App() {
  const [problemDescription, setProblemDescription] = useState(null);
  const [budgetTier, setBudgetTier] = useState(null);
  const [agentStatus, setAgentStatus] = useState(null);
  const [appStatus, setAppStatus] = useState({ status: 'connecting', active_agents: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect WebSocket with auto-reconnect
    const connectWS = () => {
      wsRef.current = connectWebSocket(
        (data) => {
          setAgentStatus(data);
          setError(null); // Clear error on successful message
        },
        (error) => {
          console.log('WebSocket disconnected, will retry on next status poll');
          // Don't show error immediately - status polling will reconnect
          if (wsRef.current) {
            wsRef.current = null;
          }
        }
      );
    };

    connectWS();

    // Poll application status and reconnect WebSocket if needed
    const statusInterval = setInterval(async () => {
      try {
        const status = await getApplicationStatus();
        setAppStatus(status);

        // Reconnect WebSocket if it's disconnected
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          console.log('🔄 Reconnecting WebSocket...');
          connectWS();
        }
      } catch (err) {
        console.error('Failed to fetch app status:', err);
        setAppStatus({ status: 'error', active_agents: 0 });
      }
    }, 2000);

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      clearInterval(statusInterval);
    };
  }, []);

  const handleProblemSubmit = async (description, tier) => {
    setProblemDescription(description);
    setBudgetTier(tier);
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await generateSolution(description, tier);
      console.log('Solution generation started:', response);
      setResult(response);

      // Request status for this agent
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ agent_id: response.agent_id }));
      }
    } catch (err) {
      setError('Failed to start solution generation');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex flex-col">
      {/* Fixed Header */}
      <div className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-md border-b border-white/10 px-4 py-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-3xl">🤖</div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
                  Ensemble AI
                </h1>
                <p className="text-blue-300 text-xs">Collaborative Agent System</p>
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-white/10 backdrop-blur-md rounded-full border border-white/20">
                <div className={`w-2 h-2 rounded-full ${appStatus.status === 'running' ? 'bg-green-400 animate-pulse shadow-lg shadow-green-400/50' : 'bg-gray-400'}`}></div>
                <span className="font-medium text-white text-xs">{appStatus.status === 'running' ? 'Online' : 'Connecting'}</span>
              </div>
              <div className="px-3 py-1.5 bg-white/10 backdrop-blur-md rounded-full border border-white/20">
                <span className="font-medium text-white text-xs">{appStatus.active_agents} Agent{appStatus.active_agents !== 1 ? 's' : ''}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">

          {error && (
          <div className="mt-6 p-4 bg-red-500/20 border-l-4 border-red-500 text-red-200 rounded-lg shadow-lg backdrop-blur-sm">
            <div className="flex items-start">
              <span className="text-2xl mr-3">⚠️</span>
              <div>
                <p className="font-semibold text-white">Error</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </div>
        )}

        {isLoading && (
          <div className="mt-6 p-4 bg-blue-500/20 border-l-4 border-blue-400 text-blue-200 rounded-lg shadow-lg backdrop-blur-sm">
            <div className="flex items-center">
              <div className="animate-spin h-6 w-6 mr-3 border-3 border-blue-400 border-t-transparent rounded-full"></div>
              <span className="font-medium">Starting agent execution...</span>
            </div>
          </div>
        )}

        {result && (
          <div className="mt-6 p-6 bg-white/10 backdrop-blur-md rounded-xl shadow-2xl border border-white/20">
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-white">Execution Started</h2>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                budgetTier === 'full_firepower' ? 'bg-purple-500/30 text-purple-200 border border-purple-400/50' :
                budgetTier === 'economical' ? 'bg-green-500/30 text-green-200 border border-green-400/50' :
                'bg-blue-500/30 text-blue-200 border border-blue-400/50'
              }`}>
                {budgetTier === 'full_firepower' ? '🚀 Full Firepower' :
                 budgetTier === 'economical' ? '💰 Economical' :
                 '⚖️ Balanced'}
              </span>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold text-blue-300">Task</p>
                <p className="text-white">{problemDescription}</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-blue-300">Agent ID</p>
                <p className="text-sm font-mono text-gray-300">{result.agent_id}</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-blue-300">Status</p>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse shadow-lg shadow-yellow-400/50"></div>
                  <span className="text-sm capitalize text-white">{result.status || 'running'}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {agentStatus && agentStatus.agents && Object.keys(agentStatus.agents).length > 0 && (
          <div className="mt-6 p-6 bg-white/10 backdrop-blur-md rounded-xl shadow-2xl border border-white/20">
            <h2 className="text-xl font-bold mb-4 text-white">Active Agents</h2>
            {Object.entries(agentStatus.agents).map(([agentId, agentInfo]) => (
              <div key={agentId} className="mb-4 p-4 bg-white/5 rounded-lg border border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-white">{agentId}</h3>
                    {agentInfo.status === 'running' && (
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                      </div>
                    )}
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
                <div className="space-y-2 text-sm">
                  <div className="text-gray-300"><span className="font-semibold text-blue-300">Type:</span> {agentInfo.type}</div>
                  <div className="text-gray-300"><span className="font-semibold text-blue-300">Budget:</span> {agentInfo.budget_tier}</div>
                  {agentInfo.problem && <div className="text-gray-300"><span className="font-semibold text-blue-300">Task:</span> {agentInfo.problem}</div>}
                  {agentInfo.error && (
                    <div className="mt-3 p-3 bg-red-500/20 border-l-4 border-red-500 rounded backdrop-blur-sm">
                      <p className="font-semibold text-red-200">Error:</p>
                      <p className="text-red-300 mt-1">{agentInfo.error}</p>
                      {agentInfo.traceback && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-red-400 text-xs hover:text-red-300">Show traceback</summary>
                          <pre className="text-xs mt-2 overflow-auto max-h-48 bg-black/30 p-2 rounded text-red-200">
                            {agentInfo.traceback}
                          </pre>
                        </details>
                      )}
                    </div>
                  )}
                  {agentInfo.result && (
                    <div className="mt-3 p-3 bg-green-500/20 border-l-4 border-green-500 rounded backdrop-blur-sm">
                      <p className="font-semibold text-green-200">Result:</p>
                      <pre className="text-xs mt-1 overflow-auto max-h-48 text-green-100">
                        {JSON.stringify(agentInfo.result, null, 2)}
                      </pre>
                    </div>
                  )}
                  {agentInfo.logs && agentInfo.logs.length > 0 && (
                    <div className="mt-3 p-3 bg-blue-500/20 border-l-4 border-blue-500 rounded backdrop-blur-sm">
                      <p className="font-semibold text-blue-200">Execution Log:</p>
                      <div className="mt-2 space-y-1 max-h-64 overflow-y-auto">
                        {agentInfo.logs.map((log, idx) => (
                          <div key={idx} className="text-xs text-blue-100 font-mono">
                            {log}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Generated Files */}
                  {agentInfo.generated_files && agentInfo.generated_files.length > 0 && (
                    <FileDisplay files={agentInfo.generated_files} />
                  )}

                  {/* Chat Interface - show for running or completed agents */}
                  {(agentInfo.status === 'running' || agentInfo.status === 'completed') && (
                    <ChatInterface
                      agentId={agentId}
                      messages={agentInfo.messages || []}
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        </div>
      </div>

      {/* Fixed Input Panel - like AIM */}
      <div className="sticky bottom-0 z-50 bg-slate-900/95 backdrop-blur-md border-t border-white/10 px-4 py-4">
        <div className="max-w-6xl mx-auto">
          <ProblemInputForm onProblemSubmit={handleProblemSubmit} />
        </div>
      </div>
    </div>
  );
}

export default App;