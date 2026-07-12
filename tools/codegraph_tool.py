import sqlite3
import os
import sys
import json
import argparse
from pathlib import Path

def resolve_db_path():
    # Resolve the repository root directory dynamically (relative to tools/codegraph_tool.py)
    root = Path(__file__).resolve().parents[1]
    
    # 1. Check local workspace root
    db = root / ".codegraph" / "codegraph.db"
    if db.exists():
        return db
        
    # 2. Check parent folder's parent (in case we are in a Git worktree, e.g. .worktrees/<branch>)
    if len(root.parents) >= 2:
        wt_db = root.parents[1] / ".codegraph" / "codegraph.db"
        if wt_db.exists():
            return wt_db
            
    # 3. Fallback to the original hardcoded path
    return Path("e:/AI-based-project/urban-platform/.codegraph/codegraph.db")

DB_PATH = resolve_db_path()


def get_connection():
    if not DB_PATH.exists():
        print(f"Error: Codegraph database not found at {DB_PATH}. Please make sure Claude Code has indexed the project.", file=sys.stderr)
        sys.exit(1)
    return sqlite3.connect(DB_PATH)

def cmd_status(args):
    """Get the status of the codegraph index."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT count(*) FROM files;")
    file_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM nodes;")
    node_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM edges;")
    edge_count = cursor.fetchone()[0]
    
    # Get counts by node kind
    cursor.execute("SELECT kind, count(*) FROM nodes GROUP BY kind ORDER BY count(*) DESC;")
    node_kinds = cursor.fetchall()
    
    # Get counts by edge kind
    cursor.execute("SELECT kind, count(*) FROM edges GROUP BY kind ORDER BY count(*) DESC;")
    edge_kinds = cursor.fetchall()
    
    print("=== Codegraph Database Status ===")
    print(f"Database Path: {DB_PATH}")
    print(f"File Size: {DB_PATH.stat().st_size} bytes")
    print(f"Indexed Files: {file_count}")
    print(f"Indexed Nodes: {node_count}")
    print(f"Indexed Edges: {edge_count}")
    print("\nNode Kinds:")
    for kind, count in node_kinds:
         print(f"  - {kind}: {count}")
    print("\nEdge Kinds:")
    for kind, count in edge_kinds:
         print(f"  - {kind}: {count}")
    conn.close()

def cmd_search(args):
    """Search for nodes matching a query."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"%{args.query}%"
    cursor.execute("""
        SELECT id, kind, name, qualified_name, file_path, start_line, end_line 
        FROM nodes 
        WHERE name LIKE ? OR qualified_name LIKE ? OR docstring LIKE ?
        LIMIT ?;
    """, (query, query, query, args.limit))
    
    results = cursor.fetchall()
    print(f"=== Search Results for '{args.query}' (Limit: {args.limit}) ===")
    if not results:
        print("No matching nodes found.")
    else:
        for row in results:
            print(f"[{row[1].upper()}] {row[3]} ({row[4]}:{row[5]}-{row[6]})")
            print(f"  ID: {row[0]}")
    conn.close()

def cmd_info(args):
    """Get detailed information about a node."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, kind, name, qualified_name, file_path, start_line, end_line, docstring, signature, decorators
        FROM nodes
        WHERE id = ? OR name = ? OR qualified_name = ?;
    """, (args.node, args.node, args.node))
    
    node = cursor.fetchone()
    if not node:
        print(f"Error: Node '{args.node}' not found.", file=sys.stderr)
        sys.exit(1)
        
    print(f"=== Node: {node[3]} ===")
    print(f"ID: {node[0]}")
    print(f"Kind: {node[1]}")
    print(f"File Path: {node[4]} (Lines {node[5]}-{node[6]})")
    if node[8]:
        print(f"Signature: {node[8]}")
    if node[9]:
        print(f"Decorators: {node[9]}")
    if node[7]:
        print("\nDocstring:")
        print("----------------------------------------")
        print(node[7])
        print("----------------------------------------")
        
    # Get relations
    cursor.execute("""
        SELECT e.kind, n.qualified_name, n.kind, e.line
        FROM edges e
        JOIN nodes n ON e.target = n.id
        WHERE e.source = ?;
    """, (node[0],))
    outgoing = cursor.fetchall()
    if outgoing:
        print("\nOutgoing Edges (What this node points to/depends on):")
        for ekind, target_name, tkind, line in outgoing:
            print(f"  - [{ekind.upper()}] -> [{tkind.upper()}] {target_name} (line {line})")
            
    cursor.execute("""
        SELECT e.kind, n.qualified_name, n.kind, e.line
        FROM edges e
        JOIN nodes n ON e.source = n.id
        WHERE e.target = ?;
    """, (node[0],))
    incoming = cursor.fetchall()
    if incoming:
        print("\nIncoming Edges (What references/calls this node):")
        for ekind, source_name, skind, line in incoming:
            print(f"  - [{ekind.upper()}] <- [{skind.upper()}] {source_name} (line {line})")
            
    conn.close()

