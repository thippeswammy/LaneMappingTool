import { create } from 'zustand';
import axios from 'axios';

const API_URL = 'http://localhost:5001'; // Flask backend server


export const useStore = create((set, get) => ({
  // State
  nodes: [],
  edges: [],
  fileNames: [],
  availableFiles: { raw_files: [], saved_files: [], pickle_files: [], json_files: [], raw_path: '', saved_path: '', subdirs: [], current_subdir: 'Gitam_lanes', current_saved_subdir: '' },
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
  yawAnalysisResult: null, // Stores { anomalies, profile, total_nodes }
  isAnalyzingYaw: false,
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
  focusTarget: null, // { x, y, random: Math.random() } to trigger focus


  // Saved Graph Overlay
  savedNodes: [],
  savedEdges: [],
  showSavedGraph: false,


  // Path Direction Validation
  pathDirectionStatus: null, // { overall_status, details }

  // Simulation State
  simulationMode: false,
  simulationFiles: [],
  simulationPoints: [],      // Loaded points {name, x, y, yaw}
  simStartPose: null,        // Selected start pose {x, y, yaw, name}
  simEndPose: null,          // Selected end pose {x, y, yaw, name}
  tempSimPose: null,         // Temporary pose during drag {x, y, yaw, type}
  activeSimulationPath: [],  // Path for animation
  simulationPathType: 'directed', // 'directed' or 'undirected'
  carPosition: null, // Current position of the car animation {x, y, yaw}
  isSimulating: false,
  simulationStatus: '',

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

  // Simulation Actions
  toggleSimulationMode: () => set(state => ({ simulationMode: !state.simulationMode })),

  fetchSimulationFiles: async () => {
    try {
      const response = await axios.get(`${API_URL}/api/simulation/files`);
      if (response.data.status === 'success') {
        set({ simulationFiles: response.data.files });
      }
    } catch (error) {
      console.error("Error fetching simulation files:", error);
    }
  },

  loadSimulationPoints: async (filename) => {
    try {
      set({ status: `Loading simulation file: ${filename}...` });
      const response = await axios.post(`${API_URL}/api/simulation/load`, { filename });
      if (response.data.status === 'success') {
        set({
          simulationPoints: response.data.points,
          status: `Loaded ${response.data.points.length} simulation points.`
        });
      }
    } catch (error) {
      console.error("Error loading simulation points:", error);
      set({ status: 'Error loading simulation points.' });
    }
  },

  computeSimulationPath: async (startName, endName) => {
    console.log("=".repeat(70));
    console.log("computeSimulationPath called!");
    console.log("Start name:", startName);
    console.log("End name:", endName);

    const { simulationPoints } = get();
    console.log("Simulation points loaded:", simulationPoints?.length || 0);

    const startPoint = typeof startName === 'string'
      ? simulationPoints.find(p => p.name === startName)
      : startName; // Assume it's an object {x, y, yaw}

    const endPoint = typeof endName === 'string'
      ? simulationPoints.find(p => p.name === endName)
      : endName; // Assume it's an object {x, y, yaw}

    console.log("Start point resolved:", startPoint);
    console.log("End point resolved:", endPoint);

    if (!startPoint || !endPoint) {
      console.error("❌ Start or end point not found!");
      set({ status: 'Error: Start or End point not found.' });
      return;
    }

    try {
      set({ status: `Computing path from ${startName} to ${endName}...` });
      console.log("Sending request to:", `${API_URL}/api/simulation/compute_path`);
      console.log("Request payload:", { start: startPoint, end: endPoint });

      const response = await axios.post(`${API_URL}/api/simulation/compute_path`, {
        start: startPoint,
        end: endPoint
      });

      console.log("Response received:", response.data);

      if (response.data.status === 'success') {
        console.log("✅ Path computed successfully!");
        set({
          activeSimulationPath: response.data.path,
          simulationPathType: response.data.path_type || 'directed',
          status: response.data.message || 'Path computed. Ready to simulate.'
        });
        return response.data.path;
      }
    } catch (error) {
      console.error("❌ Error computing simulation path:", error);
      console.error("Error response:", error.response?.data);
      set({ status: 'Error computing path.' });
    }
    return null;
  },

  startSimulation: () => set({ isSimulating: true }),
  stopSimulation: () => set({ isSimulating: false, carPosition: null }),
  setCarPosition: (pos) => set({ carPosition: pos }),
  setSimStartPose: (pose) => set({
    simStartPose: pose,
    status: pose ? `Start Pose set to (${pose.x.toFixed(2)}, ${pose.y.toFixed(2)}) @ ${((pose.yaw * 180) / Math.PI).toFixed(1)}°` : ''
  }),
  setSimEndPose: (pose) => set({
    simEndPose: pose,
    status: pose ? `End Pose set to (${pose.x.toFixed(2)}, ${pose.y.toFixed(2)}) @ ${((pose.yaw * 180) / Math.PI).toFixed(1)}°` : ''
  }),
  setTempSimPose: (pose) => set({ tempSimPose: pose }),


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

  availableMaps: [],
  mapMetadata: null, // Store map metadata

  fetchMaps: async () => {
    try {
      const response = await axios.get(`${API_URL}/api/maps`);
      if (response.data.status === 'success') {
        set({ availableMaps: response.data.maps });
      }
    } catch (error) {
      console.error("Error fetching maps:", error);
    }
  },

  selectMap: async (mapName, force = false) => {
    try {
      const response = await axios.post(`${API_URL}/api/load_map`, { map_name: mapName, force_process: force });
      if (response.data.status === 'success') {
        set({ mapMetadata: response.data.metadata });
        // Refresh available maps list if we forced a process (to update 'processed' status)
        if (force) {
          get().fetchMaps();
        }
      }
    } catch (error) {
      console.error("Error loading map:", error);
    }
  },

  // fetchMapMetadata refactored to just default load if needed, 
  // but for now, we rely on user selection or default via useEffect in component.

  loadData: async (rawFiles, savedNodesFile, savedEdgesFile, rawDataDir, savedGraphDir, pickleFile, jsonFile) => {
    try {
      set({ loading: true, status: 'Loading selected files...' });
      const response = await axios.post(`${API_URL}/api/load`, {
        raw_files: rawFiles,
        saved_nodes_file: savedNodesFile,
        saved_edges_file: savedEdgesFile,
        pickle_file: pickleFile,
        json_file: jsonFile,
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
        nodes: response.data.nodes || [],
        edges: response.data.edges || [],
        fileNames: response.data.file_names || [],
        selectedNodeIds: [],
        operationStartNodeId: null,
        smoothingPreview: null,
        drawPoints: [],
        simulationPoints: [],
        activeSimulationPath: [],
        simStartPose: null,
        simEndPose: null,
        tempSimPose: null,
        pathDirectionStatus: null,
        yawVerificationResults: null,
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

  analyzeYaw: async () => {
    try {
      set({ status: 'Analyzing Yaw...', isAnalyzingYaw: true, yawAnalysisResult: null });
      const response = await axios.post(`${API_URL}/api/analyze_yaw`);
      if (response.data.status === 'success') {
        set({
          yawAnalysisResult: response.data,
          status: `Analysis Complete. Found ${response.data.anomalies.length} anomalies.`
        });
      } else {
        set({ status: 'Error: ' + response.data.message });
      }
    } catch (error) {
      console.error("Error analyzing yaw:", error);
      set({ status: 'Error analyzing yaw.' });
    } finally {
      set({ isAnalyzingYaw: false });
    }
  },

  applyYawFix: async () => {
    try {
      set({ status: 'Applying Yaw Fix...', isAnalyzingYaw: true });
      const response = await axios.post(`${API_URL}/api/fix_yaw`);
      if (response.data.status === 'success') {
        set({
          nodes: response.data.nodes,
          // Edges usually don't chang but update just in case
          edges: response.data.edges || get().edges,
          status: `Fixed ${response.data.report.length} anomalies. Please SAVE data.`,
          yawAnalysisResult: null // Clear result as it is now stale
        });
      } else {
        set({ status: 'Error: ' + response.data.message });
      }
    } catch (error) {
      console.error("Error fixing yaw:", error);
      set({ status: 'Error fixing yaw.' });
    } finally {
      set({ isAnalyzingYaw: false });
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
      tempSimPose: null,
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

  focusOnNode: (nodeId) => {
    const { nodes } = get();
    const node = nodes.find(n => n[0] === nodeId);
    if (node) {
      // Toggle random to ensure effect triggers even for same node click
      set({
        focusTarget: { x: node[1], y: node[2], random: Math.random() },
        selectedNodeIds: [nodeId], // Also select it
        mode: 'select'
      });
    }
  },

  setSelectedNodeIds: (ids) => {
    set({ selectedNodeIds: ids });
  },

  addDrawPoint: (point) => {
    set(state => {
      const lastPoint = state.drawPoints[state.drawPoints.length - 1];
      const newPoints = [];

      if (lastPoint) {
        // Calculate distance between last point and new point
        const dx = point.x - lastPoint.x;
        const dy = point.y - lastPoint.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Interpolate points at 0.5m intervals if distance is sufficient
        const SPACING = 0.5;
        if (distance > SPACING) {
          const numSegments = Math.floor(distance / SPACING);
          for (let i = 1; i <= numSegments; i++) {
            const t = (i * SPACING) / distance;
            newPoints.push({
              x: lastPoint.x + dx * t,
              y: lastPoint.y + dy * t
            });
          }
        }
      }

      // Always add the clicked point at the end
      newPoints.push(point);

      return {
        drawPoints: [...state.drawPoints, ...newPoints]
      };
    });
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
    } else if (['smooth', 'remove_between', 'reverse_path', 'connect', 'two_way_road'].includes(mode)) {
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
        } else if (mode === 'two_way_road') {
          // Logic with Retry for Two Way Road
          const executeTwoWay = async (strict = true) => {
            try {
              await axios.post(`${API_URL}/api/operation`, {
                operation: 'two_way_road',
                params: { start_id: startId, end_id: endId, strict_direction: strict }
              });
              set({
                status: `Created two-way road between ${startId} and ${endId}${!strict ? ' (Forced)' : ''}.`,
                mode: 'select', selectedNodeIds: [], operationStartNodeId: null
              });
              // Refresh data
              const { nodes, edges } = (await axios.get(`${API_URL}/api/data`)).data;
              set({ nodes, edges });
            } catch (err) {
              const response = err.response;
              if (strict && response && response.status === 404 && response.data.error_type === 'no_path') {
                if (window.confirm("No directed path found for Two-Way Road.\n\nForce creation along UNDIRECTED path?\n(Warning: May Create unintended paths.)")) {
                  await executeTwoWay(false);
                  return;
                }
              }
              console.error("Error creating two-way road:", err);
              set({ status: `Error: ${response?.data?.message || 'Failed to create two-way road.'}` });
            }
          };
          executeTwoWay(true);
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