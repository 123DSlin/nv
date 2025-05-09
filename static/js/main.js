// Network topology visualization using vis.js
let network = null;
let selectedNodes = {
    source: null,
    target: null,
    loop: null
};
let selectMode = null; // 'source' or 'target' or null
let verificationMode = 'reachability'; // 'reachability' or 'isolation' or 'path'
let hierarchicalEnabled = false;
const groupColors = {
    core: '#2563eb',
    border: '#10b981',
    dist: '#f59e0b',
    host: '#ef4444',
    Unknown: '#757575'
};

function getGroupColor(group) {
    return groupColors[group] || '#757575';
}

function getLevelByGroup(group) {
    if (group === 'core') return 1;
    if (group === 'border') return 2;
    if (group === 'dist') return 3;
    if (group === 'dept' || group === 'host') return 4;
    return 5;
}

function startSelectNode(type) {
    selectMode = type;
    updateVerificationControls();
}

function selectSourceNode(nodeId, label) {
    selectedNodes.source = nodeId;
    updateVerificationControls();
}

function selectTargetNode(nodeId, label) {
    selectedNodes.target = nodeId;
    updateVerificationControls();
}

function clearSourceNode() {
    if (selectedNodes.source) {
        const node = network.body.data.nodes.get(selectedNodes.source);
        node.color = {
            background: '#4CAF50',
            border: '#388E3C'
        };
        network.body.data.nodes.update(node);
        selectedNodes.source = null;
    }
    // 自动进入选择源节点模式
    selectMode = 'source';
    updateVerificationControls();
}

function clearTargetNode() {
    if (selectedNodes.target) {
        const node = network.body.data.nodes.get(selectedNodes.target);
        node.color = {
            background: '#4CAF50',
            border: '#388E3C'
        };
        network.body.data.nodes.update(node);
        selectedNodes.target = null;
    }
    // 自动进入选择目标节点模式
    selectMode = 'target';
    updateVerificationControls();
}

function clearLoopNode() {
    selectedNodes.loop = null;
    updateVerificationControls();
}

function updateNodeColors(nodes) {
    nodes.forEach(node => {
        // 确保 label 不会丢失
        if (!node.label) {
            // 尝试从 network.body.data.nodes 获取原始 label
            const original = network && network.body && network.body.data ? network.body.data.nodes.get(node.id) : null;
            node.label = original && original.label ? original.label : node.id;
        }
        // 路径定位模式下，未生成路径时也要高亮 Source/Target
        if (verificationMode === 'path') {
            if (node.id === selectedNodes.source) {
                node.color = {
                    background: '#e53935', // 深红
                    border: '#b71c1c',
                    highlight: { background: '#e53935', border: '#b71c1c' }
                };
                node.font = { color: '#000', size: 16, bold: true };
            } else if (node.id === selectedNodes.target) {
                node.color = {
                    background: '#ff7043', // 橙红
                    border: '#bf360c',
                    highlight: { background: '#ff7043', border: '#bf360c' }
                };
                node.font = { color: '#000', size: 16, bold: true };
            } else {
                node.color = {
                    background: getGroupColor(node.group),
                    border: '#333',
                    highlight: {
                        background: getGroupColor(node.group),
                        border: '#111'
                    }
                };
                node.font = { color: '#000', size: 14, bold: true };
            }
            nodes.update(node);
            return;
        }
        // 其他模式
        if (node.id === selectedNodes.source) {
            node.color = {
                background: '#e53935', // 深红
                border: '#b71c1c',
                highlight: { background: '#e53935', border: '#b71c1c' }
            };
            node.font = { color: '#000', size: 16, bold: true };
        } else if (node.id === selectedNodes.target) {
            node.color = {
                background: '#ff7043', // 橙红
                border: '#bf360c',
                highlight: { background: '#ff7043', border: '#bf360c' }
            };
            node.font = { color: '#000', size: 16, bold: true };
        } else {
            node.color = {
                background: getGroupColor(node.group),
                border: '#333',
                highlight: {
                    background: getGroupColor(node.group),
                    border: '#111'
                }
            };
            node.font = { color: '#000', size: 14, bold: true };
        }
        nodes.update(node);
    });
}

function initNetwork(container, nodes, edges) {
    // 分组着色+分层
    nodes.forEach(node => {
        node.color = {
            background: getGroupColor(node.group),
            border: '#333',
            highlight: {
                background: getGroupColor(node.group),
                border: '#111'
            }
        };
        if (hierarchicalEnabled) {
            node.level = getLevelByGroup(node.group);
        } else {
            delete node.level;
        }
    });
    const data = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges)
    };
    const options = {
        nodes: {
            shape: 'dot',
            size: 20,
            font: {
                size: 14,
                color: '#000000',
                face: 'arial',
                bold: true
            },
            borderWidth: 2
        },
        edges: {
            width: 2,
            color: {
                color: '#757575',
                highlight: '#FFC107'
            },
            smooth: {
                type: 'curvedCW',
                roundness: 0.3
            },
            font: {
                size: 12,
                color: '#666666'
            }
        },
        physics: hierarchicalEnabled ? false : {
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -120,
                centralGravity: 0.01,
                springLength: 300,
                springConstant: 0.08,
                avoidOverlap: 2
            },
            maxVelocity: 50,
            minVelocity: 0.1,
            stabilization: { iterations: 400 }
        },
        layout: {
            improvedLayout: true,
            hierarchical: {
                enabled: hierarchicalEnabled,
                direction: 'UD',
                sortMethod: 'directed',
                levelSeparation: 150,
                nodeSpacing: 200
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            multiselect: false,
            dragNodes: !hierarchicalEnabled,
            zoomView: true,
            dragView: true
        }
    };
    network = new vis.Network(container, data, options);
    network.on('click', function(params) {
        if (params.nodes.length > 0 && selectMode) {
            const nodeId = params.nodes[0];
            if (selectMode === 'source') {
                selectedNodes.source = nodeId;
            } else if (selectMode === 'target') {
                selectedNodes.target = nodeId;
            } else if (selectMode === 'loop') {
                selectedNodes.loop = nodeId;
            }
            selectMode = null;
            updateNodeColors(network.body.data.nodes);
            updateVerificationControls();
        }
    });
    network.on('oncontext', function(params) {
        params.event.preventDefault();
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            showNodeInfoCard(nodeId, params.pointer.DOM);
        }
    });
    network.fit({
        animation: {
            duration: 1000,
            easingFunction: 'easeInOutQuad'
        }
    });
    setTimeout(() => network.moveTo({position: {x: 0, y: 0}, scale: 1, animation: true}), 1100);
}

