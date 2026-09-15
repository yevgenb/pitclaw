"""Measure all sixteen insert pilots and M3 screw passages in full native STLs."""
from pathlib import Path
import hashlib,json
import trimesh
from verify_running_clearance import crossings
OUT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    locations=[]
    for x in (-25.5,25.5):
        for y in (-37,21):locations.append(('carrier-bottom','carrier pilot',x,y,[3,5,7],4.2))
    for x in (-38,38):
        for y in (-28,28):
            locations.append(('carrier-bottom','closure pilot',x,y,[23,25,27],4.2))
            locations.append(('carrier-top','closure screw passage',x,y,[30,35,40],3.4))
    for x in (-36,36):
        for y in (-37,37):
            locations.append(('carrier-bottom','future mount pilot',x,y,[3,5,7],4.2))
            locations.append(('carrier-bottom','external mount screw passage',x,y,[.5,1.5,2],3.4))
    for x in (-35.5,35.5):
        for y in (-40,40):
            locations.append(('carrier-top','retainer pilot',x,y,[33,35,37],4.2))
            locations.append(('carrier-retainer','retainer screw passage',x,y,[30.5,31.5,32],3.4))
    files={name:OUT/'native-stl'/f'{name}.stl' for name,*_ in locations}
    hashes={n:sha(p) for n,p in files.items()}
    meshes={n:trimesh.load(p,force='mesh') for n,p in files.items()}
    report={'status':'RUNNING','scope':'Full native STL sections, all 16 pilots and 12 M3 screw passages at 3 depths; diameter tolerance 0.005mm for mesh faceting.','sources_sha256':hashes,'measurements':[]}
    for name,label,x,y,zs,expected in locations:
        for z in zs:
            segments=trimesh.intersections.mesh_plane(meshes[name],[0,0,1],[0,0,z])
            measured=[]
            for axis,value,result_axis,centre in [(1,y,0,x),(0,x,1,y)]:
                xs=crossings(segments,axis,value,result_axis)
                left=max(v for v in xs if v<centre);right=min(v for v in xs if v>centre)
                assert abs(left-(centre-expected/2))<.005,(name,label,x,y,z,left)
                assert abs(right-(centre+expected/2))<.005,(name,label,x,y,z,right)
                measured.append(right-left)
            report['measurements'].append({'file':name+'.stl','feature':label,'assembled_coordinates_mm':[x,y,z],'diameters_xy_mm':measured,'expected_diameter_mm':expected})
    assert hashes=={n:sha(p) for n,p in files.items()}
    report['status']='PASS: all 16 pilots are 4.2mm; 12 screw passages remain 3.4mm'
    (OUT/'insert-hole-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['status'],'sections',len(report['measurements']))
if __name__=='__main__':main()
