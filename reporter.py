import ast 
import json 
import os 
import re 
import webbrowser 
from typing import Dict ,List ,Tuple 




# Tóm tắt: Không có docstring cho _module_name_from_path
def _module_name_from_path (file_path :str )->str :
    return os .path .splitext (os .path .basename (file_path ))[0 ]




# Tóm tắt: Build AST graph nodes and edges.
def analyze_calls (file_path :str )->Tuple [List [Dict ],List [Tuple [str ,str ]],Dict [str ,str ],str ]:
    """Build AST graph nodes and edges.

    Graph hierarchy:
    - file node
    - class nodes under file
    - function/method nodes under file/class

    Also returns:
    - functions_map: map short names to function node ids
    - module_name: source module name (e.g. sample)
    """
    with open (file_path ,'r',encoding ='utf-8')as f :
        src =f .read ()

    tree =ast .parse (src )
    module =_module_name_from_path (file_path )
    file_label =os .path .basename (file_path )

    nodes :List [Dict ]=[]
    edges :List [Tuple [str ,str ]]=[]
    functions_map :Dict [str ,str ]={}

    file_id =module 
    nodes .append ({
    'id':file_id ,
    'label':file_label ,
    'type':'file',
    'lineno':None ,
    })

    id_to_ast :Dict [str ,ast .AST ]={}

    for node in tree .body :
        if isinstance (node ,ast .FunctionDef ):
            fid =f"{module}::{node.name}"
            nodes .append ({
            'id':fid ,
            'label':node .name ,
            'type':'function',
            'lineno':getattr (node ,'lineno',None ),
            })
            edges .append ((file_id ,fid ))
            functions_map [node .name ]=fid 
            id_to_ast [fid ]=node 

        if isinstance (node ,ast .ClassDef ):
            cid =f"{module}::{node.name}"
            nodes .append ({
            'id':cid ,
            'label':node .name ,
            'type':'class',
            'lineno':getattr (node ,'lineno',None ),
            })
            edges .append ((file_id ,cid ))

            for sub in node .body :
                if isinstance (sub ,ast .FunctionDef ):
                    mid =f"{cid}::{sub.name}"
                    nodes .append ({
                    'id':mid ,
                    'label':sub .name ,
                    'type':'method',
                    'lineno':getattr (sub ,'lineno',None ),
                    })
                    edges .append ((cid ,mid ))
                    functions_map [sub .name ]=mid 
                    functions_map [f"{node.name}::{sub.name}"]=mid 
                    id_to_ast [mid ]=sub 


    existing_nodes ={n ['id']for n in nodes }
    for caller_id ,ast_node in id_to_ast .items ():
        for sub in ast .walk (ast_node ):
            if not isinstance (sub ,ast .Call ):
                continue 

            callee_id =None 
            if isinstance (sub .func ,ast .Name ):
                callee_id =functions_map .get (sub .func .id )
            elif isinstance (sub .func ,ast .Attribute ):
                attr =sub .func .attr 
                val =sub .func .value 
                if isinstance (val ,ast .Name )and val .id ==module :
                    callee_id =functions_map .get (attr )
                else :
                    callee_id =functions_map .get (attr )

            if callee_id and callee_id in existing_nodes :
                edges .append ((caller_id ,callee_id ))

    return nodes ,edges ,functions_map ,module 




# Tóm tắt: Extract test functions and map called functions using AST.
def extract_tests (test_file_path :str ,functions_map :Dict [str ,str ],module_name :str )->Dict [str ,Dict ]:
    """Extract test functions and map called functions using AST."""
    with open (test_file_path ,'r',encoding ='utf-8')as f :
        src =f .read ()

    tree =ast .parse (src )
    lines =src .splitlines ()
    tests :Dict [str ,Dict ]={}