function updateVerificationControls() {
    const verifyButton = document.getElementById('verify-action-btn');
    if (!verifyButton) return;
    const sourceLabel = document.getElementById('source-node');
    const targetLabel = document.getElementById('target-node');
    const hint = document.getElementById('node-selection-hint');
    const selectSourceBtn = document.getElementById('select-source-btn');
    const selectTargetBtn = document.getElementById('select-target-btn');
    const clearSourceBtn = document.getElementById('clear-source-btn');
    const clearTargetBtn = document.getElementById('clear-target-btn');
    const loopNodeLabel = document.getElementById('loop-node');
    const selectLoopBtn = document.getElementById('select-loop-node-btn');
    const clearLoopBtn = document.getElementById('clear-loop-node-btn');

    if (selectedNodes.source) {
        const sourceNode = network.body.data.nodes.get(selectedNodes.source);
        if (sourceNode) {
            sourceLabel.textContent = sourceNode.label;
            selectSourceBtn.style.display = 'none';
            clearSourceBtn.style.display = '';
        } else {
            sourceLabel.textContent = '未选择';
            selectSourceBtn.style.display = '';
            clearSourceBtn.style.display = 'none';
            selectedNodes.source = null;
        }
    } else {
        sourceLabel.textContent = '未选择';
        selectSourceBtn.style.display = '';
        clearSourceBtn.style.display = 'none';
    }
    
    if (selectedNodes.target) {
        const targetNode = network.body.data.nodes.get(selectedNodes.target);
        if (targetNode) {
            targetLabel.textContent = targetNode.label;
            selectTargetBtn.style.display = 'none';
            clearTargetBtn.style.display = '';
        } else {
            targetLabel.textContent = '未选择';
            selectTargetBtn.style.display = '';
            clearTargetBtn.style.display = 'none';
            selectedNodes.target = null;
        }
    } else {
        targetLabel.textContent = '未选择';
        selectTargetBtn.style.display = '';
        clearTargetBtn.style.display = 'none';
    }
    
    verifyButton.disabled = !(selectedNodes.source && selectedNodes.target);

    // 动态提示
    if (selectMode === 'source') {
        hint.textContent = '请在拓扑图中点击选择源节点';
    } else if (selectMode === 'target') {
        hint.textContent = '请在拓扑图中点击选择目标节点';
    } else if (!selectedNodes.source) {
        hint.textContent = '请点击"选择"按钮并在拓扑图中选择源节点';
    } else if (!selectedNodes.target) {
        hint.textContent = '请点击"选择"按钮并在拓扑图中选择目标节点';
    } else {
        hint.textContent = '已选择源节点和目标节点，可点击下方按钮进行可达性验证';
    }

    // 新增loop节点选择
    if (loopNodeLabel && selectLoopBtn && clearLoopBtn) {
        if (selectedNodes.loop) {
            const node = network && network.body && network.body.data ? network.body.data.nodes.get(selectedNodes.loop) : null;
            loopNodeLabel.textContent = node ? node.label : '未选择';
            selectLoopBtn.style.display = 'none';
            clearLoopBtn.style.display = '';
        } else {
            loopNodeLabel.textContent = '未选择';
            selectLoopBtn.style.display = '';
            clearLoopBtn.style.display = 'none';
        }
    }
}

