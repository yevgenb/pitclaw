#!/usr/bin/env python3
"""Independently parse exported Gerber/Excellon and compare with native evidence.

Gerbonara parses CAM, Shapely compares copper connectivity. Circular/arc geometry
uses <=0.002 mm approximation; this supplements native DRC, not factory CAM.
"""
from collections import Counter,defaultdict
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import tempfile
import warnings
import zipfile
from gerbonara import LayerStack
from gerbonara.graphic_objects import Flash,Line
from gerbonara.graphic_primitives import Circle,Rectangle,Line as PrimitiveLine,ArcPoly
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union

archive,refpath,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=True)
ref=json.loads(refpath.read_text())
def key(diameter,endpoints):
    return (round(diameter,4),tuple(sorted(tuple(round(x,4) for x in p) for p in endpoints)))
def holekey(o):
    if isinstance(o,Flash):ends=[(o.x,o.y)]*2
    elif isinstance(o,Line):ends=[(o.x1,o.y1),(o.x2,o.y2)]
    else:raise AssertionError(('Unexpected drill primitive',type(o)))
    return key(o.aperture.diameter,ends)
def geom(p):
    if isinstance(p,Circle):return Point(p.x,p.y).buffer(p.r,quad_segs=64)
    if isinstance(p,PrimitiveLine):
        return LineString([(p.x1,p.y1),(p.x2,p.y2)]).buffer(p.width/2,quad_segs=64)
    if isinstance(p,(Rectangle,ArcPoly)):
        q=p.to_arc_poly().approximate_arcs(max_error=.002)
        shape=Polygon(q.outline)
        return shape if shape.is_valid else shape.buffer(0)
    raise AssertionError(('Unhandled copper primitive',type(p)))

