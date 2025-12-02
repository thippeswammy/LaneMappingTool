import { create } from 'zustand';
import axios from 'axios';

const API_URL = ''; // Use relative paths

export const useStore = create((set, get) => ({
  // State
  nodes: [],
  edges: [],
  fileNames: [],
  loading: true,
  status: 'Initializing...',
  mode: 'select', // select, draw, smooth, connect, remove_between, reverse_path, zoom

  // Selections & temporary data
  selectedNodeIds: [],
  operationStartNodeId: null,
  smoothingPreview: null,
  smoothStartNodeId: null,
  smoothEndNodeId: null,
  smoothness: 1.0,
  weight: 1,
  pointSize: 2, // Default point size
  plotWidth: 100, // Default plot width in %
  drawPoints: [], // Temporary points for Draw mode

  // Actions
  setSmoothness: (smoothness) => {
    set({ smoothness });
    const { smoothStartNodeId, smoothEndNodeId } = get();
    if (smoothStartNodeId && smoothEndNodeId) {
      get().previewSmooth(smoothStartNodeId, smoothEndNodeId);
    }
  },
  setWeight: (weight) => {
    set({ weight });
    const { smoothStartNodeId, smoothEndNodeId } = get();
    if (smoothStartNodeId && smoothEndNodeId) {
      get().previewSmooth(smoothStartNodeId, smoothEndNodeId);
    }
  },
  setPointSize: (pointSize) => set({ pointSize }),
  setPlotWidth: (width) => set({ plotWidth: width }),

  fetchData: async () => {
    try {
      set({ loading: true, status: 'Loading data...' });
      const response = await axios.get(`${API_URL}/api/data`);
      const { nodes, edges, file_names } = response.data;
      set({
        nodes: nodes || [],
        edges: edges || [],
        fileNames: file_names || [],
        loading: false,
        status: 'Ready'
      });
    } catch (error) {
      console.error("Error fetching data:", error);
      set({ loading: false, status: 'Error fetching data.' });
    }
  },

  performOperation: async (operation, params = {}) => {
    try {
      set({ status: `Executing: ${operation}...` });
      const response = await axios.post(`${API_URL}/api/operation`, { operation, params });
      const { nodes, edges } = response.data;
      set({
        nodes,
        edges,
        status: `${operation} successful.`,
        selectedNodeIds: [],
        operationStartNodeId: null,
      });
      if (['remove_between', 'reverse_path', 'add_edge'].includes(operation)) {
        set({ mode: 'select' });
      }
    } catch (error) {
      console.error(`Error performing operation ${operation}:`, error);
      set({ status: `Error: ${operation} failed.` });
    }
  },

  setMode: (mode) => {
    set({
      mode,
      status: `Mode: ${mode}`,
      selectedNodeIds: [],
      operationStartNodeId: null,
      smoothingPreview: null,
      smoothStartNodeId: null,
      smoothEndNodeId: null,
      drawPoints: [],
    });
  },

  setSelectedNodeIds: (ids) => {
    set({ selectedNodeIds: ids });
  },

  addDrawPoint: (point) => {
    set(state => ({
      drawPoints: [...state.drawPoints, point]
    }));
  },

  finalizeDraw: async () => {
    const { drawPoints, performOperation } = get();
    if (drawPoints.length === 0) return;

    await performOperation('batch_add_nodes', {
      points: drawPoints,
      lane_id: 0,
      connect_to_start_id: null
    });

    set({ drawPoints: [] });
  },

  cancelDraw: () => {
    set({ drawPoints: [], status: 'Draw canceled.' });
  },

  handleNodeClick: (nodeId) => {
    const { mode, operationStartNodeId, performOperation } = get();

    if (mode === 'select') {
      set(state => ({
        selectedNodeIds: state.selectedNodeIds.includes(nodeId)
          ? []
          : [nodeId]
      }));
    } else if (['smooth', 'remove_between', 'reverse_path', 'connect'].includes(mode)) {
      if (!operationStartNodeId) {
        set({ operationStartNodeId: nodeId, status: `Start node ${nodeId} selected.` });
      } else {
        if (operationStartNodeId === nodeId) return;

        const startId = operationStartNodeId;
        const endId = nodeId;

        set({ operationStartNodeId: null });

        if (mode === 'smooth') {
          set({ smoothStartNodeId: startId, smoothEndNodeId: endId });
          get().previewSmooth(startId, endId);
        } else if (mode === 'connect') {
          performOperation('add_edge', { from_id: startId, to_id: endId });
        } else if (mode === 'remove_between') {
          performOperation('remove_between', { start_id: startId, end_id: endId });
        } else if (mode === 'reverse_path') {
          performOperation('reverse_path', { start_id: startId, end_id: endId });
        }
      }
    }
  },

  previewSmooth: async (startId, endId) => {
    const { smoothness, weight } = get();
    try {
      set({ status: 'Generating smooth preview...' });
      const response = await axios.post(`${API_URL}/api/smooth`, {
        start_id: startId,
        end_id: endId,
        smoothness: smoothness,
        weight: weight,
      });
      set({
        smoothingPreview: response.data.updated_nodes,
        status: 'Preview generated. Click "Apply Smooth" to confirm.'
      });
    } catch (error) {
      console.error("Error generating smooth preview:", error);
      const errorMessage = error.response?.data?.message || 'Error generating preview.';
      set({ status: `Error: ${errorMessage}`, smoothingPreview: null });
    }
  },

  applySmooth: () => {
    const { smoothingPreview, nodes } = get();
    if (!smoothingPreview) return;

    const updatedNodes = nodes.slice();
    const nodeMap = new Map(updatedNodes.map(n => [n[0], n]));

    smoothingPreview.forEach(previewNode => {
      const existingNode = nodeMap.get(previewNode[0]);
      if (existingNode) {
        Object.assign(existingNode, previewNode);
      }
    });

    get().performOperation('apply_updates', { nodes: updatedNodes, edges: get().edges });
    set({ smoothingPreview: null, mode: 'select', smoothStartNodeId: null, smoothEndNodeId: null });
  },

  saveData: async () => {
    const { nodes, edges } = get();
    try {
      set({ status: 'Saving...' });
      await axios.post(`${API_URL}/api/save`, { nodes, edges });
      set({ status: 'Save successful.' });
    } catch (error) {
      console.error("Error saving data:", error);
      set({ status: 'Save failed.' });
    }
  }
}));

// Expose store for debugging
window.store = useStore;