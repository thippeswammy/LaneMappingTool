import { create } from 'zustand';
import axios from 'axios';

const API_URL = ''; // Use relative paths

export const useStore = create((set, get) => ({
  // State
  nodes: [],
  edges: [],
  fileNames: [],
  availableFiles: { raw_files: [], saved_files: [], raw_path: '', saved_path: '', subdirs: [], current_subdir: 'TEMP1', current_saved_subdir: '' },
  currentRawDir: 'TEMP1',
  currentSavedDir: '',
  loading: true,
  status: 'Initializing...',
  mode: 'select', // select, draw, smooth, connect, remove_between, reverse_path, zoom, brush_select, box_select
  isFileLoaderOpen: false,

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

  fetchFiles: async (subdir = null, savedSubdir = null) => {
    try {
      const params = {};
      if (subdir) params.subdir = subdir;
      if (savedSubdir) params.saved_subdir = savedSubdir;

      const response = await axios.get(`${API_URL}/api/files`, { params });
      set({ availableFiles: response.data });
      if (subdir) {
        set({ currentRawDir: subdir });
      }
      if (savedSubdir) {
        set({ currentSavedDir: savedSubdir });
      }
    } catch (error) {
      console.error("Error fetching files:", error);
    }
  },

  loadData: async (rawFiles, savedNodesFile, savedEdgesFile, rawDataDir, savedGraphDir) => {
    try {
      set({ loading: true, status: 'Loading selected files...' });
      const response = await axios.post(`${API_URL}/api/load`, {
        raw_files: rawFiles,
        saved_nodes_file: savedNodesFile,
        saved_edges_file: savedEdgesFile,
        raw_data_dir: rawDataDir,
        saved_graph_dir: savedGraphDir
      });
      const { nodes, edges, file_names } = response.data;
      set({
        nodes: nodes || [],
        edges: edges || [],
        fileNames: file_names || [],
        loading: false,
        status: 'Data loaded successfully.'
      });
    } catch (error) {
      console.error("Error loading data:", error);
      set({ loading: false, status: 'Error loading data.' });
    }
  },

  unloadData: async (filename) => {
    try {
      set({ loading: true, status: `Unloading ${filename}...` });
      const response = await axios.post(`${API_URL}/api/unload`, { filename });
      const { nodes, edges, file_names } = response.data;
      set({
        nodes: nodes || [],
        edges: edges || [],
        fileNames: file_names || [],
        loading: false,
        status: `Unloaded ${filename}.`
      });
    } catch (error) {
      console.error("Error unloading data:", error);
      set({ loading: false, status: 'Error unloading data.' });
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
      if (['remove_between', 'reverse_path', 'add_edge', 'copy_points', 'delete_points'].includes(operation)) {
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

  setFileLoaderOpen: (isOpen) => {
    set({ isFileLoaderOpen: isOpen });
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