// File upload handling
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const networkGraph = document.getElementById('networkGraph');
    const uploadButton = document.getElementById('upload-button');

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const fileInput = document.getElementById('file-input');
        
        if (fileInput.files.length === 0) {
            alert('Please select at least one configuration file');
            return;
        }

        // 只添加 .cfg/.txt 文件
        let validFileCount = 0;
        for (const file of fileInput.files) {
            if (file.name.endsWith('.cfg') || file.name.endsWith('.txt')) {
                formData.append('files', file);
                validFileCount++;
            }
        }
        if (validFileCount === 0) {
            alert('No valid .cfg or .txt files found in your selection.');
            return;
        }

        // Disable upload button and show loading state
        uploadButton.disabled = true;
        uploadButton.textContent = 'Uploading...';

        try {
            console.log('Sending upload request...');
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            console.log('Response status:', response.status);
            const responseText = await response.text();
            console.log('Response text:', responseText);

            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                console.error('Failed to parse response as JSON:', e);
                throw new Error('Invalid server response');
            }

            if (!response.ok) {
                throw new Error(data.detail || 'Upload failed');
            }
            
            // Display topology
            if (data.topology && data.topology.nodes && data.topology.edges) {
                console.log('Received valid topology data');
                // Clear previous network if exists
                if (network) {
                    network.destroy();
                }
                // Initialize network visualization
                initNetwork(networkGraph, data.topology.nodes, data.topology.edges);
                // 重置节点选择
                selectedNodes.source = null;
                selectedNodes.target = null;
                selectedNodes.loop = null;
                updateVerificationControls();
                // Show topology section
                document.querySelector('.topology-section').style.display = 'block';
                // Show verification controls
                document.querySelector('.verification-controls').style.display = 'block';
            } else {
                console.error('Invalid topology data:', data);
                alert('Failed to generate topology from configuration files');
            }

        } catch (error) {
            console.error('Upload error:', error);
            alert('Error: ' + error.message);
        } finally {
            // Re-enable upload button
            uploadButton.disabled = false;
            uploadButton.textContent = 'Upload';
        }
    });

    loadSnapshotList();
    document.getElementById('load-snapshot-btn').addEventListener('click', loadSnapshotTopology);
    // Tab切换事件
    document.getElementById('tab-reachability').addEventListener('click', function() { switchVerificationTab('reachability'); });
    document.getElementById('tab-isolation').addEventListener('click', function() { switchVerificationTab('isolation'); });
    document.getElementById('tab-path').addEventListener('click', function() { switchVerificationTab('path'); });
    document.getElementById('tab-disjoint').addEventListener('click', function() { switchVerificationTab('disjoint'); });
    document.getElementById('tab-loop').addEventListener('click', function() { switchVerificationTab('loop'); });
    // 验证按钮事件
    document.getElementById('verify-action-btn').addEventListener('click', async function() {
        if (selectedNodes.source && selectedNodes.target) {
            const sourceNode = network.body.data.nodes.get(selectedNodes.source);
            const targetNode = network.body.data.nodes.get(selectedNodes.target);
            try {
                let url, body;
                if (verificationMode === 'reachability') {
                    url = '/verify-reachability';
                    body = JSON.stringify({ source: sourceNode.label, target: targetNode.label });
                } else if (verificationMode === 'isolation') {
                    url = '/verify-isolation';
                    body = JSON.stringify({ source: sourceNode.label, target: targetNode.label });
                } else if (verificationMode === 'path') {
                    url = '/locate-path';
                    body = JSON.stringify({ source: sourceNode.label, target: targetNode.label });
                }
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body
                });
                if (!response.ok) throw new Error('Verification failed');
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
    });
    document.getElementById('verify-disjoint-btn').addEventListener('click', async function() {
        if (selectedNodes.source && selectedNodes.target) {
            const sourceNode = network.body.data.nodes.get(selectedNodes.source);
            const targetNode = network.body.data.nodes.get(selectedNodes.target);
            const mode = document.getElementById('disjoint-mode').value;
            try {
                const response = await fetch('/verify-disjoint-paths', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source: sourceNode.label, target: targetNode.label, mode })
                });
                if (!response.ok) throw new Error('Disjoint path verification failed');
                const data = await response.json();
                displayDisjointResults(data);
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
    });
    document.getElementById('verify-loop-btn').addEventListener('click', async function() {
        const mode = document.getElementById('loop-mode').value;
        let body = { mode };
        if (mode === 'node') {
            if (!selectedNodes.loop) {
                alert('请选择检测节点');
                return;
            }
            const node = network.body.data.nodes.get(selectedNodes.loop);
            body.node = node.label;
        }
        try {
            const response = await fetch('/verify-forwarding-loops', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!response.ok) throw new Error('Forwarding loop check failed');
            const data = await response.json();
            displayLoopResults(data);
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });

    document.getElementById('toggle-hierarchical-btn').addEventListener('click', function() {
        hierarchicalEnabled = !hierarchicalEnabled;
        // 重新渲染当前拓扑
        if (network && network.body && network.body.data) {
            let nodes = network.body.data.nodes.get();
            const edges = network.body.data.edges.get();
            // 清除所有节点的 color/font 字段，回到初始状态
            nodes = nodes.map(node => {
                const {id, label, group, level} = node;
                const cleanNode = {id, label, group};
                if (level !== undefined) cleanNode.level = level;
                return cleanNode;
            });
            // 清空选中节点，彻底清除高亮
            selectedNodes.source = null;
            selectedNodes.target = null;
            selectedNodes.loop = null;
            initNetwork(document.getElementById('networkGraph'), nodes, edges);
            updateVerificationControls();
        }
    });

    document.getElementById('clear-highlight-btn').addEventListener('click', function() {
        if (network && network.body && network.body.data) {
            let nodes = network.body.data.nodes.get();
            let edges = network.body.data.edges.get();
            // 清除所有节点的 color/font 字段，回到初始状态
            nodes = nodes.map(node => {
                const {id, label, group, level} = node;
                const cleanNode = {id, label, group};
                if (level !== undefined) cleanNode.level = level;
                return cleanNode;
            });
            // 清除所有边的 color/width 等自定义属性
            edges = edges.map(edge => {
                const {id, from, to, label, title} = edge;
                return {id, from, to, label, title};
            });
            // 深拷贝 nodes/edges，防止 vis-network 复用旧对象
            const nodesCopy = JSON.parse(JSON.stringify(nodes));
            const edgesCopy = JSON.parse(JSON.stringify(edges));
            selectedNodes.source = null;
            selectedNodes.target = null;
            selectedNodes.loop = null;
            // 彻底销毁旧network实例
            network.destroy();
            // 用干净数据重建
            initNetwork(document.getElementById('networkGraph'), nodesCopy, edgesCopy);
            updateVerificationControls();
            // 隐藏结果区
            document.querySelector('.results-section').style.display = 'none';
            document.getElementById('results').innerHTML = '';
        }
    });

    document.getElementById('loop-mode').addEventListener('change', function() {
        if (this.value === 'node') {
            document.getElementById('loop-node-container').style.display = '';
        } else {
            document.getElementById('loop-node-container').style.display = 'none';
        }
    });
});

function switchVerificationTab(mode) {
    verificationMode = mode;
    document.getElementById('tab-reachability').classList.toggle('tab-active', mode === 'reachability');
    document.getElementById('tab-isolation').classList.toggle('tab-active', mode === 'isolation');
    document.getElementById('tab-path').classList.toggle('tab-active', mode === 'path');
    document.getElementById('tab-disjoint').classList.toggle('tab-active', mode === 'disjoint');
    document.getElementById('tab-loop').classList.toggle('tab-active', mode === 'loop');
    let title = 'Verification可达性', btn = '验证可达性';
    if (mode === 'isolation') { title = 'Verification隔离性'; btn = '验证隔离性'; }
    if (mode === 'path') { title = '路径定位'; btn = '路径定位'; }
    if (mode === 'disjoint') { title = '不相交路径'; btn = '验证不相交路径'; }
    if (mode === 'loop') { title = '转发环路检测'; btn = '检测环路'; }
    document.getElementById('verification-title').textContent = title;
    document.getElementById('verify-action-btn').textContent = btn;
    document.getElementById('verify-action-btn').style.display = (mode === 'disjoint' || mode === 'loop') ? 'none' : '';
    document.getElementById('verify-disjoint-btn').style.display = (mode === 'disjoint') ? '' : 'none';
    document.getElementById('verify-loop-btn').style.display = (mode === 'loop') ? '' : 'none';
    document.getElementById('path-strategy-container').style.display = mode === 'path' ? 'block' : 'none';
    document.getElementById('disjoint-mode-container').style.display = mode === 'disjoint' ? 'block' : 'none';
    // 环路检测tab下，检测节点控件始终可见
    if (mode === 'loop') {
        document.getElementById('loop-mode-container').style.display = '';
        document.getElementById('loop-node-container').style.display = '';
        document.getElementById('loop-mode').value = 'global';
        // 隐藏源/目标节点选择
        document.querySelectorAll('.node-info')[0].style.display = 'none';
        document.querySelectorAll('.node-info')[1].style.display = 'none';
    } else {
        document.getElementById('loop-mode-container').style.display = 'none';
        document.getElementById('loop-node-container').style.display = 'none';
        // 显示源/目标节点选择
        document.querySelectorAll('.node-info')[0].style.display = '';
        document.querySelectorAll('.node-info')[1].style.display = '';
    }
    updateVerificationControls();
    document.querySelector('.results-section').style.display = 'none';
    document.getElementById('results').innerHTML = '';
}