with tempfile.TemporaryDirectory(prefix='pitclaw-cam-audit-') as temp:
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==9 and all(Path(n).name==n for n in z.namelist())
        assert z.testzip() is None
        z.extractall(temp)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        stack=LayerStack.open(Path(temp))
        assert set(stack.graphic_layers)=={('top','copper'),('bottom','copper'),
            ('top','mask'),('bottom','mask'),('top','silk'),('bottom','silk'),('mechanical','outline')}
        drill_rounding=0.0
        for plated,layer in [(True,stack.drill_pth),(False,stack.drill_npth)]:
            expected=[key(h['diameter_mm'],h['endpoints_mm']) for h in ref['holes'] if h['plated']==plated]
            actual=[holekey(o) for o in layer.objects]
            assert len(expected)==len(actual)
            for diameter,ends in expected:
                candidates=[]
                for i,(got_d,got_ends) in enumerate(actual):
                    if abs(diameter-got_d)>1e-6:continue
                    error=max(abs(a-b) for p,q in zip(ends,got_ends) for a,b in zip(p,q))
                    # KiCad's decimal-mm Excellon output has a 0.001 mm grid.
                    if error<=.000501:candidates.append((error,i))
                assert candidates,('Excellon/native hole mismatch',plated,diameter,ends)
                error,i=min(candidates);drill_rounding=max(drill_rounding,error);actual.pop(i)
            assert not actual
        outline=[]
        for o in stack.outline.objects:
            assert isinstance(o,Line)
            outline.append(sorted([[round(o.x1,6),round(o.y1,6)],[round(o.x2,6),round(o.y2,6)]]))
        assert sorted(outline)==ref['outline_segments'],'Gerber/native profile mismatch'
        endpoints=Counter(tuple(p) for s in outline for p in s)
        assert len(outline)==4 and set(endpoints.values())=={2},'Profile is not one closed rectangle'
        xs,ys=zip(*endpoints)
        assert [max(xs)-min(xs),max(ys)-min(ys)]==[60,92]
        assert ref['thickness_mm']==1.6 and ref['copper_layers']==2

        # Copper union independently decoded from Gerber primitives, ignoring net labels.
        components={};bounds={};edge_gaps={}
        outline_box=box(min(xs),min(ys),max(xs),max(ys))
        for side in ('top','bottom'):
            primitives=[p for o in stack[side,'copper'].objects for p in o.to_primitives()]
            assert primitives and all(p.polarity_dark for p in primitives),'Extend audit for clear-polarity copper'
            copper=unary_union([geom(p) for p in primitives])
            assert copper.is_valid
            assert outline_box.covers(copper),'Copper outside board outline'
            edge_gaps[side]=round(copper.distance(outline_box.boundary),4)
            assert edge_gaps[side]>=.499,'Exported copper violates selected 0.5 mm edge rule'
            components[side]=list(copper.geoms) if copper.geom_type=='MultiPolygon' else [copper]
            bounds[side]=list(copper.bounds)
        parent={}
        def find(k):
            parent.setdefault(k,k)
            if parent[k]!=k:parent[k]=find(parent[k])
            return parent[k]
        def join(a,b):parent[find(a)]=find(b)
        landings=[]
        for pad in ref['pads']+ref['vias']:
            point=Point(pad['center_mm']);nodes=[]
            for side,polys in components.items():
                found=[(side,i) for i,p in enumerate(polys) if p.distance(point)<.001]
                assert len(found)==1,('Missing or ambiguous CAM pad/via copper',pad,side,found)
                nodes.extend(found)
            join(*nodes);landings.append((pad,nodes[0]))
        nets_by_component=defaultdict(set);components_by_net=defaultdict(set)
        for pad,node in landings:
            net=pad['net'] or 'UNCONNECTED:'+pad.get('id','via')
            component=find(node)
            nets_by_component[component].add(net);components_by_net[net].add(component)
        shorts={str(k):sorted(v) for k,v in nets_by_component.items() if len(v)>1}
        opens={k:len(v) for k,v in components_by_net.items() if len(v)>1}
        assert not shorts and not opens,('CAM connectivity mismatch',shorts,opens)
        # Native pads/vias bridge layers only where the separately checked drill is plated.
        for side in ('top','bottom'):
            assert stack[side,'mask'].objects
            (out/f'gerber-{side}.svg').write_text(str(stack.to_pretty_svg(side=side,margin=1)))
        parser_warnings=sorted(set('G90 header statement found after end of header'
                                  if 'G90 header statement found after end of header' in str(w.message)
                                  else str(w.message) for w in caught))
        # KiCad puts G90 after M95; Gerbonara accepts its unambiguous absolute coordinates.
        assert all('G90 header statement found after end of header' in w
                   or w.startswith(('Layer "top paste" not found.','Layer "bottom paste" not found.'))
                   for w in parser_warnings),parser_warnings
        report={'result':'PASS','archive':archive.name.replace('.candidate',''),
                'pcb_sha256':ref['pcb_sha256'],
                'gerbonara_version':importlib.metadata.version('gerbonara'),
                'shapely_version':importlib.metadata.version('shapely'),
                'profile_centerline_mm':[60,92],'closed_profile_segments':4,
                'gerber_layers':sorted('/'.join(k) for k in stack.graphic_layers),
                'plated_holes_and_slots':len(stack.drill_pth.objects),
                'nonplated_holes':len(stack.drill_npth.objects),
                'plated_slots':sum(isinstance(o,Line) for o in stack.drill_pth.objects),
                'drills_match_native_positions_sizes_orientations':True,
                'maximum_drill_coordinate_rounding_mm':round(drill_rounding,6),
                'copper_bounds_mm':bounds,'copper_edge_clearance_mm':edge_gaps,
                'electrical_pad_landings':len(ref['pads']),'via_bridges':len(ref['vias']),
                'nets_checked':len(components_by_net),'exported_copper_shorts':shorts,
                'exported_copper_opens':opens,'parser_warnings':parser_warnings,
                'scope':'Exact archived CAM parsed independently; approximate vector connectivity compared with native pad nets. Does not qualify thermal behavior or physical fit.'}
        (out/'cam-audit.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
