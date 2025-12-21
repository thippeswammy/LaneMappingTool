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

  // Refs for state access in callbacks to avoid re-creating options
  const nodesRef = useRef(nodes);
  const modeRef = useRef(mode);
  const selectedNodeIdsRef = useRef(selectedNodeIds);
  const performOperationRef = useRef(performOperation);
  const handleNodeClickRef = useRef(handleNodeClick);
  const addDrawPointRef = useRef(addDrawPoint);
  const setSelectedNodeIdsRef = useRef(setSelectedNodeIds);

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
    modeRef.current = mode;
    selectedNodeIdsRef.current = selectedNodeIds;
    performOperationRef.current = performOperation;
    handleNodeClickRef.current = handleNodeClick;
    addDrawPointRef.current = addDrawPoint;
    setSelectedNodeIdsRef.current = setSelectedNodeIds;
    addDrawPointRef.current = addDrawPoint;
    setSelectedNodeIdsRef.current = setSelectedNodeIds;
  }, [nodes, mode, selectedNodeIds, performOperation, handleNodeClick, addDrawPoint, setSelectedNodeIds]);

  // Keep a ref for showYaw so the plugin can access the latest value without re-creation
  const showYawRef = useRef(showYaw);
  useEffect(() => {
    showYawRef.current = showYaw;
  }, [showYaw]);


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
      chart.options.scales.x.suggestedMin = minX !== Infinity ? minX : undefined;
      chart.options.scales.x.suggestedMax = maxX !== -Infinity ? maxX : undefined;
      chart.options.scales.y.suggestedMin = minY !== Infinity ? minY : undefined;
      chart.options.scales.y.suggestedMax = maxY !== -Infinity ? maxY : undefined;
      chart.update('none');
    }
  }, [minX, maxX, minY, maxY]);

  // Imperatively update pan enablement based on mode
  useEffect(() => {
    const chart = chartRef.current;
    if (chart) {
      const isSelectionMode = mode === 'brush_select' || mode === 'box_select';
      if (chart.options.plugins.zoom.pan.enabled !== !isSelectionMode) {
        chart.options.plugins.zoom.pan.enabled = !isSelectionMode;
        chart.update('none');
      }
    }
  }, [mode]);

  // Force update when showYaw toggles to ensure plugin draws/clears
  useEffect(() => {
    const chart = chartRef.current;
    if (chart) {
      chart.update();
    }
  }, [showYaw]);


  // Performance Optimization: Prepare edge data
  const chartData = useMemo(() => {
    const edgeData = [];
    if (nodes && edges) {
      const nodeMap = new Map(nodes.map(n => [n[0], n]));
      edges.forEach(edge => {
        const fromNode = nodeMap.get(edge[0]);
        const toNode = nodeMap.get(edge[1]);
        if (fromNode && toNode) {
          edgeData.push({ x: fromNode[1], y: fromNode[2] });
          edgeData.push({ x: toNode[1], y: toNode[2] });
          edgeData.push({ x: NaN, y: NaN });
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
        },
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

        {
          label: 'Nodes',
          data: nodes ? nodes.map(node => ({
            x: node[1],
            y: node[2],
            id: node[0],
            yaw: node[3],
            zone: node[4],
            width: node[5],
            indicator: node[6]
          })) : [],
          backgroundColor: nodes ? nodes.map(node => {
            if (selectedNodeIds.includes(node[0])) return 'red';
            if (operationStartNodeId === node[0]) return 'blue';
            return 'rgba(0,255,255,1)';
          }) : [],
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
      ]
    };
  }, [nodes, edges, selectedNodeIds, operationStartNodeId, smoothingPreview, drawPoints, pointSize, yawVerificationResults, showSavedGraph, savedNodes, savedEdges]);

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
            // Use a distinct high-contrast color for arrows if requested, otherwise default to dataset prop
            // User requested "different color". Let's use Magenta for visibility against the blue line.
            const arrowColor = 'rgba(255, 0, 255, 1)';
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
              // Saved nodes have radius 3, let's give it 6px clearance
              const offset = 8;

              // Arrow tip position
              const tipX = x2 - offset * Math.cos(angle);
              const tipY = y2 - offset * Math.sin(angle);

              const headLen = 6; // Arrow head length (smaller than point size)

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

  const yawPlugin = useMemo(() => ({
    id: 'yawPlugin',
    afterDatasetsDraw(chart) {
      if (!showYawRef.current) return;

      const ctx = chart.ctx;
      const xAxis = chart.scales.x;
      const yAxis = chart.scales.y;
      const currentNodes = nodesRef.current;

      if (!currentNodes) return;

      ctx.save();
      ctx.strokeStyle = 'rgba(255, 165, 0, 0.8)'; // Orange
      ctx.lineWidth = 2;
      ctx.fillStyle = 'rgba(255, 165, 0, 0.8)';

      currentNodes.forEach(node => {
        const x = xAxis.getPixelForValue(node[1]);
        const y = yAxis.getPixelForValue(node[2]);
        const yaw = node[3]; // format: [id, x, y, yaw, ...]

        if (x === undefined || y === undefined) return;

        const arrowLen = 15;
        const headLen = 5;

        // End point (Flip Y for canvas)
        const endX = x + arrowLen * Math.cos(yaw);
        const endY = y - arrowLen * Math.sin(yaw);

        // Draw line
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(endX, endY);
        ctx.stroke();

        // Draw arrow head
        const angle = Math.atan2(endY - y, endX - x);

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
    if (currentMode !== 'brush_select' && currentMode !== 'box_select') return;

    const chart = chartRef.current;
    if (!chart) return;

    const rect = chart.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const xData = chart.scales.x.getValueForPixel(x);
    const yData = chart.scales.y.getValueForPixel(y);

    isDraggingRef.current = true;
    dragStartRef.current = { x: xData, y: yData, pixelX: x, pixelY: y };

    if (currentMode === 'box_select') {
      setSelectionBox({ startX: xData, startY: yData, endX: xData, endY: yData });
    } else if (currentMode === 'brush_select') {
      // Initial click in brush mode also selects
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

  const handleCanvasMouseMove = useCallback((event) => {
    if (!isDraggingRef.current) return;
    const currentMode = modeRef.current;
    if (currentMode !== 'brush_select' && currentMode !== 'box_select') return;

    const chart = chartRef.current;
    if (!chart) return;

    const rect = chart.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const xData = chart.scales.x.getValueForPixel(x);
    const yData = chart.scales.y.getValueForPixel(y);

    if (currentMode === 'box_select') {
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

    if (currentMode === 'box_select' && selectionBox) {
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
        const currentSelected = selectedNodeIdsRef.current;
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
        plugins={[yawPlugin, arrowPlugin]}
        onClick={handleCanvasClick}
      />
    </div>
  );
});

export default Plot;
