import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  agentStatus: null,
  appStatus: { status: 'connecting', active_agents: 0 },
  isLoading: false,
  error: null,
  result: null,
};

export const agentSlice = createSlice({
  name: 'agent',
  initialState,
  reducers: {
    setAgentStatus: (state, action) => {
      state.agentStatus = action.payload;
    },
    setAppStatus: (state, action) => {
      state.appStatus = action.payload;
    },
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    setResult: (state, action) => {
      state.result = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setAgentStatus,
  setAppStatus,
  setLoading,
  setError,
  setResult,
  clearError,
} = agentSlice.actions;

export default agentSlice.reducer;
