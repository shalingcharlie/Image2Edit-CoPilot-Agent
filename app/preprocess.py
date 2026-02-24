from PIL import Image, ImageOps
from io import BytesIO
def preprocess_image_to_jpeg(image_bytes: bytes, max_side: int = 2000,
quality: int = 82) -&gt; bytes:
img = Image.open(BytesIO(image_bytes))
img = ImageOps.exif_transpose(img) # correct rotation from phone
img = img.convert(&quot;RGB&quot;)
w, h = img.size
scale = min(1.0, max_side / max(w, h))
if scale &lt; 1.0:
img = img.resize((int(w * scale), int(h * scale)))
out = BytesIO()
img.save(out, format=&quot;JPEG&quot;, quality=quality, optimize=True)
return out.getvalue()

backend/app/validate.py
from typing import List
from .ir_schema import IR, Node, Edge
def validate_ir(ir: IR) -&gt; IR:
warnings: List[str] = list(ir.warnings or [])
# Normalize nodes and ensure unique IDs
seen = set()
fixed_nodes: List[Node] = []
for idx, n in enumerate(ir.nodes or [], start=1):
nid = (n.id or &quot;&quot;).strip() or f&quot;n{idx}&quot;
if nid in seen:
nid = f&quot;{nid}_{idx}&quot;
warnings.append(&quot;Duplicate node id detected; renamed.&quot;)
seen.add(nid)
txt = (n.text or &quot;&quot;).strip() or &quot;???&quot;
if txt == &quot;???&quot;:
warnings.append(f&quot;Node {nid} text unclear (set to ???).&quot;)
ntype = n.type if n.type in (&quot;process&quot;, &quot;decision&quot;, &quot;start_end&quot;,
&quot;io&quot;) else &quot;process&quot;

fixed_nodes.append(Node(id=nid, type=ntype, text=txt,
confidence=float(n.confidence or 1.0)))
node_ids = {n.id for n in fixed_nodes}
# Filter edges to valid endpoints
fixed_edges: List[Edge] = []
for e in ir.edges or []:
src = (e.source or &quot;&quot;).strip()
tgt = (e.target or &quot;&quot;).strip()
if src in node_ids and tgt in node_ids and src != tgt:
fixed_edges.append(Edge(source=src, target=tgt, label=(e.label or
&quot;&quot;), confidence=float(e.confidence or 1.0)))
# Fallback: chain sequentially if no edges
if fixed_nodes and not fixed_edges:
warnings.append(&quot;No valid edges found; chained nodes sequentially as
fallback.&quot;)
for i in range(len(fixed_nodes) - 1):
fixed_edges.append(Edge(source=fixed_nodes[i].id,
target=fixed_nodes[i + 1].id))
# Overall confidence (simple heuristic)
conf = float(ir.confidence or 0.85)
ir.nodes = fixed_nodes
ir.edges = fixed_edges
ir.warnings = warnings
ir.confidence = conf
return ir