def cmd_callers(args):
    """Find all callers of a node."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.qualified_name, s.kind, e.line, e.col, s.file_path
        FROM edges e
        JOIN nodes s ON e.source = s.id
        JOIN nodes t ON e.target = t.id
        WHERE (t.id = ? OR t.name = ? OR t.qualified_name = ?) AND e.kind = 'calls';
    """, (args.node, args.node, args.node))
    
    callers = cursor.fetchall()
    print(f"=== Callers of '{args.node}' ===")
    if not callers:
        print("No callers found.")
    else:
        for name, kind, line, col, file_path in callers:
            print(f"  - [{kind.upper()}] {name} in {file_path}:{line}:{col}")
    conn.close()

def cmd_callees(args):
    """Find all callees of a node."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.qualified_name, t.kind, e.line, e.col, t.file_path
        FROM edges e
        JOIN nodes s ON e.source = s.id
        JOIN nodes t ON e.target = t.id
        WHERE (s.id = ? OR s.name = ? OR s.qualified_name = ?) AND e.kind = 'calls';
    """, (args.node, args.node, args.node))
    
    callees = cursor.fetchall()
    print(f"=== Callees of '{args.node}' ===")
    if not callees:
        print("No callees found.")
    else:
        for name, kind, line, col, file_path in callees:
            print(f"  - [{kind.upper()}] {name} in {file_path}:{line}:{col}")
    conn.close()

