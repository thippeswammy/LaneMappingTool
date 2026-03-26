import React, { useRef, useEffect, useImperativeHandle, forwardRef, useCallback, useMemo } from 'react';
import { Chart, registerables } from 'chart.js';
import { Line } from 'react-chartjs-2';
import zoomPlugin from 'chartjs-plugin-zoom';
import { useStore } from '../store';

// Register Chart.js components
Chart.register(...registerables, zoomPlugin);

const Plot = forwardRef(({ nodes, edges, width, height }, ref) => {
  console.log("Plot component rendering", { nodesCount: nodes?.length, edgesCount: edges?.length });
  const mode = useStore(state => state.mode);
  const sidebarMode = useStore(state => state.sidebarMode);
  const handleNodeClick = useStore(state => state.handleNodeClick);
  const performOperation = useStore(state => state.performOperation);
  const selectedNodeIds = useStore(state => state.selectedNodeIds);
  const operationStartNodeId = useStore(state => state.operationStartNodeId);
  const smoothingPreview = useStore(state => state.smoothingPreview);
  const drawPoints = useStore(state => state.drawPoints);
  const addDrawPoint = useStore(state => state.addDrawPoint);
  const pointSize = useStore(state => state.pointSize);
  const setSelectedNodeIds = useStore(state => state.setSelectedNodeIds);
  const yawVerificationResults = useStore(state => state.yawVerificationResults);
  const showYaw = useStore(state => state.showYaw);
  const showSavedGraph = useStore(state => state.showSavedGraph);
  const savedNodes = useStore(state => state.savedNodes);
  const savedEdges = useStore(state => state.savedEdges);
  const focusTarget = useStore(state => state.focusTarget); // Subscribe to focus requests

  // Simulation State
  const simulationPoints = useStore(state => state.simulationPoints);
  const activeSimulationPath = useStore(state => state.activeSimulationPath);
  const simulationPathType = useStore(state => state.simulationPathType);
  const isSimulating = useStore(state => state.isSimulating);
  const carPosition = useStore(state => state.carPosition);
  const simStartPose = useStore(state => state.simStartPose);
  const setSimStartPose = useStore(state => state.setSimStartPose);
  const simEndPose = useStore(state => state.simEndPose);
  const setSimEndPose = useStore(state => state.setSimEndPose);
  const tempSimPose = useStore(state => state.tempSimPose);
  const setTempSimPose = useStore(state => state.setTempSimPose);

  // Refs for state access in callbacks to avoid re-creating options
  const nodesRef = useRef(nodes);
  const edgesRef = useRef(edges);
  const modeRef = useRef(mode);
  const selectedNodeIdsRef = useRef(selectedNodeIds);
  const performOperationRef = useRef(performOperation);
  const handleNodeClickRef = useRef(handleNodeClick);
  const addDrawPointRef = useRef(addDrawPoint);
  const setSelectedNodeIdsRef = useRef(setSelectedNodeIds);
  const setSimStartPoseRef = useRef(setSimStartPose);
  const setSimEndPoseRef = useRef(setSimEndPose);
  const setTempSimPoseRef = useRef(setTempSimPose);
  const setModeRef = useRef(useStore.getState().setMode);

  // Persistent bounds to prevent axis shrinking
  const boundsRef = useRef({ minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity });

  // Synchronously update bounds based on current nodes to ensure options are stable
  if (nodes && nodes.length > 0) {
    let { minX, maxX, minY, maxY } = boundsRef.current;
    let updated = false;

    nodes.forEach(node => {
      if (node[1] < minX) { minX = node[1]; updated = true; }
      if (node[1] > maxX) { maxX = node[1]; updated = true; }
      if (node[2] < minY) { minY = node[2]; updated = true; }
      if (node[2] > maxY) { maxY = node[2]; updated = true; }
    });

    if (updated) {
      boundsRef.current = { minX, maxX, minY, maxY };
    }
  }

  // Extract current bounds for useMemo dependencies
  const { minX, maxX, minY, maxY } = boundsRef.current;

  // Update refs on render
  useEffect(() => {
    nodesRef.current = nodes;
    edgesRef.current = edges;
    modeRef.current = mode;
    selectedNodeIdsRef.current = selectedNodeIds;
    performOperationRef.current = performOperation;
    handleNodeClickRef.current = handleNodeClick;
    addDrawPointRef.current = addDrawPoint;
    setSelectedNodeIdsRef.current = setSelectedNodeIds;
    setSimStartPoseRef.current = setSimStartPose;
    setSimEndPoseRef.current = setSimEndPose;
    setTempSimPoseRef.current = setTempSimPose;
  }, [nodes, edges, mode, selectedNodeIds, performOperation, handleNodeClick, addDrawPoint, setSelectedNodeIds, setSimStartPose, setSimEndPose, setTempSimPose]);

  // Keep a ref for showYaw so the plugin can access the latest value without re-creation
  const showYawRef = useRef(showYaw);
  const sidebarModeRef = useRef(sidebarMode); // Ref for sidebarMode

  useEffect(() => {
    showYawRef.current = showYaw;
    sidebarModeRef.current = sidebarMode;
  }, [showYaw, sidebarMode]);

  // Animation Ref
  const animationRef = useRef({ index: 0, startTime: 0 });
  const requestRef = useRef();

  useEffect(() => {
    if (isSimulating && activeSimulationPath.length > 0) {
      animationRef.current.index = 0;

      const animate = () => {
        if (!chartRef.current) return;

        // Speed control
        animationRef.current.index += 2.5; // Adjust speed here (increased 5x)

        if (animationRef.current.index >= activeSimulationPath.length) {
          animationRef.current.index = activeSimulationPath.length - 1;
          // Optional: Auto stop or loop?
        }

        chartRef.current.update('none'); // Update without full re-render

        if (isSimulating && animationRef.current.index < activeSimulationPath.length - 1) {
          requestRef.current = requestAnimationFrame(animate);
        }
      };
      requestRef.current = requestAnimationFrame(animate);
    } else {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
      if (chartRef.current) chartRef.current.update('none');
    }

    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [isSimulating, activeSimulationPath]);


  const mapMetadata = useStore(state => state.mapMetadata);
  // Removed fetchMapMetadata call as it is no longer in the store.
  // Map metadata should be loaded via selectMap or initial state.
  const mapImageRef = useRef(null);

  useEffect(() => {
    if (mapMetadata && mapMetadata.image_url) {
      const img = new Image();
      img.src = mapMetadata.image_url;
      img.onload = () => {
        mapImageRef.current = img;
        if (chartRef.current) chartRef.current.update();
      };
    }
  }, [mapMetadata]);

  const backgroundPlugin = useMemo(() => ({
    id: 'backgroundPlugin',
    beforeDraw(chart) {
      if (!mapImageRef.current || !mapMetadata) return;

      const ctx = chart.ctx;
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;

      const { min_x, min_y, max_x, max_y } = mapMetadata;

      // Map bounds to pixel coordinates
      // Map Y is flipped relative to Chart.js usually?
      // Chart.js: Y increases upwards (Cartesian) if we set it so?
      // Default Chart.js (Line): usually Y increases upwards for 'linear' scale? Yes.
      // Map Image: Top-Left origin.
      // We need to draw the image such that its corners align with data min_x/max_y etc.
      // Metadata: origin_top_left = True.
      // Image Top-Left corresponds to (min_x, max_y) in Cartesian world.
      // Image Bottom-Right corresponds to (max_x, min_y).

      const left = xAxis.getPixelForValue(min_x);
      const right = xAxis.getPixelForValue(max_x);
      const top = yAxis.getPixelForValue(max_y);  // High Y value = Low pixel Y (top)
      const bottom = yAxis.getPixelForValue(min_y); // Low Y value = High pixel Y (bottom)

      const width = right - left;
      const height = bottom - top;

      ctx.save();
      ctx.globalAlpha = 0.5; // Transparency
      // ctx.drawImage(image, dx, dy, dWidth, dHeight)
      ctx.drawImage(mapImageRef.current, left, top, width, height);
      ctx.restore();
    }
  }), [mapMetadata]);


  const chartRef = useRef(null);
  const lastDrawnNodeId = useRef(null);

  // Expose methods to parent
  useImperativeHandle(ref, () => ({
    resetZoom: () => {
      if (chartRef.current) {
        chartRef.current.resetZoom();
      }
    },
    togglePan: () => {
      console.log("Pan toggled (placeholder)");
    },
    toggleZoom: () => {
      console.log("Zoom toggled (placeholder)");
    }
  }));

  useEffect(() => {
    if (mode !== 'draw') {
      lastDrawnNodeId.current = null;
    }
  }, [mode]);

  // Imperatively update chart bounds
  useEffect(() => {
    const chart = chartRef.current;
    if (chart) {
      let { minX, maxX, minY, maxY } = boundsRef.current;

      // Adjust using Map Metadata if available
      if (mapMetadata) {
        minX = minX !== Infinity ? Math.min(minX, mapMetadata.min_x) : mapMetadata.min_x;
        maxX = maxX !== -Infinity ? Math.max(maxX, mapMetadata.max_x) : mapMetadata.max_x;
        minY = minY !== Infinity ? Math.min(minY, mapMetadata.min_y) : mapMetadata.min_y;
        maxY = maxY !== -Infinity ? Math.max(maxY, mapMetadata.max_y) : mapMetadata.max_y;
      }

      chart.options.scales.x.suggestedMin = minX !== Infinity ? minX : undefined;
      chart.options.scales.x.suggestedMax = maxX !== -Infinity ? maxX : undefined;
      chart.options.scales.y.suggestedMin = minY !== Infinity ? minY : undefined;
      chart.options.scales.y.suggestedMax = maxY !== -Infinity ? maxY : undefined;
      chart.update('none');
    }
  }, [minX, maxX, minY, maxY, mapMetadata]);

  // Imperatively update pan enablement based on mode
  useEffect(() => {
    const chart = chartRef.current;
    if (chart) {
      const isSelectionMode = mode === 'brush_select' || mode === 'box_select' || mode === 'set_sim_start' || mode === 'set_sim_end';
      if (chart.options.plugins.zoom.pan.enabled !== !isSelectionMode) {
        chart.options.plugins.zoom.pan.enabled = !isSelectionMode;
        chart.update('none');
      }
    }
  }, [mode]);

  // Update chart when simulation poses change
  useEffect(() => {
    const chart = chartRef.current;
    if (chart) {
      chart.update('none');
    }
  }, [simStartPose, simEndPose, tempSimPose]);

  // Force update when showYaw toggles to ensure plugin draws/clears
  useEffect(() => {
    const chart = chartRef.current;
    if (chart) {
      chart.update();
    }
  }, [showYaw, sidebarMode]);

  // Handle Focus Target
  useEffect(() => {
    const chart = chartRef.current;
    if (chart && focusTarget) {
      // Zoom to point
      const { x, y } = focusTarget;

      // We want to center on (x,y) with a reasonable zoom level
      // Current boundaries?
      const zoomWidth = 10; // View 10 meters width
      const zoomHeight = 10;

      const newMinX = x - zoomWidth / 2;
      const newMaxX = x + zoomWidth / 2;
      const newMinY = y - zoomHeight / 2;
      const newMaxY = y + zoomHeight / 2;

      chart.options.scales.x.min = newMinX;
      chart.options.scales.x.max = newMaxX;
      chart.options.scales.y.min = newMinY;
      chart.options.scales.y.max = newMaxY;

      chart.update();
    }
  }, [focusTarget]);


  // Performance Optimization: Prepare edge data
  const chartData = useMemo(() => {
    const edgeData = [];
    const reverseEdgeData = []; // Declare here for proper scope

    if (nodes && edges) {
      const nodeMap = new Map(nodes.map(n => [n[0], n]));

      // Filter edges if simulating
      let edgesToRender = edges;
      let reverseEdges = [];

      if (isSimulating && activeSimulationPath.length > 0) {
        // Get IDs in path
        const pathIds = new Set(activeSimulationPath.map(p => p.id));

        // Build forward path segments (consecutive pairs in path)
        const forwardSegments = new Set();
        for (let i = 0; i < activeSimulationPath.length - 1; i++) {
          const from = activeSimulationPath[i].id;
          const to = activeSimulationPath[i + 1].id;
          forwardSegments.add(`${from}->${to}`);
        }

        // Separate edges into forward path edges and reverse edges
        const filteredEdges = edges.filter(e => pathIds.has(e[0]) && pathIds.has(e[1]));

        edgesToRender = [];
        reverseEdges = [];

        filteredEdges.forEach(edge => {
          const segmentKey = `${edge[0]}->${edge[1]}`;
          const reverseKey = `${edge[1]}->${edge[0]}`;

          // If this edge is in the forward path, it's a forward edge
          if (forwardSegments.has(segmentKey)) {
            edgesToRender.push(edge);
          }
          // If the reverse of this edge is in the forward path, it's a reverse edge
          else if (forwardSegments.has(reverseKey)) {
            reverseEdges.push(edge);
          }
          // Otherwise, it's just a normal edge between path nodes (not part of the sequential path)
          else {
            edgesToRender.push(edge);
          }
        });
      }

      edgesToRender.forEach(edge => {
        const fromNode = nodeMap.get(edge[0]);
        const toNode = nodeMap.get(edge[1]);
        if (fromNode && toNode) {
          edgeData.push({ x: fromNode[1], y: fromNode[2] });
          edgeData.push({ x: toNode[1], y: toNode[2] });
          edgeData.push({ x: NaN, y: NaN });
        }
      });

      // Populate reverse edge data
      reverseEdges.forEach(edge => {
        const fromNode = nodeMap.get(edge[0]);
        const toNode = nodeMap.get(edge[1]);
        if (fromNode && toNode) {
          reverseEdgeData.push({ x: fromNode[1], y: fromNode[2] });
          reverseEdgeData.push({ x: toNode[1], y: toNode[2] });
          reverseEdgeData.push({ x: NaN, y: NaN });
        }
      });
    }

    return {
      datasets: [
        {
          label: 'Edges',
          data: edgeData,
          borderColor: 'rgba(200, 200, 200, 0.8)',
          borderWidth: 1,
          pointRadius: 0,
          showLine: true,
          type: 'line',
          spanGaps: false,
          arrowColor: 'rgba(200, 200, 200, 0.8)' // Enable arrows for main edges
        },
        // Reverse Edges (opposite direction to path) - show with large red arrows
        ...((isSimulating && reverseEdgeData && reverseEdgeData.length > 0) ? [{
          label: 'Reverse Path Edges',
          data: reverseEdgeData,
          borderColor: 'rgba(255, 0, 0, 0.9)', // Bright Red
          borderWidth: 3,
          pointRadius: 0,
          showLine: true,
          type: 'line',
          spanGaps: false,
          arrowColor: 'rgba(255, 0, 0, 0.9)', // Red arrows
          arrowSize: 20, // Larger arrows
          order: -6 // On top of everything
        }] : []),
        // Verification Datasets
        ...(yawVerificationResults ? [
          {
            label: 'Aligned Edges',
            data: (() => {
              const data = [];
              const nodeMap = new Map(nodes.map(n => [n[0], n]));
              yawVerificationResults.forEach(res => {
                if (res.status === 'aligned') {
                  const u = nodeMap.get(res.u);
                  const v = nodeMap.get(res.v);
                  if (u && v) {
                    data.push({ x: u[1], y: u[2] });
                    data.push({ x: v[1], y: v[2] });
                    data.push({ x: NaN, y: NaN });
                  }
                }
              });
              return data;
            })(),
            borderColor: 'rgba(0, 255, 0, 0.8)', // Green
            borderWidth: 2,
            pointRadius: 0,
            showLine: true,
            type: 'line',
            spanGaps: false,
            order: -1
          },
          {
            label: 'Misaligned Edges',
            data: (() => {
              const data = [];
              const nodeMap = new Map(nodes.map(n => [n[0], n]));
              yawVerificationResults.forEach(res => {
                if (res.status === 'misaligned') {
                  const u = nodeMap.get(res.u);
                  const v = nodeMap.get(res.v);
                  if (u && v) {
                    data.push({ x: u[1], y: u[2] });
                    data.push({ x: v[1], y: v[2] });
                    data.push({ x: NaN, y: NaN });
                  }
                }
              });
              return data;
            })(),
            borderColor: 'rgba(255, 0, 0, 0.8)', // Red
            borderWidth: 2,
            pointRadius: 0,
            showLine: true,
            type: 'line',
            spanGaps: false,
            order: -1
          }
        ] : []),

        // Saved Graph Overlay
        ...(showSavedGraph ? [
          {
            label: 'Saved Edges',
            data: (() => {
              const data = [];
              if (savedNodes && savedEdges) {
                const nodeMap = new Map(savedNodes.map(n => [n[0], n]));
                savedEdges.forEach(edge => {
                  const u = nodeMap.get(edge[0]);
                  const v = nodeMap.get(edge[1]);
                  if (u && v) {
                    data.push({ x: u[1], y: u[2] });
                    data.push({ x: v[1], y: v[2] });
                    data.push({ x: NaN, y: NaN });
                  }
                });
              }
              return data;
            })(),
            borderColor: 'rgba(0, 0, 255, 0.5)', // Blue, semi-transparent
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 0,
            showLine: true,
            type: 'line',
            spanGaps: false,
            order: 0,
            arrowColor: 'rgba(0, 0, 255, 0.5)' // Custom prop for arrowPlugin
          },
          {
            label: 'Saved Nodes',
            data: savedNodes ? savedNodes.map(node => ({
              x: node[1],
              y: node[2]
            })) : [],
            backgroundColor: 'rgba(0, 0, 255, 0.5)',
            pointRadius: 3,
            type: 'scatter',
            order: 0
          }
        ] : []),

        ...(simulationPoints && simulationPoints.length > 0 ? [{
          label: 'Simulation Points',
          data: simulationPoints.map(p => ({ x: p.x, y: p.y })),
          backgroundColor: '#00FF00', // Lime Green
          pointRadius: 4,
          type: 'scatter',
          order: -3 // Top of everything
        }] : []),

        ...(carPosition ? [{
          label: 'Car',
          data: [{ x: carPosition.x, y: carPosition.y }],
          backgroundColor: '#FF00FF', // Magenta Car
          pointRadius: 8,
          pointHoverRadius: 8,
          type: 'scatter',
          order: -5 // Top check
        }] : []),

        ...(activeSimulationPath && activeSimulationPath.length > 0 ? [{
          label: 'Simulation Path',
          data: activeSimulationPath.map(p => ({ x: p.x, y: p.y })),
          borderColor: simulationPathType === 'directed' ? 'rgba(0, 255, 0, 0.8)' : 'rgba(255, 100, 0, 0.8)', // Green or Orange
          borderWidth: 4,
          borderDash: simulationPathType === 'directed' ? [] : [10, 5],
          pointRadius: 0,
          showLine: true,
          type: 'line',
          spanGaps: false,
          order: -4 // Top of simulation points
        }] : []),

        {
          label: 'Nodes',
          ...(() => {
            const nodesToRender = (nodes && isSimulating && activeSimulationPath.length > 0)
              ? nodes.filter(n => activeSimulationPath.some(p => p.id === n[0]))
              : (nodes || []);

            return {
              data: nodesToRender.map(node => ({
                x: node[1],
                y: node[2],
                id: node[0],
                yaw: node[3],
                zone: node[4],
                width: node[5],
                indicator: node[6]
              })),
              backgroundColor: nodesToRender.map(node => {
                if (Array.isArray(selectedNodeIds) && selectedNodeIds.includes(node[0])) return 'red';
                if (operationStartNodeId === node[0]) return 'blue';
                return 'rgba(0,255,255,1)';
              })
            };
          })(),
          pointRadius: pointSize,
          pointHitRadius: 10,
          type: 'scatter',
        },
        ...(smoothingPreview ? [{
          label: 'Smooth Preview',
          data: smoothingPreview.map(p => ({ x: p[1], y: p[2] })),
          borderColor: 'rgba(255, 0, 0, 1)',
          borderWidth: 2,
          borderDash: [10, 3],
          pointRadius: 0,
          showLine: true,
          type: 'line',
          spanGaps: false,
          order: -2
        }] : []),
        ...(drawPoints && drawPoints.length > 0 ? [{
          label: 'Draw Preview',
          data: drawPoints,
          borderColor: 'rgba(255, 255, 255, 0.8)',
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: 'rgba(255, 255, 255, 0.8)',
          showLine: true,
          type: 'line',
          spanGaps: false,
          order: -2
        }] : []),
        ...(simStartPose ? [{
          label: 'Sim Start Pose',
          data: [{ x: simStartPose.x, y: simStartPose.y }],
          backgroundColor: '#00FF00', // Green
          pointRadius: 6,
          type: 'scatter',
          order: -10,
          pose: simStartPose // For custom drawing
        }] : []),
        ...(simEndPose ? [{
          label: 'Sim End Pose',
          data: [{ x: simEndPose.x, y: simEndPose.y }],
          backgroundColor: '#0000FF', // Blue
          pointRadius: 6,
          type: 'scatter',
          order: -10,
          pose: simEndPose
        }] : []),
        ...(tempSimPose ? [{
          label: 'Temp Pose',
          data: [{ x: tempSimPose.x, y: tempSimPose.y }],
          backgroundColor: 'rgba(255, 255, 255, 0.5)',
          pointRadius: 4,
          type: 'scatter',
          order: -10,
          pose: tempSimPose
        }] : []),
      ]
    };
  }, [nodes, edges, selectedNodeIds, operationStartNodeId, smoothingPreview, drawPoints, pointSize, yawVerificationResults, showSavedGraph, savedNodes, savedEdges, simulationPoints, activeSimulationPath, simulationPathType, isSimulating, carPosition, simStartPose, simEndPose, tempSimPose]);

  const arrowPlugin = useMemo(() => ({
    id: 'arrowPlugin',
    afterDatasetsDraw(chart) {
      const ctx = chart.ctx;
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;

      chart.data.datasets.forEach((dataset, i) => {
        if (dataset.arrowColor) {
          const meta = chart.getDatasetMeta(i);
          // Only draw if dataset is visible
          if (!meta.hidden && meta.data.length > 0) {
            ctx.save();
            // Use the dataset's arrowColor
            const arrowColor = dataset.arrowColor || 'rgba(200, 200, 200, 0.8)';
            const arrowSize = dataset.arrowSize || 6; // Default size 6, or custom from dataset
            ctx.fillStyle = arrowColor;
            ctx.strokeStyle = arrowColor;

            const data = dataset.data;
            // Data structure: [{x,y}, {x,y}, {NaN}, {x,y}, {x,y}, {NaN}...]
            // Step by 3
            for (let j = 0; j < data.length - 1; j += 3) {
              const start = data[j];
              const end = data[j + 1];

              if (!start || !end || isNaN(start.x) || isNaN(end.x)) continue;

              const x1 = xAxis.getPixelForValue(start.x);
              const y1 = yAxis.getPixelForValue(start.y);
              const x2 = xAxis.getPixelForValue(end.x);
              const y2 = yAxis.getPixelForValue(end.y);

              if (x1 === undefined || x2 === undefined) continue;

              // Calculate angle
              const angle = Math.atan2(y2 - y1, x2 - x1);

              // Offset from the end node to avoid covering it
              const offset = 8;

              // Arrow tip position
              const tipX = x2 - offset * Math.cos(angle);
              const tipY = y2 - offset * Math.sin(angle);

              const headLen = arrowSize; // Use custom arrow size

              ctx.beginPath();
              ctx.moveTo(tipX, tipY);
              ctx.lineTo(
                tipX - headLen * Math.cos(angle - Math.PI / 6),
                tipY - headLen * Math.sin(angle - Math.PI / 6)
              );
              ctx.lineTo(
                tipX - headLen * Math.cos(angle + Math.PI / 6),
                tipY - headLen * Math.sin(angle + Math.PI / 6)
              );
              ctx.lineTo(tipX, tipY);
              ctx.fill();
            }
            ctx.restore();
          }
        }
      });
    }
  }), []);

  const poseArrowPlugin = useMemo(() => ({
    id: 'poseArrowPlugin',
    afterDatasetsDraw(chart) {
      const poses = [];
      if (simStartPose) poses.push({ ...simStartPose, color: '#00FF00' });
      if (simEndPose) poses.push({ ...simEndPose, color: '#0000FF' });
      if (tempSimPose) poses.push({ ...tempSimPose, color: '#FFFFFF' });

      if (poses.length === 0) return;

      const ctx = chart.ctx;
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;

      ctx.save();
      poses.forEach(pose => {
        const x = xAxis.getPixelForValue(pose.x);
        const y = yAxis.getPixelForValue(pose.y);
        const angle = pose.yaw;

        const arrowLen = 30;
        const tipX = x + arrowLen * Math.cos(angle);
        const tipY = y + arrowLen * Math.sin(angle);

        ctx.lineWidth = 3;
        ctx.strokeStyle = pose.color;
        ctx.fillStyle = pose.color;

        // Shaft
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(tipX, tipY);
        ctx.stroke();

        // Head
        const headLen = 10;
        ctx.beginPath();
        ctx.moveTo(tipX, tipY);
        ctx.lineTo(
          tipX - headLen * Math.cos(angle - Math.PI / 6),
          tipY - headLen * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          tipX - headLen * Math.cos(angle + Math.PI / 6),
          tipY - headLen * Math.sin(angle + Math.PI / 6)
        );
        ctx.fill();

        // Base dot
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1;
        ctx.stroke();
      });
      ctx.restore();
    }
  }), [simStartPose, simEndPose, tempSimPose]);

  const yawPlugin = useMemo(() => ({
    id: 'yawPlugin',
    afterDatasetsDraw(chart) {
      if (!showYawRef.current || sidebarModeRef.current !== 'edit') return;

      const ctx = chart.ctx;
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;
      const currentNodes = nodesRef.current;
      const currentEdges = edgesRef.current;

      if (!currentNodes) return;

      // Identify danger nodes (nodes involving bi-directional edges: A->B and B->A)
      const dangerNodes = new Set();
      if (currentEdges) {
        const edgeSet = new Set();
        currentEdges.forEach(e => edgeSet.add(`${e[0]},${e[1]}`));
        currentEdges.forEach(e => {
          if (edgeSet.has(`${e[1]},${e[0]}`)) {
            dangerNodes.add(e[0]);
            dangerNodes.add(e[1]);
          }
        });
      }

      ctx.save();
      // Default color
      const defaultColor = 'rgba(255, 165, 0, 0.8)'; // Orange
      const dangerColor = 'red';

      ctx.lineWidth = 2;

      // Calculate scales (pixels per data unit) locally to avoid precision issues with large coordinates
      const midX = (xAxis.min + xAxis.max) / 2;
      const midY = (yAxis.min + yAxis.max) / 2;

      const originX = xAxis.getPixelForValue(midX);
      const unitX = xAxis.getPixelForValue(midX + 1);
      const scaleX = unitX - originX;

      const originY = yAxis.getPixelForValue(midY);
      const unitY = yAxis.getPixelForValue(midY + 1);
      const scaleY = unitY - originY;

      currentNodes.forEach(node => {
        const x = xAxis.getPixelForValue(node[1]);
        const y = yAxis.getPixelForValue(node[2]);
        const yaw = node[3]; // format: [id, x, y, yaw, ...]

        if (x === undefined || y === undefined) return;

        // Set color based on danger status
        const isDanger = dangerNodes.has(node[0]);
        ctx.strokeStyle = isDanger ? dangerColor : defaultColor;
        ctx.fillStyle = isDanger ? dangerColor : defaultColor;

        // Calculate direction vector in pixel space
        // Yaw is in data space (CCW from East)
        const dirX = Math.cos(yaw) * scaleX;
        const dirY = Math.sin(yaw) * scaleY;

        // Normalize to fixed pixel length
        const len = Math.sqrt(dirX * dirX + dirY * dirY);
        if (len === 0) return;

        const arrowLen = 15;
        const ndx = dirX / len;
        const ndy = dirY / len;

        const endX = x + ndx * arrowLen;
        const endY = y + ndy * arrowLen;

        // Draw line
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(endX, endY);
        ctx.stroke();

        // Draw arrow head
        // We calculate the angle of the PIXEL line for the arrow head rotation
        const angle = Math.atan2(ndy, ndx);
        const headLen = 5;

        ctx.beginPath();
        ctx.moveTo(endX, endY);
        ctx.lineTo(
          endX - headLen * Math.cos(angle - Math.PI / 6),
          endY - headLen * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          endX - headLen * Math.cos(angle + Math.PI / 6),
          endY - headLen * Math.sin(angle + Math.PI / 6)
        );
        ctx.lineTo(endX, endY);
        ctx.fill();
      });

      ctx.restore();
    }
  }), []); // Empty dependencies!


  const handleCanvasContextMenu = useCallback((event) => {
    event.preventDefault();
    const chart = chartRef.current;
    if (!chart) return;

    const elements = chart.getElementsAtEventForMode(event, 'nearest', { intersect: true }, true);

    if (elements.length > 0) {
      const element = elements[0];
      if (element.datasetIndex === 1) { // Nodes dataset
        const currentNodes = nodesRef.current;
        const nodeId = currentNodes[element.index][0];

        if (event.ctrlKey || event.metaKey) {
          performOperationRef.current('delete_points', { point_ids: [nodeId] });
        } else {
          performOperationRef.current('break_links', { point_id: nodeId });
        }
      }
    }
  }, []);

  const findNearestNode = useCallback((x, y) => {
    const currentNodes = nodesRef.current;
    if (!currentNodes || currentNodes.length === 0) return null;
    let minDist = Infinity;
    let nearestNode = null;

    currentNodes.forEach(node => {
      const dx = node[1] - x;
      const dy = node[2] - y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < minDist) {
        minDist = dist;
        nearestNode = node;
      }
    });
    return { node: nearestNode, dist: minDist };
  }, []);

  // Native Click Handler passed to the Line component (which renders the canvas)
  const handleCanvasClick = useCallback((event) => {
    const chart = chartRef.current;
    if (!chart) return;

    // We use the native event or the React synthetic event.
    // React synthetic event has .nativeEvent, but properties like clientX are on the synthetic event too.
    // event.button === 0 is Left Click.

    const rect = chart.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const xScale = chart.scales.x;
    const yScale = chart.scales.y;
    const xData = xScale.getValueForPixel(x);
    const yData = yScale.getValueForPixel(y);

    const currentMode = modeRef.current;

    console.log("Canvas Click (Native):", {
      button: event.button,
      ctrlKey: event.ctrlKey,
      metaKey: event.metaKey,
      xData, yData,
      mode: currentMode
    });

    if (currentMode === 'draw') {
      addDrawPointRef.current({ x: xData, y: yData });
    } else {
      // Check if we clicked on an existing element using Chart.js helper
      // We need to use the native event for getElementsAtEventForMode if possible, 
      // or just pass the synthetic event which Chart.js handles.
      const elements = chart.getElementsAtEventForMode(event.nativeEvent || event, 'nearest', { intersect: true }, true);

      if (elements.length > 0) {
        const element = elements[0];
        if (element.datasetIndex === 1) { // Nodes dataset
          const currentNodes = nodesRef.current;
          const nodeId = currentNodes[element.index][0];
          // Normal click on node -> Select
          // Shift + Click -> Multi-select (handled in handleNodeClick)
          handleNodeClickRef.current(nodeId, event.shiftKey);
          return;
        }
      }

      // If no element clicked, check for Ctrl + Click (Add Node)
      // Explicitly check for Left Click (button 0) and Ctrl key
      if (event.button === 0 && (event.ctrlKey || event.metaKey)) {
        const result = findNearestNode(xData, yData);
        const CONNECTION_THRESHOLD = 5.0;

        if (result && result.node && result.dist < CONNECTION_THRESHOLD) {
          const nearestNode = result.node;
          const nearestNodeId = nearestNode[0];
          const zone = nearestNode[4];
          performOperationRef.current('add_node', { x: xData, y: yData, lane_id: zone, connect_to: nearestNodeId });
        } else {
          performOperationRef.current('add_node', { x: xData, y: yData, lane_id: 0, connect_to: null });
        }
      }
    }
  }, [findNearestNode]);

  // Selection State
  const [selectionBox, setSelectionBox] = React.useState(null);
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef(null);

  const handleCanvasMouseDown = useCallback((event) => {
    const currentMode = modeRef.current;
    if (currentMode !== 'brush_select' && currentMode !== 'box_select' && currentMode !== 'set_sim_start' && currentMode !== 'set_sim_end') return;

    const chart = chartRef.current;
    if (!chart) return;

    const rect = chart.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const xData = chart.scales.x.getValueForPixel(x);
    const yData = chart.scales.y.getValueForPixel(y);

    isDraggingRef.current = true;
    dragStartRef.current = { x: xData, y: yData, pixelX: x, pixelY: y };

    if (currentMode === 'set_sim_start' || currentMode === 'set_sim_end') {
      setTempSimPoseRef.current({ x: xData, y: yData, yaw: 0, type: currentMode });
    } else if (currentMode === 'box_select') {
      setSelectionBox({ startX: xData, startY: yData, endX: xData, endY: yData });
    } else if (currentMode === 'brush_select') {
      // Initial click in brush mode also selects
      const result = findNearestNode(xData, yData);
      if (result && result.node && result.dist < 5.0) { // Threshold
        const nodeId = result.node[0];
        const currentSelected = selectedNodeIdsRef.current || [];
        if (!currentSelected.includes(nodeId)) {
          handleNodeClickRef.current(nodeId, true); // true for multi-select
        }
      }
    }
  }, [findNearestNode]);

  const handleCanvasMouseMove = useCallback((event) => {
    if (!isDraggingRef.current) return;
    const currentMode = modeRef.current;
    if (currentMode !== 'brush_select' && currentMode !== 'box_select' && currentMode !== 'set_sim_start' && currentMode !== 'set_sim_end') return;

    const chart = chartRef.current;
    if (!chart) return;

    const rect = chart.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const xData = chart.scales.x.getValueForPixel(x);
    const yData = chart.scales.y.getValueForPixel(y);

    if (currentMode === 'set_sim_start' || currentMode === 'set_sim_end') {
      const dx = xData - dragStartRef.current.x;
      const dy = yData - dragStartRef.current.y;
      const yaw = Math.atan2(dy, dx);
      setTempSimPoseRef.current({ ...dragStartRef.current, yaw, type: currentMode });
    } else if (currentMode === 'box_select') {
      setSelectionBox(prev => ({ ...prev, endX: xData, endY: yData }));
    } else if (currentMode === 'brush_select') {
      const result = findNearestNode(xData, yData);
      if (result && result.node && result.dist < 5.0) { // Threshold
        const nodeId = result.node[0];
        const currentSelected = selectedNodeIdsRef.current;
        if (!currentSelected.includes(nodeId)) {
          handleNodeClickRef.current(nodeId, true); // true for multi-select
        }
      }
    }
  }, [findNearestNode]);

  const handleCanvasMouseUp = useCallback((event) => {
    if (!isDraggingRef.current) return;
    isDraggingRef.current = false;
    const currentMode = modeRef.current;

    if (currentMode === 'set_sim_start' || currentMode === 'set_sim_end') {
      const { x, y, yaw } = useStore.getState().tempSimPose || {};
      if (x !== undefined) {
        const pose = { x, y, yaw, name: `Manual_${currentMode === 'set_sim_start' ? 'Start' : 'End'}` };
        if (currentMode === 'set_sim_start') setSimStartPoseRef.current(pose);
        else setSimEndPoseRef.current(pose);
      }
      setTempSimPoseRef.current(null);
      setModeRef.current('select');
    } else if (currentMode === 'box_select' && selectionBox) {
      // Finalize box selection
      const { startX, startY, endX, endY } = selectionBox;
      const minX = Math.min(startX, endX);
      const maxX = Math.max(startX, endX);
      const minY = Math.min(startY, endY);
      const maxY = Math.max(startY, endY);

      const currentNodes = nodesRef.current;
      const newSelectedIds = [];

      currentNodes.forEach(node => {
        const nx = node[1];
        const ny = node[2];
        if (nx >= minX && nx <= maxX && ny >= minY && ny <= maxY) {
          newSelectedIds.push(node[0]);
        }
      });

      // Update selection
      if (event.shiftKey) {
        // Add to existing
        const currentSelected = selectedNodeIdsRef.current || [];
        const combined = [...new Set([...currentSelected, ...newSelectedIds])];
        setSelectedNodeIdsRef.current(combined);
      } else {
        // Replace
        setSelectedNodeIdsRef.current(newSelectedIds);
      }

      setSelectionBox(null);
    }
    dragStartRef.current = null;
  }, [selectionBox]);

  // Add selection box to datasets if it exists
  const chartDataWithSelection = useMemo(() => {
    const data = chartData;
    if (selectionBox) {
      // Create a rectangle dataset
      const { startX, startY, endX, endY } = selectionBox;
      const boxData = [
        { x: startX, y: startY },
        { x: endX, y: startY },
        { x: endX, y: endY },
        { x: startX, y: endY },
        { x: startX, y: startY }
      ];

      return {
        ...data,
        datasets: [
          ...data.datasets,
          {
            label: 'Selection Box',
            data: boxData,
            borderColor: 'rgba(255, 255, 0, 0.8)',
            borderWidth: 1,
            borderDash: [5, 5],
            fill: true,
            backgroundColor: 'rgba(255, 255, 0, 0.1)',
            type: 'line',
            pointRadius: 0,
            order: -1 // Draw on top
          }
        ]
      };
    }
    return data;
  }, [chartData, selectionBox]);

  // Simulation Plugins
  const drawSimulationPoints = useMemo(() => ({
    id: 'drawSimulationPoints',
    afterDatasetsDraw(chart) {
      if (simulationPoints.length === 0) return;

      const ctx = chart.ctx;
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;

      ctx.save();
      ctx.lineWidth = 2;
      ctx.textAlign = 'center';
      ctx.font = 'bold 12px Arial';

      simulationPoints.forEach(point => {
        const x = xAxis.getPixelForValue(point.x);
        const y = yAxis.getPixelForValue(point.y);

        // Skip if out of bounds (optimization)
        // if (x < 0 || x > chart.width || y < 0 || y > chart.height) return;

        // Draw Arrow (Yaw)
        const arrowLen = 20; // Longer arrow
        const angle = point.yaw;

        const tipX = x + arrowLen * Math.cos(angle);
        const tipY = y + arrowLen * Math.sin(angle);

        // Arrow Shaft
        ctx.beginPath();
        ctx.strokeStyle = '#00FF00'; // Lime Green
        ctx.moveTo(x, y);
        ctx.lineTo(tipX, tipY);
        ctx.stroke();

        // Arrow Head
        const headLen = 8;
        ctx.beginPath();
        ctx.fillStyle = '#00FF00';
        ctx.moveTo(tipX, tipY);
        ctx.lineTo(
          tipX - headLen * Math.cos(angle - Math.PI / 6),
          tipY - headLen * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          tipX - headLen * Math.cos(angle + Math.PI / 6),
          tipY - headLen * Math.sin(angle + Math.PI / 6)
        );
        ctx.fill();

        // Draw Point Circle
        ctx.beginPath();
        ctx.fillStyle = '#FFFF00'; // Yellow center
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();

        // Draw Label
        ctx.fillStyle = '#FFFFFF';
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 2;
        ctx.strokeText(point.name, x, y - 10);
        ctx.fillText(point.name, x, y - 10);
      });

      ctx.restore();
    }
  }), [simulationPoints]);

  const drawSimulationPath = useMemo(() => ({
    id: 'drawSimulationPath',
    beforeDatasetsDraw(chart) {
      if (activeSimulationPath.length === 0) return;

      const ctx = chart.ctx;
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;

      ctx.save();
      ctx.beginPath();
      ctx.strokeStyle = '#FFFF00'; // Yellow
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);

      activeSimulationPath.forEach((point, index) => {
        const x = xAxis.getPixelForValue(point.x);
        const y = yAxis.getPixelForValue(point.y);
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });

      ctx.stroke();
      ctx.restore();
    }
  }), [activeSimulationPath]);

  const carAnimationPlugin = useMemo(() => ({
    id: 'carAnimationPlugin',
    afterDatasetsDraw(chart) {
      if (!isSimulating || activeSimulationPath.length === 0) return;

      const idx = animationRef.current.index;
      const floorIdx = Math.floor(idx);
      const ceilIdx = Math.min(floorIdx + 1, activeSimulationPath.length - 1);
      const ratio = idx - floorIdx;

      const p1 = activeSimulationPath[floorIdx];
      const p2 = activeSimulationPath[ceilIdx];

      if (!p1 || !p2) return;

      // Linear interpolation
      const currentX = p1.x + (p2.x - p1.x) * ratio;
      const currentY = p1.y + (p2.y - p1.y) * ratio;
      // Interpolate yaw too ?
      // If we don't have yaw in path, compute it from p1->p2
      let currentYaw = p1.yaw;
      if (currentYaw === undefined) {
        currentYaw = Math.atan2(p2.y - p1.y, p2.x - p1.x);
      }

      const ctx = chart.ctx;
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;

      const screenX = xAxis.getPixelForValue(currentX);
      const screenY = yAxis.getPixelForValue(currentY);
      // Yaw is in global coords, need to convert to screen rotation?
      // Screen Y is flipped? check map metadata or assumption. 
      // Usually standard math angle works if we flip Y logic or if both are cartesian.
      // Since arrow plugin uses sin/cos directly, let's assume standard.

      ctx.save();
      ctx.translate(screenX, screenY);
      // Rotate context
      // If Y axis is flipped (pixels increase downwards), positive angle (CCW) might need sign change.
      // Chart.js default: Y increases downwards.
      // Our data: Y increases... depends on data.
      // Assuming standard rotation.
      ctx.rotate(currentYaw);

      // Draw Car
      ctx.fillStyle = '#00BFFF'; // Deep Sky Blue
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 1;

      // Car Body (Rectangle)
      ctx.fillRect(-10, -5, 20, 10);
      ctx.strokeRect(-10, -5, 20, 10);

      // Headlights / Direction indicator
      ctx.fillStyle = '#FFFF00';
      ctx.beginPath();
      ctx.arc(8, -3, 2, 0, 2 * Math.PI); // Front Left
      ctx.arc(8, 3, 2, 0, 2 * Math.PI);  // Front Right
      ctx.fill();

      ctx.restore();
    }
  }), [isSimulating, activeSimulationPath, animationRef]); // Depend on animationRef?


  const options = useMemo(() => ({
    responsive: true,
    animation: false,
    maintainAspectRatio: false,
    events: ['mousemove', 'mouseout', 'click', 'touchstart', 'touchmove', 'mousedown', 'mouseup'],
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function (context) {
            if (context.dataset.label === 'Nodes') {
              const point = context.raw;
              return [
                `Node ID: ${point.id}`,
                `X: ${point.x.toFixed(2)}`,
                `Y: ${point.y.toFixed(2)}`,
                `Yaw: ${point.yaw !== undefined ? point.yaw.toFixed(2) : 'N/A'}`,
                `Zone: ${point.zone !== undefined ? point.zone : 'N/A'}`,
                `Width: ${point.width !== undefined ? point.width.toFixed(2) : 'N/A'}`,
                `Indicator: ${point.indicator !== undefined ? point.indicator : 'N/A'}`
              ];
            }
            return null;
          }
        }
      },
      zoom: {
        pan: {
          enabled: true, // Default enabled, controlled imperatively
          mode: 'xy',
        },
        zoom: {
          wheel: { enabled: true },
          pinch: { enabled: true },
          mode: 'xy',
        }
      }
    },
    scales: {
      x: {
        type: 'linear',
        position: 'bottom',
        grid: { color: '#444' },
        ticks: { color: '#aaa' }
      },
      y: {
        type: 'linear',
        position: 'left',
        grid: { color: '#444' },
        ticks: { color: '#aaa' }
      }
    }
  }), []); // Removed dependencies to prevent recreation

  return (
    <div
      className="plot-container"
      style={{ position: 'relative', height: height, width: width }}
      onContextMenu={handleCanvasContextMenu}
      onMouseDown={handleCanvasMouseDown}
      onMouseMove={handleCanvasMouseMove}
      onMouseUp={handleCanvasMouseUp}
    >
      <Line
        ref={chartRef}
        data={chartDataWithSelection}
        options={options}
        plugins={[backgroundPlugin, yawPlugin, arrowPlugin, drawSimulationPoints, drawSimulationPath, carAnimationPlugin, poseArrowPlugin]}
        onClick={handleCanvasClick}
      />
    </div>
  );
});

export default Plot;