// 高亮拓扑图上的最佳路径
function highlightBestPathOnGraph(bestPath) {
    if (!network || !bestPath || bestPath.length < 2) return;
    const allNodes = network.body.data.nodes.get();
    const allEdges = network.body.data.edges.get();
    // 先重置
    allNodes.forEach(node => {
        node.color = {
            background: getGroupColor(node.group),
            border: '#333',
            highlight: {
                background: getGroupColor(node.group),
                border: '#111'
            }
        };
        node.font = { color: '#000', size: 14, bold: true };
        network.body.data.nodes.update(node);
    });
    allEdges.forEach(edge => {
        network.body.data.edges.update({
            id: edge.id,
            color: {
                color: '#757575',
                highlight: '#FFC107'
            },
            width: 2
        });
    });
    // 路径节点高亮（浅红）
    bestPath.forEach(label => {
        const node = allNodes.find(n => n.label === label);
        if (node) {
            node.color = {
                background: '#ffb3b3', // 浅红
                border: '#e53935'
            };
            node.font = { color: '#000', size: 14, bold: true };
            network.body.data.nodes.update(node);
        }
    });
    // 高亮路径上的边（红色）
    for (let i = 0; i < bestPath.length - 1; i++) {
        const fromLabel = bestPath[i];
        const toLabel = bestPath[i + 1];
        const fromNode = allNodes.find(n => n.label === fromLabel);
        const toNode = allNodes.find(n => n.label === toLabel);
        if (fromNode && toNode) {
            const edge = allEdges.find(e =>
                (e.from === fromNode.id && e.to === toNode.id) ||
                (e.from === toNode.id && e.to === fromNode.id)
            );
            if (edge) {
                network.body.data.edges.update({
                    id: edge.id,
                    color: {
                        color: '#e53935', // 红色
                        highlight: '#e53935'
                    },
                    width: 5
                });
            }
        }
    }
    // 最后再高亮 Source/Target 节点，确保优先级最高
    if (bestPath.length > 0) {
        const sourceNode = allNodes.find(n => n.label === bestPath[0]);
        if (sourceNode) {
            sourceNode.color = {
                background: '#e53935', // 深红
                border: '#b71c1c',
                highlight: { background: '#e53935', border: '#b71c1c' }
            };
            sourceNode.font = { color: '#000', size: 16, bold: true };
            network.body.data.nodes.update(sourceNode);
        }
    }
    if (bestPath.length > 1) {
        const targetNode = allNodes.find(n => n.label === bestPath[bestPath.length-1]);
        if (targetNode) {
            targetNode.color = {
                background: '#ff7043', // 橙红
                border: '#bf360c',
                highlight: { background: '#ff7043', border: '#bf360c' }
            };
            targetNode.font = { color: '#000', size: 16, bold: true };
            network.body.data.nodes.update(targetNode);
        }
    }
}

