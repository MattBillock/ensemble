import React, { useState, useEffect, useRef } from 'react';
import ProblemInputForm from './components/ProblemInputForm';
import AgentStatusPane from './components/AgentStatusPane';
import AgentSummaryPane from './components/AgentSummaryPane';
import FileViewerPane from './components/FileViewerPane';
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
    // Listen for agent resume events from ChatInterface
    const handleAgentResume = (event) => {
      const { task, budgetTier } = event.detail;
      handleProblemSubmit(task, budgetTier);
    };

    window.addEventListener('spawn-agent-task', handleAgentResume);

    // Connect WebSocket with auto-reconnect
    const connectWS = () => {
      wsRef.current = connectWebSocket(
        (data) => {
          setAgentStatus(data);
          setError(null);
        },
        (error) => {
          console.log('WebSocket disconnected, will retry on next status poll');
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
      window.removeEventListener('spawn-agent-task', handleAgentResume);
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
    <div className="h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex flex-col overflow-hidden">
      {/* Fixed Header */}
      <div className="flex-shrink-0 bg-slate-900/95 backdrop-blur-md border-b border-white/10 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl">🤖</div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
                Ensemble AI
              </h1>
              <p className="text-blue-300 text-xs">Collaborative Multi-Agent System</p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-sm">
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

      {/* 4-Pane Layout (2x2 Grid) */}
      <div className="flex-1 grid grid-cols-2 gap-0 overflow-hidden">
        {/* Top-Left: Agent Status & Conversation */}
        <div className="border-r border-b border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden">
          <AgentStatusPane agentStatus={agentStatus} />
        </div>

        {/* Top-Right: Agent Summary */}
        <div className="border-b border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden">
          <AgentSummaryPane agentStatus={agentStatus} />
        </div>

        {/* Bottom-Left: Input Area */}
        <div className="border-r border-white/10 bg-white/5 backdrop-blur-sm flex flex-col overflow-hidden">
          <div className="flex-shrink-0 border-b border-white/10 p-4">
            <h3 className="font-semibold text-white">New Task</h3>
            <p className="text-xs text-gray-400">Describe what you want the agents to build</p>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {error && (
              <div className="mb-4 p-3 bg-red-500/20 border-l-4 border-red-500 text-red-200 rounded-lg">
                <div className="flex items-start">
                  <span className="text-xl mr-2">⚠️</span>
                  <div>
                    <p className="font-semibold text-white">Error</p>
                    <p className="text-sm">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {isLoading && (
              <div className="mb-4 p-3 bg-blue-500/20 border-l-4 border-blue-400 text-blue-200 rounded-lg">
                <div className="flex items-center">
                  <div className="animate-spin h-5 w-5 mr-2 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                  <span className="font-medium">Starting agent execution...</span>
                </div>
              </div>
            )}

            {result && (
              <div className="mb-4 p-4 bg-green-500/20 border-l-4 border-green-400 rounded-lg">
                <p className="text-sm font-semibold text-green-200 mb-1">✅ Agent Launched</p>
                <p className="text-xs text-green-300">Agent ID: {result.agent_id}</p>
                <p className="text-xs text-green-300">Status: {result.status}</p>
              </div>
            )}
          </div>
          <div className="flex-shrink-0 border-t border-white/10 p-4">
            <ProblemInputForm onProblemSubmit={handleProblemSubmit} />
          </div>
        </div>

        {/* Bottom-Right: File Viewer */}
        <div className="bg-white/5 backdrop-blur-sm overflow-hidden">
          <FileViewerPane agentStatus={agentStatus} />
        </div>
      </div>
    </div>
  );
}

export default App;