# Tóm tắt: Không có docstring cho _collect_calls
    def _collect_calls (fn_node :ast .FunctionDef )->List [str ]:
        calls :List [str ]=[]
        for sub in ast .walk (fn_node ):
            if not isinstance (sub ,ast .Call ):
                continue 

            func_id =None 
            if isinstance (sub .func ,ast .Name ):
                func_id =functions_map .get (sub .func .id )
            elif isinstance (sub .func ,ast .Attribute ):
                attr =sub .func .attr 
                val =sub .func .value 
                if isinstance (val ,ast .Name )and val .id ==module_name :
                    func_id =functions_map .get (attr )
                else :
                    func_id =functions_map .get (attr )

            if func_id :
                calls .append (func_id )


        return list (dict .fromkeys (calls ))

    for node in tree .body :
        if isinstance (node ,ast .FunctionDef )and node .name .startswith ('test'):
            start =node .lineno -1 
            end =getattr (node ,'end_lineno',node .lineno )
            tests [node .name ]={
            'source':'\n'.join (lines [start :end ]),
            'class':None ,
            'calls':_collect_calls (node ),
            }

        if isinstance (node ,ast .ClassDef ):
            for sub in node .body :
                if isinstance (sub ,ast .FunctionDef )and sub .name .startswith ('test'):
                    start =sub .lineno -1 
                    end =getattr (sub ,'end_lineno',sub .lineno )
                    tid =f"{node.name}::{sub.name}"
                    tests [tid ]={
                    'source':'\n'.join (lines [start :end ]),
                    'class':node .name ,
                    'calls':_collect_calls (sub ),
                    }

    return tests 




# Tóm tắt: Không có docstring cho map_tests_to_functions
def map_tests_to_functions (tests :Dict [str ,Dict ],functions_map :Dict [str ,str ])->Dict [str ,List [str ]]:
    mapping ={fid :[]for fid in set (functions_map .values ())}
    for tid ,info in tests .items ():
        for fid in info .get ('calls',[]):
            mapping .setdefault (fid ,[]).append (tid )
    return mapping 




# Tóm tắt: Parse pytest - v output lines into status map by test id and short id.
def parse_pytest_output (output :str )->Dict [str ,str ]:
    """Parse pytest -v output lines into status map by test id and short id."""
    status :Dict [str ,str ]={}
    stat_re =re .compile (r'\b(PASSED|FAILED|ERROR|XFAILED|XPASS|skipped)\b')

    for line in output .splitlines ():
        sline =line .strip ()
        if not sline :
            continue 

        m =stat_re .search (sline )
        if not m :
            continue 

        stat =m .group (1 )
        tokens =sline .split ()
        tid =None 
        for t in tokens :
            if '::'in t and t .startswith ('test_'):
                tid =t 
                break 
            if t .startswith ('test_')and t .endswith ('.py'):
                tid =t 
                break 
            if '::'in t and '.py::'in t :
                tid =t 
                break 

        if not tid :
            for t in tokens :
                if '::'in t :
                    tid =t 
                    break 

        if not tid :
            continue 

        tid =tid .rstrip (',:')
        status [tid ]=stat 

        if '::'in tid :
            short =tid .split ('::')[-1 ]
            status [short ]=stat 

    return status 




# Tóm tắt: Không có docstring cho _node_color
def _node_color (status_counts :Dict [str ,int ],ntype :str )->str :
    if ntype =='file':
        return '#4f46e5'
    if ntype =='class':
        return '#0ea5e9'

    if not status_counts :
        return '#9ca3af'

    if status_counts .get ('FAILED')or status_counts .get ('ERROR'):
        return '#ef4444'

    total =sum (status_counts .values ())
    passed =status_counts .get ('PASSED',0 )
    if total >0 and passed ==total :
        return '#22c55e'

    return '#f59e0b'