function clearGraphHighlight() {
    if (!network) return;
    const allNodes = network.body.data.nodes.get();
    allNodes.forEach(node => {
        network.body.data.nodes.update({
            id: node.id,
            color: {
                background: '#4CAF50',
                border: '#388E3C'
            }
        });
    });
    const allEdges = network.body.data.edges.get();
    allEdges.forEach(edge => {
        network.body.data.edges.update({
            id: edge.id,
            color: {
                color: '#757575',
                highlight: '#FFC107'
            },
            width: 2
        });
    });
}

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    let html = '<div class="results-container">';
    if (data.report && data.report.analysis && data.report.analysis.reachability) {
        // 可达性验证
        const report = data.report;
        html += `
        <div class="card result-card">
            <h3>Reachability Verification</h3>
            <div class="status-badge status-${report.summary.overall_status.toLowerCase()}">
                ${report.summary.overall_status}
            </div>
            <div class="verification-details">
                <div class="detail-item">
                    <span class="detail-label">Source Node:</span>
                    <span class="detail-value">${report.analysis.reachability.details.source}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Target Node:</span>
                    <span class="detail-value">${report.analysis.reachability.details.target}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value ${report.analysis.reachability.details.reachable ? 'status-pass' : 'status-fail'}">
                        ${report.analysis.reachability.details.reachable ? 'Reachable' : 'Not Reachable'}
                    </span>
                </div>
            </div>
        `;
        if (report.analysis.reachability.details.reachable && report.analysis.reachability.details.path) {
            html += `
                <div class="path-container">
                    <h4>Path Details</h4>
                    <div class="path-nodes">
                        ${report.analysis.reachability.details.path.map((node, index) => `
                            <div class="path-node">
                                <span class="node-number">${index + 1}</span>
                                <span class="node-name">${node}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            // 先清除高亮再高亮可达路径
            clearGraphHighlight();
            highlightBestPathOnGraph(report.analysis.reachability.details.path);
        }
        if (!report.analysis.reachability.details.reachable) {
            html += `
                <div class="reason-container">
                    <h4>Reason</h4>
                    <p class="reason-text">${report.analysis.reachability.details.reason}</p>
                </div>
            `;
        }
        html += '</div>';
        clearGraphHighlight();
        // 保持Source/Target高亮
        updateNodeColors(network.body.data.nodes);
    } else if (data.report && data.report.analysis && data.report.analysis.isolation) {
        // 隔离性验证
        const report = data.report;
        html += `
        <div class="card result-card">
            <h3>Isolation Verification</h3>
            <div class="status-badge status-${report.summary.overall_status.toLowerCase()}">
                ${report.summary.overall_status}
            </div>
            <div class="verification-details">
                <div class="detail-item">
                    <span class="detail-label">Source Node:</span>
                    <span class="detail-value">${report.analysis.isolation.details.source}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Target Node:</span>
                    <span class="detail-value">${report.analysis.isolation.details.target}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value ${report.analysis.isolation.details.isolated ? 'status-pass' : 'status-fail'}">
                        ${report.analysis.isolation.details.isolated ? 'Isolated' : 'Not Isolated'}
                    </span>
                </div>
            </div>
        `;
        if (!report.analysis.isolation.details.isolated && report.analysis.isolation.details.path) {
            html += `
                <div class="path-container">
                    <h4>Path (Not Isolated)</h4>
                    <div class="path-nodes">
                        ${report.analysis.isolation.details.path.map((node, index) => `
                            <div class="path-node">
                                <span class="node-number">${index + 1}</span>
                                <span class="node-name">${node}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        if (report.analysis.isolation.details.isolated && report.analysis.isolation.details.reason) {
            html += `
                <div class="reason-container">
                    <h4>Reason</h4>
                    <p class="reason-text">${report.analysis.isolation.details.reason}</p>
                </div>
            `;
        }
        html += '</div>';
        clearGraphHighlight();
        // 保持Source/Target高亮
        updateNodeColors(network.body.data.nodes);
    } else if (verificationMode === 'path' && data.status === 'success') {
        clearGraphHighlight();
        const pathStrategy = document.getElementById('path-strategy').value;
        let strategyName = '最短路径';
        switch(pathStrategy) {
            case 'core_preferred': strategyName = '优先核心设备'; break;
            case 'border_preferred': strategyName = '优先边界设备'; break;
            case 'redundant': strategyName = '冗余路径'; break;
        }
        
        html += `
        <div class="card result-card">
            <h3>路径定位</h3>
            <div class="verification-details">
                <div class="detail-item">
                    <span class="detail-label">Source Node:</span>
                    <span class="detail-value">${data.best_path && data.best_path.length > 0 ? data.best_path[0] : ''}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Target Node:</span>
                    <span class="detail-value">${data.best_path && data.best_path.length > 0 ? data.best_path[data.best_path.length-1] : ''}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">选择策略:</span>
                    <span class="detail-value">${strategyName}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">最佳路径:</span>
                    <span class="detail-value">
                        ${data.found && data.best_path && data.best_path.length > 0 ?
                            data.best_path.map((node, index) => `<span class=\"node-name\">${index > 0 ? ' → ' : ''}${node}</span>`).join('')
                            : '<span style=\"color:#f44336\">无可用路径</span>'}
                    </span>
                </div>
            </div>
            ${(data.paths && data.paths.length > 0) ? `
            <div class=\"all-paths-card\" style=\"margin-top:1.5rem;\">
                <h4>所有可达路径</h4>
                <div class=\"path-nodes\">
                    ${data.paths.map((path, idx) => `
                        <div class=\"path-node\" style=\"background:${JSON.stringify(path)===JSON.stringify(data.best_path)?'#e6fff5':'#f5f5f5'};font-weight:${JSON.stringify(path)===JSON.stringify(data.best_path)?'bold':'normal'};\">
                            <span class=\"node-number\">${idx + 1}</span>
                            ${path.map((node, i) => `<span class=\"node-name\">${i > 0 ? ' → ' : ''}${node}</span>`).join('')}
                            <button class=\"btn btn-primary\" style=\"margin-left:1em;\" onclick=\"window.toggleHighlightPath('path',${idx})\">高亮</button>
                            ${JSON.stringify(path)===JSON.stringify(data.best_path)?'<span style=\"color:#10b981;margin-left:1em;\">最佳</span>':''}
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            <div class=\"strategy-hint\" style=\"margin-top:1.5rem;padding:1rem;background:#f8fafc;border-radius:8px;color:#1e40af;font-size:1rem;\">
                <b>策略选择建议：</b><br>
                需要最快响应时选择最短路径<br>
                需要高可靠性时选择优先核心设备的路径<br>
                需要负载均衡时选择冗余路径<br>
                需要特定网络策略时选择优先边界设备的路径
            </div>
        </div>
        `;
        // 高亮切换逻辑
        if (!window._highlightState) window._highlightState = {};
        window.toggleHighlightPath = function(type, idx) {
            if (!window._highlightState[type]) window._highlightState[type] = {current: null};
            if (window._highlightState[type].current === idx) {
                clearGraphHighlight();
                window._highlightState[type].current = null;
            } else {
                clearGraphHighlight();
                highlightBestPathOnGraph(data.paths[idx]);
                window._highlightState[type].current = idx;
            }
        };
    }
    html += '</div>';
    resultsDiv.innerHTML = html;
    document.querySelector('.results-section').style.display = 'block';
}

function showError(message) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="alert alert-danger">
            Error: ${message}
        </div>
    `;
}

// 快照选择与加载
async function loadSnapshotList() {
    const select = document.getElementById('snapshot-select');
    select.innerHTML = '';
    try {
        const res = await fetch('/snapshots');
        const data = await res.json();
        if (data.snapshots && data.snapshots.length > 0) {
            data.snapshots.reverse().forEach(snap => {
                const option = document.createElement('option');
                option.value = snap.id;
                option.text = `${snap.timestamp} (共${snap.files.length}个文件)`;
                option.title = snap.files.map(f => f.split('_').slice(1).join('_')).join(', ');
                select.appendChild(option);
            });
        } else {
            const option = document.createElement('option');
            option.value = '';
            option.text = '暂无快照';
            select.appendChild(option);
        }
    } catch (e) {
        select.innerHTML = '<option value="">加载失败</option>';
    }
}

async function loadSnapshotTopology() {
    const select = document.getElementById('snapshot-select');
    const snapshotId = select.value;
    if (!snapshotId) return;
    const networkGraph = document.getElementById('networkGraph');
    try {
        const res = await fetch(`/load-snapshot/${snapshotId}`);
        const data = await res.json();
        if (data.status === 'success' && data.topology && data.topology.nodes && data.topology.edges) {
            if (network) network.destroy();
            initNetwork(networkGraph, data.topology.nodes, data.topology.edges);
            // 重置节点选择
            selectedNodes.source = null;
            selectedNodes.target = null;
            selectedNodes.loop = null;
            updateVerificationControls();
            document.querySelector('.topology-section').style.display = 'block';
            document.querySelector('.verification-controls').style.display = 'block';
        } else {
            alert('快照拓扑加载失败');
        }
    } catch (e) {
        alert('快照拓扑加载失败: ' + e.message);
    }
}

async function verifyPath() {
    const source = document.getElementById('source-node').textContent;
    const target = document.getElementById('target-node').textContent;
    const pathStrategy = document.getElementById('path-strategy').value;
    
    try {
        const response = await fetch('/locate-path', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source: source,
                target: target,
                path_strategy: pathStrategy
            }),
        });
        
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error:', error);
        alert('验证失败: ' + error.message);
    }
}

