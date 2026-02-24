from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response, JSONResponse
from .preprocess import preprocess_image_to_jpeg

from .extract_model import extract_ir_from_image
from .validate import validate_ir
from .export_drawio import ir_to_drawio_xml
app = FastAPI(title=&quot;Photo → Draw.io (Copilot MVP)&quot;, version=&quot;0.1&quot;)
@app.get(&quot;/health&quot;)
def health():
return {&quot;ok&quot;: True}
@app.post(&quot;/v1/convert&quot;, summary=&quot;Upload photo and get an editable .drawio
file&quot;)
async def convert(image: UploadFile = File(...)):
if not image:
raise HTTPException(status_code=400, detail=&quot;Missing file field
&#39;image&#39;&quot;)
raw = await image.read()
if not raw:
raise HTTPException(status_code=400, detail=&quot;Empty upload&quot;)
# Normalize image for better extraction reliability
jpeg = preprocess_image_to_jpeg(raw, max_side=2000, quality=82)
# Extract → validate → export
ir = extract_ir_from_image(jpeg, max_attempts=2)
ir = validate_ir(ir)
xml = ir_to_drawio_xml(ir, diagram_name=&quot;Copilot Flowchart&quot;)
return Response(
content=xml,
media_type=&quot;application/xml&quot;,
headers={&quot;Content-Disposition&quot;: &#39;attachment;
filename=&quot;copilot_output.drawio&quot;&#39;}
)
@app.post(&quot;/v1/convert_json&quot;, summary=&quot;Debug endpoint: return structured
graph JSON&quot;)
async def convert_json(image: UploadFile = File(...)):
raw = await image.read()
jpeg = preprocess_image_to_jpeg(raw, max_side=2000, quality=82)
ir = validate_ir(extract_ir_from_image(jpeg, max_attempts=2))
return JSONResponse({
&quot;confidence&quot;: ir.confidence,
&quot;warnings&quot;: ir.warnings,
&quot;nodes&quot;: [n.__dict__ for n in ir.nodes],
&quot;edges&quot;: [{&quot;from&quot;: e.source, &quot;to&quot;: e.target, &quot;label&quot;: e.label,
&quot;confidence&quot;: e.confidence} for e in ir.edges],
})
