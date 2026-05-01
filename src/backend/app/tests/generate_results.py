"""
Generador de HTML para resultados de tests.
Ejecuta pytest y genera results.html automáticamente.
"""

import subprocess
import json
import os


def run_tests():
    """Ejecuta pytest y guarda resultados en JSON."""
    proc_result = subprocess.run(
        ["pytest", "app/tests/unit/pqr/", "app/tests/unit/history/", "-v", "--json-report", "--json-report-file=app/tests/results.json"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    )
    return proc_result.returncode


def load_tests_from_json():
    """Carga los resultados del JSON."""
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")
    if not os.path.exists(json_path):
        return []
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    tests = []
    for test in data.get("tests", []):
        if test.get("outcome") in ("passed", "skipped"):
            nodeid = test.get("nodeid", "")
            
            if "test_pqr.py" in nodeid:
                service = "pqr"
                filepath = "app/tests/unit/pqr/test_pqr.py"
            elif "test_history.py" in nodeid:
                service = "history"
                filepath = "app/tests/unit/history/test_history.py"
            else:
                continue
            
            # Extract class and method name from nodeid
            parts = nodeid.split("::")
            test_name = parts[-1] if parts else nodeid
            class_name = parts[1] if len(parts) > 1 else ""
            
            # Get line number
            lineno = test.get("lineno", 0)
            
            # Get test code
            code = get_test_code(filepath, lineno)
            
            tests.append({
                "name": test_name,
                "service": service,
                "file": filepath,
                "class": class_name,
                "lineno": lineno,
                "status": test.get("outcome", "passed"),
                "code": code
            })
    
    return tests


def get_test_code(filepath, lineno):
    """Extrae el codigo fuente de un test."""
    if not filepath or not lineno:
        return "# Codigo no disponible"
    
    if "test_pqr.py" in filepath:
        test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unit", "pqr", "test_pqr.py")
    elif "test_history.py" in filepath:
        test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unit", "history", "test_history.py")
    else:
        test_dir = filepath
    
    if os.path.exists(test_dir):
        full_path = test_dir
    else:
        return "# No encontrado"
    
    if not os.path.exists(full_path):
        return "# No encontrado: " + full_path
    
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        
        start = lineno - 1
        if start < 0 or start >= len(lines):
            return "# Linea fuera de rango"
        
        code_lines = []
        indent = None
        
        for i in range(start, min(start + 40, len(lines))):
            line = lines[i]
            
            if indent is None and line.strip():
                indent = len(line) - len(line.lstrip())
            
            if indent is not None and len(line) - len(line.lstrip()) < indent and line.strip():
                break
            
            code_lines.append(line.rstrip())
        
        if not code_lines:
            return "# Vacio"
        
        # Extract assertions from the code
        full_code = "\n".join(code_lines)
        assertions = []
        for line in code_lines:
            if "assert" in line and "#" not in line.split("assert")[0]:
                assertions.append(line.strip())
        
        return full_code + "\n\n### ASSERTIONS ###\n" + "\n".join(assertions) if assertions else full_code
    
    except Exception as e:
        return "# Error: " + str(e)


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resultados de Tests - PQR System</title>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg: #0f1419;
            --surface: #192734;
            --surface-hover: #22303c;
            --border: #38444d;
            --text: #e7e9ea;
            --text-muted: #8b98a5;
            --primary: #1d9bf0;
            --success: #00ba7c;
            --skipped: #ffd400;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
        }
        
        .sidebar {
            width: 320px;
            background: var(--surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
        }
        
        .sidebar-header {
            padding: 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .sidebar-header h1 {
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text);
        }
        
        .refresh-btn {
            padding: 6px 12px;
            border: 1px solid var(--border);
            border-radius: 20px;
            background: transparent;
            color: var(--text-muted);
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: all 0.2s;
        }
        
        .refresh-btn:hover { background: var(--surface-hover); color: var(--text); }
        
        .filters {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            gap: 6px;
        }
        
        .filter-btn {
            padding: 6px 12px;
            border: none;
            border-radius: 16px;
            background: var(--bg);
            color: var(--text-muted);
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .filter-btn:hover { background: var(--surface-hover); }
        .filter-btn.active { background: var(--primary); color: white; }
        
        .stats-bar {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            gap: 16px;
            font-size: 13px;
        }
        
        .stat { display: flex; align-items: center; gap: 6px; }
        .stat .dot { width: 8px; height: 8px; border-radius: 50%; }
        .stat .dot.passed { background: var(--success); }
        .stat .dot.skipped { background: var(--skipped); }
        
        .test-list {
            flex: 1;
            overflow-y: auto;
        }
        
        .test-item {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .test-item:hover { background: var(--surface-hover); }
        .test-item.active { background: var(--surface-hover); border-left: 3px solid var(--primary); }
        
        .test-item-header {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .test-item .status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
        .test-item .status-dot.passed { background: var(--success); }
        .test-item .status-dot.skipped { background: var(--skipped); }
        
        .test-item .name {
            font-size: 13px;
            font-weight: 500;
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .test-item .service-badge {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            background: var(--bg);
            color: var(--text-muted);
            text-transform: uppercase;
        }
        
        .test-item .class-name {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 4px;
            margin-left: 16px;
        }
        
        .main {
            flex: 1;
            margin-left: 320px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .main-header {
            padding: 16px 24px;
            border-bottom: 1px solid var(--border);
            background: var(--surface);
        }
        
        .selected-test-name {
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .selected-test-name .status-badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .status-badge.passed { background: rgba(0, 186, 124, 0.15); color: var(--success); }
        .status-badge.skipped { background: rgba(255, 212, 0, 0.15); color: var(--skipped); }
        
        .main-content { flex: 1; padding: 24px; overflow-y: auto; }
        
        .code-section { margin-bottom: 24px; }
        
        .section-title {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .code-block {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }
        
        .code-header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            font-size: 12px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
        }
        
        .code-header .file-path { font-family: 'JetBrains Mono', monospace; }
        
        .code-content {
            padding: 16px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            overflow-x: auto;
            white-space: pre;
            color: #8b98a5;
        }
        
        .code-content .assertion { color: #7ee787; font-weight: 500; }
        .code-content .result-ok { color: #00ba7c; font-weight: 600; font-size: 14px; }
        .code-content .string { color: #a5d6ff; }
        .code-content .function { color: #d2a8ff; }
        .code-content .comment { color: #5c6773; }
        .code-content .number { color: #79c0ff; }
        .code-content .keyword { color: #ff7a72; }
        
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--text-muted);
        }
        
        .empty-state .material-symbols-outlined { font-size: 64px; margin-bottom: 16px; opacity: 0.5; }
        
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
    </style>
</head>
<body>
    <aside class="sidebar">
        <div class="sidebar-header">
            <h1>
                <span class="material-symbols-outlined" style="color: var(--primary);">bug_report</span>
                Tests
            </h1>
            <button class="refresh-btn" onclick="location.reload()">
                <span class="material-symbols-outlined" style="font-size: 14px;">refresh</span>
                Actualizar
            </button>
        </div>
        
        <div class="filters">
            <button class="filter-btn active" data-filter="all">Todos</button>
            <button class="filter-btn" data-filter="pqr">PQR</button>
            <button class="filter-btn" data-filter="history">History</button>
        </div>
        
        <div class="stats-bar">
            <div class="stat"><div class="dot passed"></div><span id="passed-count">0</span> Pasados</div>
            <div class="stat"><div class="dot skipped"></div><span id="skipped-count">0</span> Omitidos</div>
        </div>
        
        <div class="test-list" id="test-list"></div>
    </aside>
    
    <main class="main">
        <div class="main-header">
            <div class="selected-test-name" id="selected-name">Selecciona un test</div>
        </div>
        
        <div class="main-content" id="main-content">
            <div class="empty-state">
                <span class="material-symbols-outlined">touch_app</span>
                <p>Selecciona un test del panel izquierdo</p>
            </div>
        </div>
    </main>

    <script>
        const testData = TEST_DATA_JSON;
        
        console.log('Test data loaded:', testData.length, 'tests');
        
        let selectedTest = null;
        
        function syntaxHighlight(code) {
            code = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            code = code.replace(/(def|class|import|from|return|if|else|elif|for|while|with|as|try|except|finally|raise|pass|break|continue|and|or|not|in|is|None|True|False|async|await)/g, '<span class="keyword">$1</span>');
            code = code.replace(/(["'])((?:\\\\.|(?!\\1)[^\\\\])*?)\\1/g, '<span class="string">$1$2$1</span>');
            code = code.replace(/\\b(\\d+)\\b/g, '<span class="number">$1</span>');
            code = code.replace(/(#.*)$/gm, '<span class="comment">$1</span>');
            return code;
        }
        
        function renderTestList(filter) {
            const filtered = filter === 'all' ? testData : testData.filter(t => t.service === filter);
            const testList = document.getElementById('test-list');
            
            testList.innerHTML = filtered.map((test, idx) => {
                return '<div class="test-item ' + (selectedTest && selectedTest.name === test.name ? 'active' : '') + '" onclick="selectTest(' + idx + ')">' +
                    '<div class="test-item-header">' +
                    '<div class="status-dot ' + test.status + '"></div>' +
                    '<span class="name">' + test.name + '</span>' +
                    '<span class="service-badge">' + test.service + '</span></div>' +
                    '<div class="test-item-header"><span class="class-name">' + test.class + '</span></div></div>';
            }).join('');
            
            document.getElementById('passed-count').textContent = testData.filter(t => t.status === 'passed').length;
            document.getElementById('skipped-count').textContent = testData.filter(t => t.status === 'skipped').length;
        }
        
        function selectTest(idx) {
            selectedTest = testData[idx];
            
            var newline = String.fromCharCode(10);
            
            document.querySelectorAll('.test-item').forEach(function(el, i) {
                el.classList.toggle('active', i === idx);
            });
            
            var nameEl = document.getElementById('selected-name');
            nameEl.innerHTML = selectedTest.name + 
                '<span class="status-badge ' + selectedTest.status + '">' + 
                (selectedTest.status === 'passed' ? '✓ Pasado' : '○ Omitido') + '</span>';
            
            var codeHtml = selectedTest.code;
            var assertionsHtml = '';
            
            if (selectedTest.code && selectedTest.code.indexOf('### ASSERTIONS ###') !== -1) {
                var parts = selectedTest.code.split('### ASSERTIONS ###');
                codeHtml = parts[0].trim();
                assertionsHtml = parts[1].trim();
            }
            
            var assertionsSection = '';
            if (assertionsHtml) {
                var assertLines = assertionsHtml.split(newline).filter(function(a) { return a.trim(); });
                assertionsSection = '<div class="code-section"><div class="section-title"><span class="material-symbols-outlined" style="font-size:16px;">check_circle</span>Verificaciones (' + assertLines.length + ')</div><div class="code-block" style="border-color:var(--success);"><div class="code-content">';
                
                assertLines.forEach(function(assertion) {
                    if (assertion.trim()) {
                        assertionsSection += '<div style="padding:4px 0;border-bottom:1px solid var(--border);color:#7ee787;">✓ ' + assertion.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>';
                    }
                });
                
                assertionsSection += '</div></div></div>';
            }
            
            let reasonHtml = '';
            if (selectedTest.reason) {
                reasonHtml = '<div class="code-section"><div class="section-title">' +
                    '<span class="material-symbols-outlined" style="font-size:16px;">info</span>Razón de omisión</div>' +
                    '<div class="code-block" style="background:rgba(255,212,0,0.1);border-color:rgba(255,212,0,0.3);">' +
                    '<div class="code-content" style="color:var(--skipped);">' + selectedTest.reason + '</div></div></div>';
            }
            
            document.getElementById('main-content').innerHTML = 
                '<div class="code-section"><div class="section-title">' +
                '<span class="material-symbols-outlined" style="font-size:16px;">code</span>Código del Test</div>' +
                '<div class="code-block"><div class="code-header">' +
                '<span class="file-path">' + selectedTest.file + ':' + (selectedTest.lineno || '') + '</span>' +
                '<span>' + selectedTest.class + '</span></div>' +
                '<div class="code-content">' + syntaxHighlight(codeHtml) + '</div></div></div>' +
                assertionsSection +
                reasonHtml;
        }
        
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                renderTestList(this.dataset.filter);
            });
        });
        
        renderTestList('all');
        
        // Debug: show count in header
        document.querySelector('.sidebar-header h1').innerHTML += ' (' + testData.length + ')';
    </script>
</body>
</html>'''


def generate_html(tests):
    """Genera el HTML con los datos de los tests."""
    passed = sum(1 for t in tests if t["status"] == "passed")
    skipped = sum(1 for t in tests if t["status"] == "skipped")
    
    tests_json = json.dumps(tests, ensure_ascii=False)
    
    html = HTML_TEMPLATE
    html = html.replace("TEST_DATA_JSON", tests_json)
    
    return html


def main():
    """Función principal."""
    print("Ejecutando tests...")
    
    exitcode = run_tests()
    
    if exitcode != 0:
        print("Algunos tests fallaron")
    
    print("Generando HTML...")
    tests = load_tests_from_json()
    
    html = generate_html(tests)
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print("Generado:", output_path)
    print("Tests:", len(tests))


if __name__ == "__main__":
    main()