function displayDisjointResults(data) {
    const resultsDiv = document.getElementById('results');
    let html = '<div class="results-container">';
    html += `<div class="card result-card">
        <h3>不相交路径验证</h3>
        <div class="verification-details">
            <div class="detail-item">
                <span class="detail-label">类型:</span>
                <span class="detail-value">${data.type === 'node' ? '节点不相交' : '边不相交'}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">结果:</span>
                <span class="detail-value">${data.found ? '存在两条不相交路径' : '不存在两条不相交路径'}</span>
            </div>
        </div>`;
    if (data.paths && data.paths.length > 0) {
        html += `<div class="all-paths-card" style="margin-top:1.5rem;">
            <h4>所有不相交路径</h4>
            <div class="path-nodes">`;
        data.paths.forEach((path, idx) => {
            html += `<div class="path-node" style="background:#f5f5f5;">
                <span class="node-number">${idx + 1}</span>
                ${path.map((node, i) => `<span class="node-name">${i > 0 ? ' → ' : ''}${node}</span>`).join('')}
                <button class="btn btn-primary" style="margin-left:1em;" onclick="window.toggleHighlightPath('disjoint',${idx})">高亮</button>
            </div>`;
        });
        html += `</div></div>`;
    }
    html += '</div></div>';
    resultsDiv.innerHTML = html;
    document.querySelector('.results-section').style.display = 'block';
    // 高亮切换逻辑
    if (!window._highlightState) window._highlightState = {};
    window.toggleHighlightPath = function(type, idx) {
        if (!window._highlightState[type]) window._highlightState[type] = {current: null};
        if (window._highlightState[type].current === idx) {
            clearGraphHighlight();
            window._highlightState[type].current = null;
        } else {
            clearGraphHighlight();
            highlightBestPathOnGraph(data.paths[idx]);
            window._highlightState[type].current = idx;
        }
    };
}

function displayLoopResults(data) {
    console.log('displayLoopResults called', data);
    const resultsDiv = document.getElementById('results');
    let html = '<div class="results-container">';
    html += `<div class="card result-card">
        <h3>转发环路检测</h3>
        <div class="verification-details">
            <div class="detail-item">
                <span class="detail-label">结果:</span>
                <span class="detail-value">${data.status === 'FAILED' && data.details && data.details.loops && data.details.loops.length > 0 ? '存在环路' : '未检测到环路'}</span>
            </div>
        </div>`;
    // 调试输出原始数据
    html += `<pre style="background:#f8fafc;color:#1e40af;font-size:12px;max-height:200px;overflow:auto;">${JSON.stringify(data, null, 2)}</pre>`;
    if (data.status === 'FAILED' && data.details && data.details.loops && data.details.loops.length > 0) {
        html += `<div class="all-paths-card" style="margin-top:1.5rem;">
            <h4>所有检测到的环路</h4>
            <div class="path-nodes">`;
        data.details.loops.forEach((loop, idx) => {
            html += `<div class="path-node" style="background:#f5f5f5;">
                <span class="node-number">${idx + 1}</span>
                ${Array.isArray(loop) ? loop.map((node, i) => `<span class="node-name">${i > 0 ? ' → ' : ''}${node}</span>`).join('') : String(loop)}
                <button class="btn btn-primary" style="margin-left:1em;" onclick="window.toggleHighlightPath('loop',${idx})">高亮</button>
            </div>`;
        });
        html += `</div></div>`;
    }
    html += '</div></div>';
    resultsDiv.innerHTML = html;
    document.querySelector('.results-section').style.display = 'block';
    // 高亮切换逻辑
    if (!window._highlightState) window._highlightState = {};
    window.toggleHighlightPath = function(type, idx) {
        if (!window._highlightState[type]) window._highlightState[type] = {current: null};
        if (window._highlightState[type].current === idx) {
            clearGraphHighlight();
            window._highlightState[type].current = null;
        } else {
            clearGraphHighlight();
            if (data.details && data.details.loops && data.details.loops[idx]) {
                highlightBestPathOnGraph(data.details.loops[idx]);
            }
            window._highlightState[type].current = idx;
        }
    };
}

// 右键节点弹出详细信息卡片
function showNodeInfoCard(nodeId, position) {
    const node = network.body.data.nodes.get(nodeId);
    fetch(`/node-info?label=${encodeURIComponent(node.label)}`)
        .then(res => res.json())
        .then(data => {
            let html = `
              <div class="node-info-card">
                <b>Device:</b> ${data.label || ''}<br>
                <b>Type:</b> ${data.group || ''}<br>
                <b>Interfaces:</b><br>
                <ul>${(data.interfaces||[]).map(i=>`<li>${i.name || ''} ${(i.ip_address ? '('+i.ip_address+')' : '')}</li>`).join('')}</ul>
                <b>BGP Peers:</b> ${(data.bgp_peers||[]).join(', ')}<br>
                <b>OSPF Peers:</b> ${(data.ospf_peers||[]).join(', ')}<br>
                <b>ACLs:</b> <ul>${(data.acls||[]).map(a=>`<li>${a}</li>`).join('')}</ul>
              </div>
            `;
            let card = document.getElementById('node-info-popup');
            if (!card) {
                card = document.createElement('div');
                card.id = 'node-info-popup';
                card.style.position = 'absolute';
                card.style.zIndex = 1000;
                document.body.appendChild(card);
            }
            card.innerHTML = html;
            card.style.left = position.x + 'px';
            card.style.top = position.y + 'px';
            card.style.display = 'block';
            // 点击其他地方关闭
            setTimeout(() => {
                document.addEventListener('click', function hideCard() {
                    card.style.display = 'none';
                    document.removeEventListener('click', hideCard);
                });
            }, 10);
        });
}

