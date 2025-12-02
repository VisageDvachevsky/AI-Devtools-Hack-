import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_BASE = `${API_URL}/api/v1`;

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const executeAgent = async (agentName: string, inputData: any, config?: any) => {
  const response = await client.post('/agents/execute', {
    agent_name: agentName,
    input_data: inputData,
    config: config || {},
  });
  return response.data;
};

export const listAgents = async () => {
  const response = await client.get('/agents/list');
  return response.data;
};

export const callMCPTool = async (toolName: string, parameters: any) => {
  const response = await client.post('/mcp/call', {
    tool_name: toolName,
    parameters: parameters,
  });
  return response.data;
};

export const listMCPTools = async () => {
  const response = await client.get('/mcp/tools');
  return response.data;
};
