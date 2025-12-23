import { create } from 'zustand';
import axios from 'axios';

const API_URL = ''; // Use relative paths

export const useStore = create((set, get) => ({
  // State
  nodes: [],
  edges: [],
  fileNames: [],
  availableFiles: { raw_files: [], saved_files: [], raw_path: '', saved_path: '', subdirs: [], current_subdir: 'Gitam_lanes', current_saved_subdir: '' },
  currentRawDir: 'Gitam_lanes',
  currentSavedDir: '',
  loading: true,
  status: 'Initializing...',
  mode: 'select', // select, select_path, draw, smooth, connect, remove_between, reverse_path, zoom, brush_select, box_select
  sidebarMode: 'edit', // 'edit' or 'control'
  isFileLoaderOpen: false,

  // Selections & temporary data
  // NOTE: When adding new temporary state, remember to add it to resetOperationState!
  selectedNodeIds: [],
  yawVerificationResults: null,
  operationStartNodeId: null,
  smoothingPreview: null,
  smoothStartNodeId: null,
  smoothEndNodeId: null,
  smoothness: 1.0,
  weight: 1,
  pointSize: 2, // Default point size
  plotWidth: 100, // Default plot width in %
  drawPoints: [], // Temporary points for Draw mode
  showYaw: false, // Toggle for showing yaw arrows

  // Saved Graph Overlay
  savedNodes: [],
  savedEdges: [],
  showSavedGraph: false,

  // Path Direction Validation
  pathDirectionStatus: null, // { overall_status, details }

  // Actions
  toggleShowYaw: () => set(state => ({ showYaw: !state.showYaw })),

  checkPathDirection: async (startId, endId) => {
    try {
      set({ status: 'Checking Path Direction...' });
      const response = await axios.post(`${API_URL}/api/check_path_direction`, {
        start_id: startId,
        end_id: endId
      });
      set({
        pathDirectionStatus: response.data,
        status: `Direction Check: ${response.data.overall_status}`
      });
    } catch (error) {
      console.error("Error checking path direction:", error);
      set({ status: 'Error checking direction.', pathDirectionStatus: null });
    }
  },

  clearPathDirectionStatus: () => set({ pathDirectionStatus: null }),


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

  unloadGraph: async () => {
    try {
      set({ loading: true, status: 'Unloading graph data...' });
      const response = await axios.post(`${API_URL}/api/unload_graph`);
      set({
        nodes: response.data.nodes,
        edges: response.data.edges,
        fileNames: response.data.file_names,
        loading: false,
        status: 'Graph data unloaded.'
      });
    } catch (error) {
      console.error("Error unloading graph data:", error);
      set({ loading: false, status: 'Error unloading graph data.' });
    }
  },

  resetTempFile: async (filename, rawDir) => {
    try {
      set({ status: `Resetting temp file for ${filename}...` });
      await axios.post(`${API_URL}/api/reset_temp_file`, { filename, raw_dir: rawDir });
      set({ status: `Reset temp file for ${filename}.` });
    } catch (error) {
      console.error("Error resetting temp file:", error);
      set({ status: 'Error resetting temp file.' });
    }
  },

  refreshLane: async (filename) => {
    try {
      const { unloadData, resetTempFile, currentRawDir } = get();
      await unloadData(filename);
      await resetTempFile(filename, currentRawDir);
      set({ status: `Refreshed ${filename} (Reset to Original). Please reload.` });
    } catch (error) {
      console.error("Error refreshing lane:", error);
      set({ status: 'Error refreshing lane.' });
    }
  },

  verifyYaw: async () => {
    try {
      set({ status: 'Verifying Yaw...' });
      const response = await axios.post(`${API_URL}/api/verify_yaw`);
      set({
        yawVerificationResults: response.data.results,
        status: 'Yaw verification complete. Check plot for Red/Green edges.'
      });
    } catch (error) {
      console.error("Error verifying yaw:", error);
      set({ status: 'Error verifying yaw.' });
    }
  },

  toggleShowSavedGraph: async () => {
    const { showSavedGraph, savedNodes } = get();

    if (!showSavedGraph) {
      // Turn ON
      // If we haven't loaded saved data yet (or want to refresh it), fetch it
      // We should refresh it every time we toggle on to ensure accuracy
      try {
        set({ status: 'Fetching saved graph...' });
        const response = await axios.get(`${API_URL}/api/get_saved_graph`);
        if (response.data.status === 'success') {
          set({
            savedNodes: response.data.nodes,
            savedEdges: response.data.edges,
            showSavedGraph: true,
            status: 'Saved graph overlay enabled.'
          });
        } else {
          set({ status: 'Error: ' + response.data.message });
        }
      } catch (error) {
        console.error("Error fetching saved graph:", error);
        set({ status: 'Error fetching saved graph.' });
      }
    } else {
      // Turn OFF
      set({ showSavedGraph: false, status: 'Saved graph overlay disabled.' });
    }
  },

  clearVerification: () => {
    set({ yawVerificationResults: null, status: 'Verification cleared.' });
  },

  performOperation: async (operation, params = {}) => {
    try {
      set({ status: `Executing: ${operation}...` });
      const response = await axios.post(`${API_URL}/api/operation`, { operation, params });
      const { nodes, edges } = response.data;
      set(state => ({
        nodes,
        edges,
        status: `${operation} successful.`,
        selectedNodeIds: operation === 'update_node_properties' ? state.selectedNodeIds : [],
        operationStartNodeId: null,
      }));
      if (['remove_between', 'reverse_path', 'add_edge', 'copy_points', 'delete_points'].includes(operation)) {
        set({ mode: 'select' });
      }
      // Keep control mode for update_node_properties
      if (operation === 'update_node_properties') {
        // Do nothing, stay in control mode
      } else if (['update_node_properties'].includes(operation)) {
        // If we wanted to switch back, but we don't.
      }
    } catch (error) {
      console.error(`Error performing operation ${operation}:`, error);
      set({ status: `Error: ${operation} failed.` });
    }
  },

  updateNodeProperties: async (pointIds, { zone, indicator }) => {
    await get().performOperation('update_node_properties', {
      point_ids: pointIds,
      zone,
      indicator
    });
  },

  resetOperationState: () => {
    set({
      selectedNodeIds: [],
      operationStartNodeId: null,
      smoothingPreview: null,
      smoothStartNodeId: null,
      smoothEndNodeId: null,
      drawPoints: [],
      yawVerificationResults: null,
      pathDirectionStatus: null,
    });
  },

  setMode: (mode) => {
    get().resetOperationState();
    set({
      mode,
      status: `Mode: ${mode}`,
    });
  },

  setSidebarMode: (sidebarMode) => set({ sidebarMode }),

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
    } else if (mode === 'select_path') {
      if (!operationStartNodeId) {
        set({ operationStartNodeId: nodeId, status: `Start node ${nodeId} selected for path.` });
      } else {
        if (operationStartNodeId === nodeId) return; // Ignore same node click

        // Fetch path from backend
        const startId = operationStartNodeId;
        const endId = nodeId;

        set({ operationStartNodeId: null, status: 'Finding path...' });

        axios.post(`${API_URL}/api/operation`, {
          operation: 'get_path',
          params: { start_id: startId, end_id: endId }
        }).then(response => {
          if (response.data.status === 'success') {
            const pathIds = response.data.path_ids || [];
            set({ selectedNodeIds: pathIds, status: `Selected ${pathIds.length} nodes in path.`, mode: 'select' });
          }
        }).catch(async (err) => {
          console.error("Error finding path:", err);
          const response = err.response;

          // Check if it's a "No directed path" error (404)
          if (response && response.status === 404 && response.data.error_type === 'no_path') {
            // Ask user if they want to force it
            const confirmForce = window.confirm("No directed path found (lanes might be disconnected or wrong direction).\n\nDo you want to FORCE the selection using an undirected search?\n(Warning: This may create invalid 'zig-zag' paths.)");

            if (confirmForce) {
              set({ status: 'Forcing path finding (Undirected)...' });
              try {
                const retryResponse = await axios.post(`${API_URL}/api/operation`, {
                  operation: 'get_path',
                  params: { start_id: startId, end_id: endId, strict_direction: false }
                });

                if (retryResponse.data.status === 'success') {
                  const pathIds = retryResponse.data.path_ids || [];
                  set({ selectedNodeIds: pathIds, status: `Forced selection of ${pathIds.length} nodes (Undirected).`, mode: 'select' });
                  return;
                }
              } catch (retryErr) {
                console.error("Error forcing path:", retryErr);
                const retryMsg = retryErr.response?.data?.message || 'Error forcing path.';
                set({ status: `Error: ${retryMsg}`, mode: 'select' });
                return;
              }
            }
          }

          const msg = response?.data?.message || 'Error finding path.';
          set({ status: `Error: ${msg}`, mode: 'select' });
        });
      }
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
          // Logic with Retry for Remove Between
          const executeRemove = async (strict = true) => {
            try {
              await axios.post(`${API_URL}/api/operation`, {
                operation: 'remove_between',
                params: { start_id: startId, end_id: endId, strict_direction: strict }
              });
              set({
                status: `Removed nodes between ${startId} and ${endId}${!strict ? ' (Forced)' : ''}.`,
                mode: 'select', selectedNodeIds: [], operationStartNodeId: null
              });
              // Refresh data
              const { nodes, edges } = (await axios.get(`${API_URL}/api/data`)).data;
              set({ nodes, edges });
            } catch (err) {
              const response = err.response;
              if (strict && response && response.status === 404 && response.data.error_type === 'no_path') {
                if (window.confirm("No directed path found for removal.\n\nForce remove along UNDIRECTED path?\n(Warning: May delete unintended nodes on 'zig-zag' path.)")) {
                  await executeRemove(false);
                  return;
                }
              }
              console.error("Error removing:", err);
              set({ status: `Error: ${response?.data?.message || 'Failed to remove.'}` });
            }
          };
          executeRemove(true);

        } else if (mode === 'reverse_path') {
          // Logic with Retry for Reverse Path
          const executeReverse = async (strict = true) => {
            try {
              await axios.post(`${API_URL}/api/operation`, {
                operation: 'reverse_path',
                params: { start_id: startId, end_id: endId, strict_direction: strict }
              });
              set({
                status: `Reversed path ${startId}->${endId}${!strict ? ' (Forced)' : ''}.`,
                mode: 'select', selectedNodeIds: [], operationStartNodeId: null
              });
              // Refresh data
              const { nodes, edges } = (await axios.get(`${API_URL}/api/data`)).data;
              set({ nodes, edges });
            } catch (err) {
              const response = err.response;
              if (strict && response && response.status === 404 && response.data.error_type === 'no_path') {
                if (window.confirm("No directed path found to reverse.\n\nForce reverse along UNDIRECTED path?\n(Warning: May reverse unintended segments.)")) {
                  await executeReverse(false);
                  return;
                }
              }
              console.error("Error reversing:", err);
              set({ status: `Error: ${response?.data?.message || 'Failed to reverse.'}` });
            }
          };
          executeReverse(true);
        }
      }
    }
  },

  previewSmooth: async (startId, endId, strict = true) => {
    const { smoothness, weight } = get();
    try {
      set({ status: `Generating smooth preview${!strict ? ' (Forced)' : ''}...` });
      const response = await axios.post(`${API_URL}/api/smooth`, {
        start_id: startId,
        end_id: endId,
        smoothness: smoothness,
        weight: weight,
        strict_direction: strict
      });
      set({
        smoothingPreview: response.data.updated_nodes,
        status: 'Preview generated. Click "Apply Smooth" to confirm.'
      });
    } catch (error) {
      console.error("Error generating smooth preview:", error);
      const response = error.response;

      if (strict && response && response.status === 404 && response.data.error_type === 'no_path') {
        if (window.confirm("No directed path found to smooth.\n\nForce smooth along UNDIRECTED path?\n(Warning: May smooth across unrelated lanes.)")) {
          get().previewSmooth(startId, endId, false);
          return;
        }
      }

      const errorMessage = response?.data?.message || 'Error generating preview.';
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