function renderLoopDetectionResult(result) {
    const resultDiv = document.getElementById('verification-result');
    resultDiv.innerHTML = '';
    if (result.status === 'PASSED') {
        resultDiv.innerHTML = '<div class="result-card success">未检测到环路</div>';
    } else if (result.status === 'FAILED' && result.details && result.details.loops && result.details.loops.length > 0) {
        let html = '<div class="result-card fail"><b>检测到环路：</b><ul>';
        result.details.loops.forEach(loop => {
            html += `<li>${loop.join(' → ')}</li>`;
        });
        html += '</ul></div>';
        resultDiv.innerHTML = html;
    } else {
        resultDiv.innerHTML = '<div class="result-card fail">检测失败或无数据</div>';
    }
}

// 快照管理弹窗逻辑
function showSnapshotMgrModal() {
    const modal = document.getElementById('snapshot-mgr-modal');
    const listDiv = document.getElementById('snapshot-mgr-list');
    listDiv.innerHTML = '<div style="text-align:center;padding:2em;">加载中...</div>';
    modal.style.display = 'flex';
    fetch('/snapshots').then(res => res.json()).then(data => {
        if (!data.snapshots || data.snapshots.length === 0) {
            listDiv.innerHTML = '<div style="text-align:center;color:#888;">暂无快照</div>';
            return;
        }
        // 按timestamp分组
        const batchMap = {};
        data.snapshots.forEach(snap => {
            if (!batchMap[snap.timestamp]) batchMap[snap.timestamp] = [];
            batchMap[snap.timestamp].push(snap);
        });
        let html = '';
        Object.keys(batchMap).sort((a,b)=>b.localeCompare(a)).forEach(ts => {
            const snaps = batchMap[ts];
            html += `<div class="batch-group" style="border:1px solid #e5e7eb;border-radius:6px;margin-bottom:1.2em;padding:1em 1.2em;">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <div><b>批次时间：</b>${ts} <span style="color:#888;font-size:13px;">（${snaps.length}个快照）</span></div>
                    <div>
                        <button class="verify-btn" onclick="viewBatchSnapshots('${ts}')">查看详情</button>
                        <button class="verify-btn" onclick="deleteBatchSnapshots('${ts}', this)">批量删除</button>
                    </div>
                </div>
            </div>`;
        });
        listDiv.innerHTML = html;
    });
}
window.showSnapshotMgrModal = showSnapshotMgrModal;

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('snapshot-mgr-btn').onclick = showSnapshotMgrModal;
    document.getElementById('close-snapshot-mgr').onclick = function() {
        document.getElementById('snapshot-mgr-modal').style.display = 'none';
    };
});

// 查看批次详情
function findConfigForFile(configs, fname) {
    const shortName = fname.split('/').pop();
    if (configs[fname]) return configs[fname];
    if (configs[shortName]) return configs[shortName];
    for (const key in configs) {
        if (key.includes(shortName)) return configs[key];
    }
    return null;
}

// 添加全局内容弹窗
if (!document.getElementById('snapshot-content-modal')) {
    const modal = document.createElement('div');
    modal.id = 'snapshot-content-modal';
    modal.style = 'display:none;position:fixed;z-index:99999;left:0;top:0;width:100vw;height:100vh;background:rgba(0,0,0,0.3);align-items:center;justify-content:center;';
    modal.innerHTML = `<div class="modal-content" style="background:#fff;padding:2rem 2.5rem;border-radius:8px;min-width:600px;max-width:90vw;max-height:80vh;overflow:auto;box-shadow:0 8px 32px rgba(0,0,0,0.18);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
            <h2 style="margin:0;font-size:1.2em;">文件内容</h2>
            <button id="close-snapshot-content-modal" style="font-size:1.5rem;background:none;border:none;cursor:pointer;">×</button>
        </div>
        <div id="snapshot-content-modal-body"></div>
    </div>`;
    document.body.appendChild(modal);
    document.getElementById('close-snapshot-content-modal').onclick = function() {
        modal.style.display = 'none';
    };
}