# Tóm tắt: Không có docstring cho generate_report
def generate_report (source_file :str ,test_file :str ,pytest_output :str ,out_dir :str ='reports')->str :
    os .makedirs (out_dir ,exist_ok =True )

    nodes ,edges ,functions_map ,module_name =analyze_calls (source_file )

    tests :Dict [str ,Dict ]={}
    test_path =test_file if os .path .exists (test_file )else os .path .join (os .getcwd (),test_file )
    if os .path .exists (test_path ):
        tests =extract_tests (test_path ,functions_map ,module_name )

    mapping =map_tests_to_functions (tests ,functions_map )
    statuses =parse_pytest_output (pytest_output or '')


    function_node_ids =set (functions_map .values ())
    for n in nodes :
        nid =n ['id']
        if nid in function_node_ids :
            ntests =mapping .get (nid ,[])
        else :
            ntests =[]

        status_counts :Dict [str ,int ]={}
        for tid in ntests :
            st =statuses .get (tid )or statuses .get (tid .split ('::')[-1 ])or 'unknown'
            status_counts [st ]=status_counts .get (st ,0 )+1 

        n ['tests']=ntests 
        n ['test_count']=len (ntests )
        n ['status_counts']=status_counts 
        n ['color']=_node_color (status_counts ,n .get ('type','function'))

    report_data ={
    'nodes':nodes ,
    'edges':[{'from':a ,'to':b }for a ,b in edges ],
    'tests':tests ,
    'pytest_output':pytest_output ,
    }

    json_path =os .path .join (out_dir ,f"report_{os.path.basename(source_file)}.json")
    html_path =os .path .join (out_dir ,f"report_{os.path.basename(source_file)}.html")

    with open (json_path ,'w',encoding ='utf-8')as jf :
        json .dump (report_data ,jf ,ensure_ascii =False ,indent =2 )

    json_text =json .dumps (report_data )
    safe_pytest =(pytest_output or '').replace ('&','&amp;').replace ('<','&lt;').replace ('>','&gt;')

    html_template ='''<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <title>Báo Cáo AutoTestTool - {{FNAME}}</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
  <link href="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.css" rel="stylesheet" type="text/css" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
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
      --neutral-bg: #f1f5f9;
      --neutral-text: #334155;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; font-family: 'Inter', sans-serif; background-color: var(--bg-color); color: var(--text-main); }
    body { display: flex; height: 100vh; overflow: hidden; }
    #network { width: calc(100% - 480px); height: 100vh; background-color: #ffffff; }
    #panel { width: 480px; padding: 24px; overflow-y: auto; height: 100vh; background-color: var(--panel-bg); border-left: 1px solid var(--border-color); box-shadow: -4px 0 15px rgba(0,0,0,0.03); z-index: 10; }
    
    h3, h4 { margin-top: 0; color: #1e293b; font-weight: 600; }
    h3 { font-size: 1.25rem; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color); }
    h4 { font-size: 1.1rem; margin-top: 24px; margin-bottom: 12px; }
    
    #details { line-height: 1.6; color: var(--text-muted); }
    #details b { color: var(--text-main); font-weight: 600; }
    
    pre { background: var(--neutral-bg); padding: 12px; border-radius: 8px; white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.875rem; border: 1px solid var(--border-color); overflow-x: auto; color: #334155; }
    
    .badge { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 9999px; margin-right: 8px; margin-bottom: 8px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.025em; }
    .ok { background: var(--success-bg); color: var(--success-text); }
    .bad { background: var(--danger-bg); color: var(--danger-text); }
    .unk { background: var(--neutral-bg); color: var(--neutral-text); }
    
    .info-grid { display: grid; grid-template-columns: auto 1fr; gap: 8px 16px; margin-bottom: 16px; font-size: 0.95rem; }
    .info-label { color: var(--text-muted); }
    
    ul.test-list { list-style: none; padding: 0; margin: 0; }
    ul.test-list li { margin-bottom: 16px; padding: 16px; border: 1px solid var(--border-color); border-radius: 8px; background: #fafafa; }
    ul.test-list li b { display: block; margin-bottom: 8px; color: var(--primary); word-break: break-all; }
    ul.test-list li i { display: inline-block; margin-bottom: 8px; font-style: normal; font-size: 0.8rem; font-weight: 600; padding: 2px 6px; border-radius: 4px; }
    
    .status-passed { background: var(--success-bg); color: var(--success-text); }
    .status-failed { background: var(--danger-bg); color: var(--danger-text); }
    .status-error { background: var(--danger-bg); color: var(--danger-text); }
    .status-unknown { background: var(--neutral-bg); color: var(--neutral-text); }
    
    hr { border: 0; border-top: 1px solid var(--border-color); margin: 24px 0; }
    
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
  </style>
</head>
<body>
  <div id="network"></div>
  <div id="panel">
    <h3>Chi Tiết Node</h3>
    <div id="details">
      <p>Nhấn vào một node trên biểu đồ để xem chi tiết các bài kiểm thử và kết quả.</p>
    </div>
    <hr/>
    <h4>Đầu ra Pytest</h4>
    <pre id="pytest_output">{{PYTEST_OUTPUT}}</pre>
  </div>

  <script>
    const data = {{DATA}};

    const typeTranslations = {
      'file': 'tệp',
      'class': 'lớp',
      'function': 'hàm',
      'method': 'phương thức'
    };

    const visNodes = data.nodes.map(n => {
      const c = n.color || '#9ca3af';
      const size = n.type === 'file' ? 38 : (n.type === 'class' ? 28 : 20);
      const label = n.type === 'function' || n.type === 'method'
        ? `${n.label}\\n(${n.test_count} kiểm thử)`
        : n.label;
      return {
        id: n.id,
        label,
        color: { background: c, border: '#1e293b', highlight: { background: c, border: '#000000' } },
        shape: n.type === 'file' ? 'box' : 'ellipse',
        font: { color: '#0f172a', face: 'Inter', size: 14 },
        shadow: { enabled: true, color: 'rgba(0,0,0,0.1)', size: 5, x: 2, y: 2 },
        size,
      };
    });

    const visEdges = data.edges.map(e => ({ 
      ...e, 
      arrows: 'to',
      color: { color: '#cbd5e1', highlight: '#94a3b8' },
      smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 }
    }));

    const container = document.getElementById('network');
    const network = new vis.Network(
      container,
      { nodes: new vis.DataSet(visNodes), edges: new vis.DataSet(visEdges) },
      {
        layout: { hierarchical: { enabled: true, direction: 'UD', sortMethod: 'directed', nodeSpacing: 150, treeSpacing: 200 } },
        physics: false,
        interaction: { hover: true, tooltipDelay: 200 },
      }
    );

    network.on('click', function(params) {
      if (!params.nodes || params.nodes.length === 0) return;
      const id = params.nodes[0];
      const node = data.nodes.find(n => n.id === id);
      const details = document.getElementById('details');

      const nodeTypeVi = typeTranslations[node.type] || node.type || 'hàm';

      let html = `<h4 style="margin-top: 0; word-break: break-all; color: var(--primary);">${escapeHtml(id)}</h4>`;
      
      html += `<div class="info-grid">`;
      html += `<span class="info-label">Loại:</span> <b>${escapeHtml(nodeTypeVi)}</b>`;
      html += `<span class="info-label">Dòng:</span> <b>${node.lineno || 'N/A'}</b>`;
      html += `<span class="info-label">Kiểm thử:</span> <b>${node.test_count || 0} bài</b>`;
      html += `</div>`;

      const counts = node.status_counts || {};
      const passed = counts.PASSED || 0;
      const failed = (counts.FAILED || 0) + (counts.ERROR || 0);
      const unknown = counts.unknown || 0;
      
      html += `<div>`;
      if (passed > 0 || (passed === 0 && failed === 0 && unknown === 0)) {
         html += `<span class="badge ok">ĐẠT: ${passed}</span>`;
      }
      if (failed > 0) {
         html += `<span class="badge bad">LỖI/THẤT BẠI: ${failed}</span>`;
      }
      if (unknown > 0) {
         html += `<span class="badge unk">KHÔNG RÕ: ${unknown}</span>`;
      }
      html += `</div>`;

      const tests = node.tests || [];
      if (tests.length > 0) {
        html += '<hr/><h4>Các Bài Kiểm Thử</h4><ul class="test-list">';
        for (const tid of tests) {
          const t = data.tests[tid] || { source: 'N/A' };
          const short = tid.includes('::') ? tid.split('::').slice(-1)[0] : tid;
          let st = countsFromOutput(tid, short);
          
          let stVi = st;
          let stClass = 'status-unknown';
          if (st === 'PASSED') { stVi = 'ĐẠT'; stClass = 'status-passed'; }
          else if (st === 'FAILED') { stVi = 'THẤT BẠI'; stClass = 'status-failed'; }
          else if (st === 'ERROR') { stVi = 'LỖI'; stClass = 'status-error'; }
          else { stVi = 'KHÔNG RÕ'; }

          html += `<li><b>${escapeHtml(tid)}</b> <i class="${stClass}">${escapeHtml(stVi)}</i><pre>${escapeHtml(t.source || '')}</pre></li>`;
        }
        html += '</ul>';
      } else {
        html += '<hr/><div><p style="color: var(--text-muted); font-style: italic;">Không có bài kiểm thử nào được ánh xạ tới node này.</p></div>';
      }

      details.innerHTML = html;
    });

    function countsFromOutput(tid, short) {
      const text = data.pytest_output || '';
      if (text.includes(tid + ' PASSED') || text.includes(short + ' PASSED')) return 'PASSED';
      if (text.includes(tid + ' FAILED') || text.includes(short + ' FAILED')) return 'FAILED';
      if (text.includes(tid + ' ERROR') || text.includes(short + ' ERROR')) return 'ERROR';
      return 'unknown';
    }

    function escapeHtml(s) {
      return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }
  </script>
</body>
</html>
'''

    html =html_template .replace ('{{DATA}}',json_text )
    html =html .replace ('{{PYTEST_OUTPUT}}',safe_pytest )
    html =html .replace ('{{FNAME}}',os .path .basename (source_file ))

    with open (html_path ,'w',encoding ='utf-8')as hf :
        hf .write (html )

    return html_path 


if __name__ =='__main__':
    print ('Use generate_report(source_file, test_file, pytest_output).')