def cmd_visualize(args):
    """Generate a Mermaid diagram for components in the system."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Let's find files and see imports or containment relation between key modules.
    # Group nodes by top-level files, excluding test files
    cursor.execute(r"""
        SELECT path FROM files 
        WHERE (path LIKE 'src/%' OR path LIKE 'tools/%' OR path = 'app.py')
          AND path NOT LIKE '%/tests/%' AND path NOT LIKE '%\tests\%';
    """)
    files = [r[0] for r in cursor.fetchall()]
    
    print("```mermaid")
    print("graph TD")
    print("  %% Style definitions")
    print("  classDef engine fill:#eff6ff,stroke:#3b82f6,stroke-width:2px;")
    print("  classDef ui fill:#f0fdf4,stroke:#22c55e,stroke-width:2px;")
    print("  classDef tool fill:#fffbeb,stroke:#fbbf24,stroke-width:2px;")
    print("  classDef main fill:#faf5ff,stroke:#a855f7,stroke-width:2px;")
    
    # Get dependencies between files via edges, excluding test dependencies
    cursor.execute(r"""
        SELECT DISTINCT s.file_path, t.file_path, e.kind
        FROM edges e
        JOIN nodes s ON e.source = s.id
        JOIN nodes t ON e.target = t.id
        WHERE s.file_path != t.file_path 
          AND s.file_path IS NOT NULL 
          AND t.file_path IS NOT NULL
          AND s.file_path NOT LIKE '%/tests/%' AND s.file_path NOT LIKE '%\tests\%'
          AND t.file_path NOT LIKE '%/tests/%' AND t.file_path NOT LIKE '%\tests\%'
          AND (s.file_path LIKE 'src/%' OR s.file_path LIKE 'tools/%' OR s.file_path = 'app.py')
          AND (t.file_path LIKE 'src/%' OR t.file_path LIKE 'tools/%' OR t.file_path = 'app.py');
    """)
    
    file_edges = cursor.fetchall()
    
    # Shorten names for nodes
    def node_id(filepath):
        return filepath.replace(".", "_").replace("/", "_").replace("\\", "_").replace("-", "_")
    
    # Generate nodes
    seen_nodes = set()
    for source, target, kind in file_edges:
        seen_nodes.add(source)
        seen_nodes.add(target)
        
    for f in seen_nodes:
        # Categorize
        style = ""
        if "src/engines" in f:
            style = ":::engine"
        elif "src/ui" in f or "pages/" in f:
            style = ":::ui"
        elif "tools/" in f or "scripts/" in f:
            style = ":::tool"
        elif f == "app.py":
            style = ":::main"
            
        print(f'  {node_id(f)}["{f}"]{style}')
        
    # Generate edges
    for source, target, kind in file_edges:
        if kind == 'imports':
            print(f"  {node_id(source)} -->|imports| {node_id(target)}")
        elif kind == 'calls':
            print(f"  {node_id(source)} -->|calls| {node_id(target)}")
            
    print("```")
    conn.close()

def cmd_check_architecture(args):
    """Check for architectural decoupling violations in the codebase."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Query distinct import relationships between local source files and src/pages modules
    cursor.execute("""
        SELECT DISTINCT s.file_path, t.name 
        FROM edges e 
        JOIN nodes s ON e.source = s.id 
        JOIN nodes t ON e.target = t.id 
        WHERE e.kind = 'imports' 
          AND (t.name LIKE 'src.%' OR t.name = 'src' OR t.name LIKE 'pages.%' OR t.name = 'pages') 
          AND s.file_path IS NOT NULL;
    """)
    all_imports = cursor.fetchall()
    conn.close()
    
    violations = []
    for src_file, imp in all_imports:
        # Normalize slashes for consistency
        src_file_norm = src_file.replace("\\", "/")
        
        # Rule 1: src/engines/ should never import from UI or Page layer
        if src_file_norm.startswith('src/engines/') and (imp.startswith('src.ui') or imp.startswith('pages')):
            violations.append(("Domain Engine importing from UI/Page layer", src_file, imp))
            
        # Rule 2: src/utils/ should never import from engines, workflow, ui, or pages
        if src_file_norm.startswith('src/utils/') and (imp.startswith('src.engines') or imp.startswith('src.workflow') or imp.startswith('src.ui') or imp.startswith('pages')):
            violations.append(("Utility Helper importing from high-level layer", src_file, imp))
            
        # Rule 3: src/config/ should never import from engines, workflow, ui, or pages
        if src_file_norm.startswith('src/config/') and (imp.startswith('src.engines') or imp.startswith('src.workflow') or imp.startswith('src.ui') or imp.startswith('pages')):
            violations.append(("Config module importing from high-level layer", src_file, imp))
            
        # Rule 4: src/data/ should never import from engines, workflow, ui, or pages
        if src_file_norm.startswith('src/data/') and (imp.startswith('src.engines') or imp.startswith('src.workflow') or imp.startswith('src.ui') or imp.startswith('pages')):
            violations.append(("Data module importing from high-level layer", src_file, imp))
            
    print("=== Architectural Decoupling Audit ===")
    if not violations:
        print("  [OK] No architectural coupling violations detected. Perfect layer separation!")
        sys.exit(0)
    else:
        print(f"  [FAIL] Found {len(violations)} architectural coupling violations:")
        for rule, src_file, imp in violations:
            print(f"    - [{rule}]:")
            print(f"        File: {src_file}")
            print(f"        Imports: {imp}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Codegraph database querying tool.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Status command
    subparsers.add_parser("status", help="Get the status of the codegraph index.")
    
    # Search command
    search_p = subparsers.add_parser("search", help="Search for nodes.")
    search_p.add_argument("query", type=str, help="Search query (substring match).")
    search_p.add_argument("--limit", type=int, default=15, help="Maximum number of results to return.")
    
    # Info command
    info_p = subparsers.add_parser("info", help="Get detailed info for a node.")
    info_p.add_argument("node", type=str, help="Node ID, name, or qualified name.")
    
    # Callers command
    callers_p = subparsers.add_parser("callers", help="Find callers of a node.")
    callers_p.add_argument("node", type=str, help="Node ID, name, or qualified name.")
    
    # Callees command
    callees_p = subparsers.add_parser("callees", help="Find callees of a node.")
    callees_p.add_argument("node", type=str, help="Node ID, name, or qualified name.")
    
    # Visualize command
    subparsers.add_parser("visualize", help="Generate a Mermaid dependency graph.")
    
    # Check architecture command
    subparsers.add_parser("check-architecture", help="Check for decoupling violations in the codebase.")
    
    args = parser.parse_args()
    if args.command == "status":
        cmd_status(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "info":
        cmd_info(args)
    elif args.command == "callers":
        cmd_callers(args)
    elif args.command == "callees":
        cmd_callees(args)
    elif args.command == "visualize":
        cmd_visualize(args)
    elif args.command == "check-architecture":
        cmd_check_architecture(args)

if __name__ == "__main__":
    main()