window.viewBatchSnapshots = function(ts) {
    // 先收起所有已展开详情
    document.querySelectorAll('.batch-detail-area').forEach(e => e.remove());
    // 找到当前批次卡片
    const batchCard = Array.from(document.querySelectorAll('.batch-group')).find(card => card.innerHTML.includes(ts));
    if (!batchCard) return;
    // 创建详情区容器
    const detailDiv = document.createElement('div');
    detailDiv.className = 'batch-detail-area';
    detailDiv.style = 'margin-top:1em;padding:1.5em 1em;background:#f8fafc;border-radius:8px;border:1px solid #e5e7eb;';
    detailDiv.innerHTML = '<div style="text-align:center;padding:2em;">加载中...</div>';
    batchCard.parentNode.insertBefore(detailDiv, batchCard.nextSibling);
    fetch(`/snapshots/batch/${ts}`).then(res=>res.json()).then(data=>{
        if (!data.snapshots || data.snapshots.length === 0) {
            detailDiv.innerHTML = '<div style="color:#888;">该批次暂无快照</div>';
            return;
        }
        // 只展示第一个快照（通常一个批次只有一个快照）
        const snap = data.snapshots[0];
        const files = snap.files || [];
        const configs = snap.content && snap.content.configs ? snap.content.configs : {};
        let html = `<button class="verify-btn" style="margin-bottom:1em;" onclick="this.closest('.batch-detail-area').remove()">关闭详情</button>`;
        if (files.length === 0) {
            html += '<div style="color:#888;">该快照下无文件</div>';
            detailDiv.innerHTML = html;
            return;
        }
        html += '<div style="display:flex;gap:2em;">';
        // 文件名列表
        html += '<div style="min-width:260px;">';
        html += '<div style="font-weight:bold;margin-bottom:0.5em;">文件列表</div>';
        html += '<ul id="snapshot-file-list" style="list-style:none;padding:0;">';
        files.forEach((fname, idx) => {
            const shortName = fname.split('/').pop();
            html += `<li style="margin-bottom:0.5em;display:flex;align-items:center;justify-content:space-between;gap:0.5em;">
                <span class="snapshot-file-label" data-fname="${fname}" style="color:#2563eb;cursor:pointer;text-decoration:underline;">${shortName}</span>
                <div style="display:flex;gap:0.5em;">
                    <button class="verify-btn" style="padding:0.2em 0.8em;font-size:0.9em;" onclick="window._showSnapshotFileContent && window._showSnapshotFileContent('${fname}', this)">查看</button>
                    <button class="verify-btn" style="padding:0.2em 0.8em;font-size:0.9em;" onclick="deleteSingleSnapshot('${snap.id}','${fname}',this)">删除</button>
                </div>
            </li>`;
        });
        html += '</ul></div>';
        // 文件内容区
        html += '<div style="flex:1;min-width:0;">';
        html += '<div id="snapshot-file-content" style="background:#f8fafc;color:#1e40af;font-size:13px;max-height:60vh;overflow:auto;border-radius:6px;padding:1em;"></div>';
        html += '</div>';
        html += '</div>';
        detailDiv.innerHTML = html;
        // 绑定"查看"按钮事件，弹窗显示内容
        window._showSnapshotFileContent = function(fname, btn) {
            let config = findConfigForFile(configs, fname);
            const modal = document.getElementById('snapshot-content-modal');
            const modalBody = document.getElementById('snapshot-content-modal-body');
            if (config) {
                modalBody.innerHTML = renderConfigContent(config);
            } else {
                modalBody.innerHTML = '';
            }
            modal.style.display = 'flex';
        };
        // 也允许点击文件名高亮内容
        detailDiv.querySelectorAll('.snapshot-file-label').forEach(label => {
            label.onclick = function(e) {
                const fname = this.getAttribute('data-fname');
                window._showSnapshotFileContent(fname);
            };
        });
    });
};

// 查看单个快照内容
window.viewSnapshotDetail = function(snapId) {
    const listDiv = document.getElementById('snapshot-mgr-list');
    listDiv.innerHTML = '<div style="text-align:center;padding:2em;">加载中...</div>';
    fetch(`/snapshot/${snapId}`).then(res=>res.json()).then(data=>{
        // 展示文件列表和内容
        const files = data.files || [];
        const configs = data.configs || {};
        let html = `<button class="verify-btn" style="margin-bottom:1em;" onclick="showSnapshotMgrModal()">返回批次列表</button>`;
        if (files.length === 0) {
            html += '<div style="color:#888;">该快照下无文件</div>';
            listDiv.innerHTML = html;
            return;
        }
        html += '<div style="display:flex;gap:2em;">';
        // 文件名列表
        html += '<div style="min-width:220px;">';
        html += '<div style="font-weight:bold;margin-bottom:0.5em;">文件列表</div>';
        html += '<ul id="snapshot-file-list" style="list-style:none;padding:0;">';
        files.forEach((fname, idx) => {
            const shortName = fname.split('/').pop();
            html += `<li style="margin-bottom:0.5em;"><a href="#" class="snapshot-file-link" data-fname="${fname}" style="color:#2563eb;text-decoration:underline;cursor:pointer;">${shortName}</a></li>`;
        });
        html += '</ul></div>';
        // 文件内容区
        html += '<div style="flex:1;min-width:0;">';
        html += '<div id="snapshot-file-content" style="background:#f8fafc;color:#1e40af;font-size:13px;max-height:60vh;overflow:auto;border-radius:6px;padding:1em;">';
        // 默认显示第一个文件内容，增强查找
        const firstFile = files[0];
        let config = findConfigForFile(configs, firstFile);
        if (config) {
            html += renderConfigContent(config);
        } else {
            html += '';
        }
        html += '</div></div>';
        html += '</div>';
        listDiv.innerHTML = html;
        // 绑定点击事件，增强查找
        document.querySelectorAll('.snapshot-file-link').forEach(link => {
            link.onclick = function(e) {
                e.preventDefault();
                const fname = this.getAttribute('data-fname');
                const contentDiv = document.getElementById('snapshot-file-content');
                let config = findConfigForFile(configs, fname);
                if (config) {
                    contentDiv.innerHTML = renderConfigContent(config);
                } else {
                    contentDiv.innerHTML = '';
                }
            };
        });
    });
};

// 渲染配置内容，优先显示raw_config，否则显示全部内容
function renderConfigContent(configObj) {
    if (configObj.raw_config && configObj.raw_config.trim()) {
        return `<pre>${escapeHtml(configObj.raw_config)}</pre>`;
    } else {
        return `<pre>${escapeHtml(JSON.stringify(configObj, null, 2))}</pre>`;
    }
}

// 防止XSS
function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, function (s) {
        return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[s]);
    });
}

// 批量删除快照
window.deleteBatchSnapshots = function(ts, btn) {
    if (!confirm('确定要批量删除该批次下的所有快照吗？')) return;
    btn.disabled = true;
    btn.textContent = '删除中...';
    fetch(`/snapshots/batch/${ts}`, {method:'DELETE'}).then(res=>res.json()).then(data=>{
        alert(`已删除：${data.deleted.length} 个快照`);
        showSnapshotMgrModal();
    }).catch(()=>{
        alert('删除失败');
        btn.disabled = false;
        btn.textContent = '批量删除';
    });
};
// 删除单个快照
window.deleteSingleSnapshot = function(snapId, fname, btn) {
    if (!confirm('确定要删除该快照吗？')) return;
    btn.disabled = true;
    btn.textContent = '删除中...';
    fetch(`/snapshot/${snapId}`, {method:'DELETE'}).then(res=>res.json()).then(data=>{
        alert('删除成功');
        showSnapshotMgrModal();
    }).catch(()=>{
        alert('删除失败');
        btn.disabled = false;
        btn.textContent = '删除';
    });
}; 