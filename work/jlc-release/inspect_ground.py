import pcbnew as pcb,json
from pathlib import Path
board=pcb.LoadBoard('hardware/carrier-revb/pitclaw-carrier.kicad_pcb')
footprints={f.GetReference():f for f in board.GetFootprints()}
copper_items=list(board.GetTracks())
vias=[i for i in copper_items if isinstance(i,pcb.PCB_VIA)]
tracks=[i for i in copper_items if not isinstance(i,pcb.PCB_VIA)]
def ground_corridor_review():
    """Inspect saved copper geometry; no thermal or voltage-drop claim.

    Erosion removes corridors narrower than the specified width, with a
    0.01 mm numerical allowance so an exactly nominal-width track retains
    nonzero polygon area. Pad landings
    are allowed to meet a surviving region within the erosion distance plus
    0.05 mm, so short pad necks are not mistaken for long return bottlenecks.
    PTH landings are represented by their outer copper shape; this does not
    model drill resistance or qualify their current capacity.
    """
    refs=(("J1","2"),("J9","2"),("J2","4"),("U2","2"),("C1","2"),
          ("C2","2"),("C3","2"),("C4","2"),("D2","2"),
          ("J7","2"),("J8","2"),("J8","5"))
    landings={f"{ref}:{num}":next(p for p in footprints[ref].Pads() if p.GetNumber()==num)
              for ref,num in refs}
    ground_vias=[v for v in vias if v.GetNetname().lstrip('/')=='GND']
    for i,via in enumerate(sorted(ground_vias,key=lambda v:(v.GetPosition().x,v.GetPosition().y)),1):
        landings[f"GND_via_{i}"]=via
    # Only power-section plated pads and actual GND vias may bridge layers in
    # the power-return graph. The ADC/DEBUG landings are reported but cannot
    # serve as the sole layer transition for a power return.
    bridges=set(landings)-{'J7:2','J8:2','J8:5'}
    widths_to_check=(0,.5,1.0,1.2,1.5,2.0)
    result={"method":"Saved GND fills + GND tracks + outer pad/via copper, eroded separately per layer with 0.01 mm corridor-width numerical allowance; landing tolerance is erosion distance + 0.05 mm. Power-section PTH pads and actual GND vias may join surviving regions across layers; ADC/DEBUG pads are not power-return bridges. PTH/via drill resistance, copper thickness, current sharing, temperature and voltage drop are not modeled.","corridor_width_numerical_allowance_mm":.01,"layers":{}}
    for layer in (pcb.F_Cu,pcb.B_Cu):
        copper=pcb.SHAPE_POLY_SET()
        for zone in board.Zones():
            if not zone.GetIsRuleArea() and zone.GetNetname().lstrip('/')=='GND' and zone.GetLayerSet().Contains(layer):
                copper.BooleanAdd(zone.GetFilledPolysList(layer))
        for footprint in footprints.values():
            for pad in footprint.Pads():
                if pad.GetNetname().lstrip('/')=='GND' and pad.GetLayerSet().Contains(layer):
                    shape=pcb.SHAPE_POLY_SET()
                    pad.TransformShapeToPolygon(shape,layer,0,pcb.FromMM(.001),pcb.ERROR_INSIDE)
                    copper.BooleanAdd(shape)
        for track in tracks+ground_vias:
            if track.GetNetname().lstrip('/')=='GND' and track.GetLayerSet().Contains(layer):
                shape=pcb.SHAPE_POLY_SET()
                track.TransformShapeToPolygon(shape,layer,0,pcb.FromMM(.001),pcb.ERROR_INSIDE)
                copper.BooleanAdd(shape)
        copper.Simplify()
        widths={}
        for width in widths_to_check:
            eroded=pcb.SHAPE_POLY_SET(copper)
            erosion=max(0,(width-.01)/2)
            if width:
                eroded.Deflate(pcb.FromMM(erosion),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcb.FromMM(.001))
            groups=[]
            for i in range(eroded.OutlineCount()):
                region=eroded.UnitSet(i)
                touching=[name for name,pad in landings.items()
                          if region.Collide(pad.GetEffectiveShape(layer),pcb.FromMM(erosion+.05))]
                if touching:
                    groups.append({"area_mm2":round(region.Area()/1e12,3),"landings":sorted(touching)})
            widths[str(width)]=groups
        result['layers'][board.GetLayerName(layer)]=widths
    networks={}
    for width in widths_to_check:
        graph={name:set() for name in bridges}
        for layer in result['layers'].values():
            for region in layer[str(width)]:
                names=set(region['landings']) & bridges
                for name in names: graph[name].update(names-{name})
        visited={'J1:2'};pending=['J1:2']
        while pending:
            for name in graph[pending.pop()]-visited:
                visited.add(name);pending.append(name)
        networks[str(width)]=sorted(visited)
    result['power_return_reachable_from_J1_by_corridor_mm']=networks
    main={'J1:2','J9:2','U2:2','C1:2','C3:2','D2:2'}
    pass
    pass
    result['main_power_return_corridor_mm']=2.0
    result['j2_combined_return_corridor_mm']=1.2
    return result

r=ground_corridor_review()
Path('work/jlc-release/ground-local.json').write_text(json.dumps(r,indent=2))
print(json.dumps({key:value for key,value in r.items() if key!='layers'},indent=2))
for k,v in r['layers'].items(): print(k,json.dumps(v['2.0'],indent=2))
