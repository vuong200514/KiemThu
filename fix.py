import sys 

with open ("d:\\Download\\chien\\reporter.py","r",encoding ="utf-8")as f :
    lines =f .readlines ()


end_idx =-1 
for i ,line in enumerate (lines ):
    if line .strip ()=="'''":

        if i >0 and "</html>"in lines [i -1 ]:
            end_idx =i 
            break 

if end_idx !=-1 :
    correct_lines =lines [:end_idx +1 ]

    correct_lines .extend ([
    "\n",
    "    html = html_template.replace('{{DATA}}', json_text)\n",
    "    html = html.replace('{{PYTEST_OUTPUT}}', safe_pytest)\n",
    "    html = html.replace('{{FNAME}}', os.path.basename(source_file))\n",
    "\n",
    "    with open(html_path, 'w', encoding='utf-8') as hf:\n",
    "        hf.write(html)\n",
    "\n",
    "    return html_path\n",
    "\n\n"
    ])


    rest ="""def generate_summary_report(reports_info: List[Dict], out_dir: str = 'reports') -> str:
    \"\"\"Generate a master summary report with a combined interactive network graph.\"\"\"
    import datetime
    import json
    os.makedirs(out_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    html_path = os.path.join(out_dir, f"summary_report_{timestamp}.html")
    
    # Combined data
    master_nodes = []
    master_edges = []
    master_tests = {}
    master_pytest_output = ""
    
    # Process each file to build the master graph
    for info in reports_info:
        fname = info.get('file_name', 'Unknown')
        status = info.get('status', 'unknown')
        
        if status == 'success':
            # Construct paths (they are in the root directory, not temp/)
            source_path = f"uploaded_{fname}"
            test_path = f"test_{fname}"
            
            if os.path.exists(source_path):
                # Analyze this file
                nodes, edges, functions_map, module_name = analyze_calls(source_path)
                
                tests = {}
                if os.path.exists(test_path):
                    tests = extract_tests(test_path, functions_map, module_name)
                    
                mapping = map_tests_to_functions(tests, functions_map)
                
                # We need the pytest output for this file to calculate statuses
                file_pytest_output = info.get('exec_output', '')
                statuses = parse_pytest_output(file_pytest_output)
                
                master_pytest_output += f"\\n===================== {fname} =====================\\n"
                master_pytest_output += file_pytest_output + "\\n"
                
                # Prefix to avoid collisions between files
                prefix = f"[{fname}] "
                
                # Add nodes
                for n in nodes:
                    new_n = n.copy()
                    new_n['id'] = prefix + n['id']
                    
                    # Compute status for this node
                    tests_for_node = mapping.get(n['id'], [])
                    new_n['tests'] = [prefix + t for t in tests_for_node]
                    new_n['test_count'] = len(tests_for_node)
                    
                    st_counts = {}
                    for tid in tests_for_node:
                        short = tid.split('::')[-1] if '::' in tid else tid
                        st = statuses.get(tid) or statuses.get(short) or 'unknown'
                        st_counts[st] = st_counts.get(st, 0) + 1
                    
                    new_n['status_counts'] = st_counts
                    master_nodes.append(new_n)
                    
                # Add edges
                for e in edges:
                    new_e = e.copy()
                    new_e['from'] = prefix + e['from']
                    new_e['to'] = prefix + e['to']
                    master_edges.append(new_e)
                    
                # Add tests
                for tid, tinfo in tests.items():
                    new_tid = prefix + tid
                    new_tinfo = tinfo.copy()
                    new_tinfo['calls'] = [prefix + c for c in tinfo.get('calls', [])]
                    master_tests[new_tid] = new_tinfo

    # Prepare JSON data for JS
    data_dict = {
        'nodes': master_nodes,
        'edges': master_edges,
        'tests': master_tests,
        'pytest_output': master_pytest_output
    }
    
    data_json = json.dumps(data_dict, ensure_ascii=False)

    html = f'''<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <title>Báo Cáo Tổng Hợp Tương Tác</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    :root {{
      --bg-color: #f8fafc;
      --panel-bg: #ffffff;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --border-color: #e2e8f0;
      --primary: #3b82f6;
      --success-bg: #dcfce7;
      --success-text: #166534;
      --danger-bg: #fee2e2;
      --danger-text: #991b1b;
      --warning-bg: #fef3c7;
      --warning-text: #b45309;
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Inter', sans-serif; background-color: var(--bg-color); color: var(--text-main); margin: 0; display: flex; height: 100vh; overflow: hidden; }}
    
    #network-container {{ flex: 1; background: #fff; position: relative; }}
    #network {{ width: 100%; height: 100%; }}
    
    #sidebar {{ width: 450px; background: var(--panel-bg); border-left: 1px solid var(--border-color); display: flex; flex-direction: column; box-shadow: -4px 0 15px rgba(0,0,0,0.03); z-index: 10; }}
    .header {{ padding: 25px; border-bottom: 1px solid var(--border-color); background: #f8fafc; }}
    .header h2 {{ margin: 0; font-size: 1.25rem; color: #1e293b; display: flex; align-items: center; gap: 10px; }}
    .header p {{ margin: 8px 0 0; font-size: 0.9rem; color: var(--text-muted); line-height: 1.5; }}
    
    .content {{ flex: 1; overflow-y: auto; padding: 25px; }}
    .content h3 {{ margin-top: 0; font-size: 1.1rem; color: #334155; padding-bottom: 10px; border-bottom: 2px solid #f1f5f9; }}
    
    .info-grid {{ display: grid; grid-template-columns: auto 1fr; gap: 12px 15px; margin: 20px 0; font-size: 0.95rem; align-items: center; }}
    .info-label {{ color: var(--text-muted); font-weight: 500; }}
    
    .badge {{ display: inline-flex; align-items: center; padding: 6px 12px; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; margin-right: 8px; margin-bottom: 8px; }}
    .ok {{ background: var(--success-bg); color: var(--success-text); }}
    .bad {{ background: var(--danger-bg); color: var(--danger-text); }}
    .unk {{ background: var(--warning-bg); color: var(--warning-text); }}
    
    .test-list {{ list-style: none; padding: 0; margin: 0; }}
    .test-list li {{ background: #f8fafc; border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
    .test-list b {{ display: block; color: #1e293b; margin-bottom: 8px; word-break: break-all; }}
    .test-list pre {{ background: #1e293b; color: #f8fafc; padding: 12px; border-radius: 6px; font-size: 0.85rem; overflow-x: auto; margin: 10px 0 0; line-height: 1.4; border: 1px solid #0f172a; }}
    
    .status-passed {{ color: #166534; font-weight: bold; font-size: 0.85rem; background: #dcfce7; padding: 2px 8px; border-radius: 4px; display: inline-block; }}
    .status-failed {{ color: #991b1b; font-weight: bold; font-size: 0.85rem; background: #fee2e2; padding: 2px 8px; border-radius: 4px; display: inline-block; }}
    .status-error {{ color: #991b1b; font-weight: bold; font-size: 0.85rem; background: #fecaca; padding: 2px 8px; border-radius: 4px; display: inline-block; }}
    .status-unknown {{ color: #b45309; font-weight: bold; font-size: 0.85rem; background: #fef3c7; padding: 2px 8px; border-radius: 4px; display: inline-block; }}
    
    .legend {{ position: absolute; bottom: 30px; left: 30px; background: rgba(255,255,255,0.95); padding: 15px 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid var(--border-color); z-index: 10; backdrop-filter: blur(4px); }}
    .legend h4 {{ margin: 0 0 10px 0; font-size: 0.9rem; color: #334155; }}
    .legend-item {{ display: flex; align-items: center; margin-bottom: 8px; font-size: 0.85rem; color: #475569; }}
    .legend-item:last-child {{ margin-bottom: 0; }}
    .color-box {{ width: 16px; height: 16px; border-radius: 4px; margin-right: 10px; border: 1px solid rgba(0,0,0,0.1); }}
    
    .back-btn {{ position: absolute; top: 20px; left: 20px; background: var(--panel-bg); padding: 10px 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid var(--border-color); z-index: 10; text-decoration: none; color: #1e293b; font-weight: 500; display: flex; align-items: center; gap: 8px; }}
    .back-btn:hover {{ background: #f1f5f9; }}
  </style>
</head>
<body>

  <div id="network-container">
    <a href="/" class="back-btn"> Trang Chủ</a>
    <div id="network"></div>
    <div class="legend">
      <h4>Chú Thích Màu Sắc</h4>
      <div class="legend-item"><div class="color-box" style="background:#4f46e5;"></div> File Root (Gốc)</div>
      <div class="legend-item"><div class="color-box" style="background:#0ea5e9;"></div> Lớp (Class)</div>
      <div class="legend-item"><div class="color-box" style="background:#22c55e;"></div> Hàm (Vượt qua 100%)</div>
      <div class="legend-item"><div class="color-box" style="background:#ef4444;"></div> Hàm (Có lỗi/thất bại)</div>
      <div class="legend-item"><div class="color-box" style="background:#f59e0b;"></div> Hàm (Thiếu test/Không rõ)</div>
    </div>
  </div>

  <div id="sidebar">
    <div class="header">
      <h2>Báo Cáo Tổng Hợp Đa Tập Tin</h2>
      <p>Sơ đồ hiển thị toàn bộ các tập tin được kiểm thử. Nhấn vào bất kỳ node nào trên biểu đồ bên trái để xem chi tiết kết quả test của nó.</p>
    </div>
    <div class="content" id="details">
      <div style="text-align: center; color: var(--text-muted); margin-top: 50px;">
        <svg style="width: 64px; height: 64px; margin-bottom: 15px; opacity: 0.5;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"></path></svg>
        <p>Vui lòng chọn một node trên đồ thị để bắt đầu</p>
      </div>
    </div>
  </div>

  <script>
    const data = {data_json};

    const typeTranslations = {{
      'file': 'Tập tin',
      'class': 'Lớp (Class)',
      'function': 'Hàm (Function)',
      'async_function': 'Hàm Bất đồng bộ'
    }};

    const visNodes = data.nodes.map(n => {{
      let c = '#9ca3af';
      if (n.type === 'file') c = '#4f46e5';
      else if (n.type === 'class') c = '#0ea5e9';
      else {{
        const counts = n.status_counts || {{}};
        const passed = counts.PASSED || 0;
        const failed = (counts.FAILED || 0) + (counts.ERROR || 0);
        const total = passed + failed + (counts.unknown || 0);
        
        if (failed > 0) c = '#ef4444';
        else if (total > 0 && passed === total) c = '#22c55e';
        else c = '#f59e0b';
      }}

      let label = n.name;
      if (label.length > 25) label = label.substring(0,22) + '...';

      let size = 25;
      if (n.type === 'file') size = 35;
      else if (n.type === 'class') size = 30;

      return {{
        id: n.id,
        label,
        color: {{ background: c, border: '#1e293b', highlight: {{ background: c, border: '#000000' }} }},
        shape: n.type === 'file' ? 'box' : 'ellipse',
        font: {{ color: '#0f172a', face: 'Inter', size: 14 }},
        shadow: {{ enabled: true, color: 'rgba(0,0,0,0.1)', size: 5, x: 2, y: 2 }},
        size,
      }};
    }});

    const visEdges = data.edges.map(e => ({{ 
      ...e, 
      arrows: 'to',
      color: {{ color: '#cbd5e1', highlight: '#94a3b8' }},
      smooth: {{ type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 }}
    }}));

    const container = document.getElementById('network');
    const network = new vis.Network(
      container,
      {{ nodes: new vis.DataSet(visNodes), edges: new vis.DataSet(visEdges) }},
      {{
        layout: {{ hierarchical: {{ enabled: true, direction: 'UD', sortMethod: 'directed', nodeSpacing: 250, treeSpacing: 300 }} }},
        physics: false,
        interaction: {{ hover: true, tooltipDelay: 200 }},
      }}
    );

    network.on('click', function(params) {{
      if (!params.nodes || params.nodes.length === 0) return;
      const id = params.nodes[0];
      const node = data.nodes.find(n => n.id === id);
      const details = document.getElementById('details');

      const nodeTypeVi = typeTranslations[node.type] || node.type || 'hàm';

      let html = `<h4 style="margin-top: 0; word-break: break-all; color: var(--primary); font-size: 1.2rem;">${{escapeHtml(id)}}</h4>`;
      
      html += `<div class="info-grid">`;
      html += `<span class="info-label">Loại:</span> <b>${{escapeHtml(nodeTypeVi)}}</b>`;
      html += `<span class="info-label">Dòng:</span> <b>${{node.lineno || 'N/A'}}</b>`;
      html += `<span class="info-label">Kiểm thử:</span> <b>${{node.test_count || 0}} bài</b>`;
      html += `</div>`;

      const counts = node.status_counts || {{}};
      const passed = counts.PASSED || 0;
      const failed = (counts.FAILED || 0) + (counts.ERROR || 0);
      const unknown = counts.unknown || 0;
      
      html += `<div style="margin-bottom: 20px;">`;
      if (passed > 0 || (passed === 0 && failed === 0 && unknown === 0)) {{
         html += `<span class="badge ok">ĐẠT: ${{passed}}</span>`;
      }}
      if (failed > 0) {{
         html += `<span class="badge bad">LỖI/THẤT BẠI: ${{failed}}</span>`;
      }}
      if (unknown > 0) {{
         html += `<span class="badge unk">KHÔNG RÕ: ${{unknown}}</span>`;
      }}
      html += `</div>`;

      const tests = node.tests || [];
      if (tests.length > 0) {{
        html += '<h3 style="margin-top: 30px;">Các Bài Kiểm Thử</h3><ul class="test-list">';
        for (const tid of tests) {{
          const t = data.tests[tid] || {{ source: 'N/A' }};
          const short = tid.includes('::') ? tid.split('::').slice(-1)[0] : tid;
          let st = countsFromOutput(tid, short);
          
          let stVi = st;
          let stClass = 'status-unknown';
          if (st === 'PASSED') {{ stVi = 'ĐẠT'; stClass = 'status-passed'; }}
          else if (st === 'FAILED') {{ stVi = 'THẤT BẠI'; stClass = 'status-failed'; }}
          else if (st === 'ERROR') {{ stVi = 'LỖI'; stClass = 'status-error'; }}
          else {{ stVi = 'KHÔNG RÕ'; }}

          html += `<li><b>${{escapeHtml(short)}}</b> <div style="margin: 8px 0;"><i class="${{stClass}}">${{escapeHtml(stVi)}}</i></div><pre>${{escapeHtml(t.source || '')}}</pre></li>`;
        }}
        html += '</ul>';
      }} else {{
        html += '<h3 style="margin-top: 30px;">Các Bài Kiểm Thử</h3><div style="background: #f1f5f9; padding: 15px; border-radius: 8px;"><p style="color: var(--text-muted); font-style: italic; margin: 0;">Không có bài kiểm thử nào được ánh xạ tới node này.</p></div>';
      }}

      details.innerHTML = html;
    }});

    function countsFromOutput(tid, short) {{
      const text = data.pytest_output || '';
      if (text.includes(tid + ' PASSED') || text.includes(short + ' PASSED')) return 'PASSED';
      if (text.includes(tid + ' FAILED') || text.includes(short + ' FAILED')) return 'FAILED';
      if (text.includes(tid + ' ERROR') || text.includes(short + ' ERROR')) return 'ERROR';
      return 'unknown';
    }}

    function escapeHtml(s) {{
      return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }}
  </script>
</body>
</html>
'''
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    return html_path

if __name__ == '__main__':
    print('Use generate_report(source_file, test_file, pytest_output).')
"""

    correct_lines .append (rest )

    with open ("d:\\Download\\chien\\reporter.py","w",encoding ="utf-8")as f :
        f .writelines (correct_lines )
    print ("Fixed reporter.py")
else :
    print ("Could not find end of html_template")
